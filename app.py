import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import datetime
import warnings
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.simplefilter(action='ignore', category=FutureWarning)

# ==========================================
# 頁面配置與自訂 CSS
# ==========================================
st.set_page_config(page_title="全方位個股掃描系統 V6.2", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 4px solid #1a252f; height: 100%;}
    .card-laca { border-top: 4px solid #d63384; }
    .card-macro { border-top: 4px solid #0dcaf0; }
    .card-flow { border-top: 4px solid #fd7e14; }
    .card-mom { border-top: 4px solid #198754; }
    .card-logic { border-top: 4px solid #6f42c1; }
    .text-up { color: #dc3545; font-weight: bold; }
    .text-down { color: #20c997; font-weight: bold; }
    .vwap-highlight { background-color: rgba(13, 110, 253, 0.1); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(13, 110, 253, 0.3); font-weight: bold; color: #084298;}
    .num-highlight { color: #dc3545; font-weight: 900; font-family: 'Courier New', Courier, monospace; font-size: 1.15rem;}

    .brainless-box { background: linear-gradient(135deg, #1a252f 0%, #2c3e50 100%); border-left: 6px solid #d4af37; padding: 15px 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 15px; color: #fff;}
    .brainless-title { font-size: 0.9rem; font-weight: bold; color: #d4af37; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
    .brainless-content { font-size: 1.25rem; font-weight: 700; line-height: 1.5; }

    .holy-grail-alert { background: linear-gradient(to right, #f6d365, #fda085); color: #856404; border-radius: 8px; padding: 15px; margin-bottom: 15px; text-align: center; font-weight: 900; font-size: 1.2rem; border: 2px solid #e0a800; box-shadow: 0 0 15px rgba(253, 160, 133, 0.5); animation: pulse 2s infinite;}
    @keyframes pulse { 0% {box-shadow: 0 0 0 0 rgba(253, 160, 133, 0.7);} 70% {box-shadow: 0 0 0 15px rgba(253, 160, 133, 0);} 100% {box-shadow: 0 0 0 0 rgba(253, 160, 133, 0);} }

    .pa-card { background-color: #fdfdfe; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); height: 100%;}
    .pa-item-active { padding: 10px; margin-bottom: 8px; border-radius: 4px; font-weight: bold; font-size: 0.9rem; border-left: 5px solid #ffc107; background-color: #fff3cd; color: #856404; }
    .pa-item-danger { padding: 10px; margin-bottom: 8px; border-radius: 4px; font-weight: bold; font-size: 0.9rem; border-left: 5px solid #dc3545; background-color: #f8d7da; color: #842029; }
    .pa-item-inactive { color: #adb5bd; padding: 8px 10px; margin-bottom: 6px; font-size: 0.85rem; border-left: 3px solid #e9ecef; background-color: #f8f9fa; border-radius: 4px;}

    .atm-alert { background: linear-gradient(to right, #ffc107, #ff9800); color: #000; border-radius: 8px; padding: 12px; margin-bottom: 15px; text-align: center; font-weight: bold;}
    .disclaimer { text-align: center; color: #6c757d; font-size: 0.85rem; padding: 10px; margin-bottom: 25px; border-bottom: 1px dashed #dee2e6; }
    .exec-table th { color: #fff; text-align: center; vertical-align: middle;}
    .exec-table td { vertical-align: middle; line-height: 1.6; }
    .hist-table th { position: sticky; top: 0; background-color: #1a252f !important; color: white !important; z-index: 10; text-align: center;}
    .hist-table td { text-align: center; vertical-align: middle; font-size: 0.95rem;}
    .badge-hist { font-size: 0.85rem; padding: 4px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 核心邏輯模組
# ==========================================
@st.cache_data(ttl=86400)
def get_stock_name(ticker):
    clean_ticker = ticker.replace('.TW', '').replace('.TWO', '')
    try:
        url = f"https://tw.stock.yahoo.com/quote/{clean_ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            match = re.search(r'<title>(.*?)\s*\(', res.text)
            if match:
                name = match.group(1).replace("Yahoo奇摩股市", "").strip()
                if name: return name
    except:
        pass
    return clean_ticker


def get_consecutive_trend(series):
    if len(series) < 2: return 0, 0
    latest_sign = np.sign(series.iloc[-1])
    if latest_sign == 0: return 0, 0
    count, cumsum = 0, 0
    for val in reversed(series):
        if np.sign(val) == latest_sign or val == 0:
            if val != 0: count += 1
            cumsum += val
        else:
            break
    return count * latest_sign, cumsum


def get_trend_shape(series):
    if len(series) < 3: return "無資料"
    v0, v1, v2 = series.iloc[-1], series.iloc[-2], series.iloc[-3]
    if v0 > v1 and v1 > v2:
        return "持續上揚 ↗"
    elif v0 < v1 and v1 < v2:
        return "持續向下 ↘"
    elif v0 > v1 and v1 <= v2:
        return "向上拐彎轉折 ⤴"
    elif v0 < v1 and v1 >= v2:
        return "向下拐彎轉折 ⤵"
    else:
        return "震盪平移 →"


def calculate_ab_rankings(c_price, ma20_val, ma20_shape, rsi_shape, mfi_shape, is_holy_grail=False, pa_penalty=0,
                          pa_bonus=0):
    if is_holy_grail:
        return "S+", "極致壓縮後強勢表態", "S+", "資金點火且OBV創高", "🌟 聖杯型態 (極致壓縮爆發)", "符合四大嚴格量化條件：壓縮、出量、破軌、資金湧入！此為勝率最高之起漲點型態。"

    ma_up = "上揚" in ma20_shape or "向上" in ma20_shape
    ma_down = "向下" in ma20_shape

    if c_price >= ma20_val and ma_up:
        a_rank, a_desc = "A+", "20日線上升且現價站穩月線"
    elif c_price < ma20_val and ma_down:
        a_rank, a_desc = "A-", "20日線下彎且跌破月線"
    else:
        a_rank, a_desc = "A", "均線平移或方向分歧"

    up_count = sum(1 for s in [rsi_shape, mfi_shape] if "上揚" in s or "向上" in s)
    down_count = sum(1 for s in [rsi_shape, mfi_shape] if "向下" in s)

    if up_count == 2 or (up_count == 1 and down_count == 0):
        b_rank, b_desc = "B+", "RSI/MFI 買盤動能共振向上"
    elif down_count == 2 or (down_count == 1 and up_count == 0):
        b_rank, b_desc = "B-", "RSI/MFI 賣壓動能共振向下"
    else:
        b_rank, b_desc = "B", "RSI/MFI 動能分歧或平移震盪"

    if pa_penalty > 0:
        return a_rank, a_desc, "B-", "裸K動能轉弱覆寫", "⚠️ 裸 K 價格行為警告", "雖然指標尚未翻轉，但 K 線實體已出現出貨或誘多特徵，請高度警戒！"
    elif pa_bonus > 0:
        return "A+", "裸K動能強勢加分", "B+", "多方攻擊訊號確認", "🚀 裸 K 強力多頭組合", "實體 K 線出現連續強勢攻擊型態（如三白兵），多方主力強烈表態！"

    if a_rank == "A+" and b_rank == "B+":
        title, msg = "趨勢動能共振 (強勢攻擊)", "大結構偏多且短線買盤強勁，標準主升段攻擊架構，順勢抱緊。"
    elif a_rank == "A+" and b_rank in ["B", "B-"]:
        title, msg = "多頭回檔洗盤 (長多短空)", "主因：20MA反映長線『趨勢』仍在墊高；RSI/MFI反映近幾日『短線震盪』。<br>此為典型的「多頭架構下之漲多回檔或量縮洗盤」，大結構並未反轉。"
    elif a_rank == "A-" and b_rank in ["B+", "B"]:
        title, msg = "左側背離潛伏 (長空短多)", "主因：長線趨勢雖偏空，但底層 RSI/MFI 動能率先向上發動。<br>此為典型的「跌深反彈」或底部「黃金坑」打底跡象，左側資金可留意。"
    elif a_rank == "A-" and b_rank == "B-":
        title, msg = "空頭共振探底 (極度弱勢)", "長線趨勢與短線動能同步下殺，標準空頭結構。切勿阻擋墜落的刀子！"
    elif a_rank == "A" and b_rank == "B+":
        title, msg = "震盪轉強突破 (醞釀表態)", "長線結構處於過渡期，短線資金已開始點火，準備向上突破。"
    elif a_rank == "A" and b_rank == "B-":
        title, msg = "震盪轉弱防守 (面臨考驗)", "長線結構不明確，且短線動能正持續衰退，需嚴格防守下方支撐。"
    else:
        title, msg = "多空分歧沉澱 (方向未明)", "趨勢與動能尚無一致共識，目前處於籌碼換手與觀望的過渡期。"

    return a_rank, a_desc, b_rank, b_desc, title, msg


@st.cache_data(ttl=300)
def fetch_macro_and_adr():
    try:
        sp500 = yf.download("^GSPC", period="5d", progress=False, auto_adjust=True)
        ndx = yf.download("^IXIC", period="5d", progress=False, auto_adjust=True)
        tsm = yf.download("TSM", period="5d", progress=False, auto_adjust=True)

        if isinstance(sp500.columns, pd.MultiIndex): sp500.columns = sp500.columns.get_level_values(0)
        if isinstance(ndx.columns, pd.MultiIndex): ndx.columns = ndx.columns.get_level_values(0)
        if isinstance(tsm.columns, pd.MultiIndex): tsm.columns = tsm.columns.get_level_values(0)

        sp500_pct = (sp500['Close'].iloc[-1] - sp500['Close'].iloc[-2]) / sp500['Close'].iloc[-2] * 100 if len(
            sp500) >= 2 else 0
        ndx_pct = (ndx['Close'].iloc[-1] - ndx['Close'].iloc[-2]) / ndx['Close'].iloc[-2] * 100 if len(ndx) >= 2 else 0
        tsm_pct = (tsm['Close'].iloc[-1] - tsm['Close'].iloc[-2]) / tsm['Close'].iloc[-2] * 100 if len(tsm) >= 2 else 0

        today_day = datetime.datetime.now().day
        is_window_dressing = today_day >= 23 or today_day <= 3

        atm_risk = False
        macro_msg = f"S&P500 {sp500_pct:+.2f}% | 納斯達克 {ndx_pct:+.2f}% | TSM ADR {tsm_pct:+.2f}%"

        if tsm_pct > 1.5 and is_window_dressing:
            atm_risk = True
            macro_msg += "<br>⚠️ <span class='text-danger'>作帳結帳期：ADR大漲易成外資提款誘因，嚴防開高走低！</span>"

        macro_score = 10
        if sp500_pct >= 0.5:
            macro_score += 3
        elif sp500_pct <= -0.5:
            macro_score -= 3
        if tsm_pct >= 1.0:
            macro_score += 7
        elif tsm_pct <= -1.0:
            macro_score -= 7
        if atm_risk: macro_score -= 10
        macro_score = max(0, min(20, macro_score))

        return atm_risk, macro_msg, tsm_pct, macro_score
    except:
        return False, "國際市場連動數據暫時無法獲取", 0, 10


@st.cache_data(ttl=60)
def fetch_chip_data(stock_id):
    url = "https://api.finmindtrade.com/api/v4/data"
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=25)).strftime("%Y-%m-%d")
    params = {"dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_id": str(stock_id), "start_date": start_date,
              "end_date": end_date}
    try:
        res = requests.get(url, params=params, timeout=5).json()
        if not res.get("data"): return 0, 0, 0, 0, 0, 0, 15, False
        df = pd.DataFrame(res["data"])
        df['Net_Buy'] = (df['buy'] - df['sell']) / 1000
        pivot = df.pivot_table(index='date', columns='name', values='Net_Buy', aggfunc='sum').fillna(0)
        pivot = pivot[(pivot.T != 0).any()]
        if pivot.empty: return 0, 0, 0, 0, 0, 0, 15, False

        f_series = pivot.get('Foreign_Investor', pd.Series([0]))
        t_series = pivot.get('Investment_Trust', pd.Series([0]))

        f_buy_latest = f_series.iloc[-1] if not f_series.empty else 0
        t_buy_latest = t_series.iloc[-1] if not t_series.empty else 0

        f_days, f_cumsum = get_consecutive_trend(f_series)
        t_days, t_cumsum = get_consecutive_trend(t_series)

        flow_score = 15
        if f_buy_latest > 0:
            flow_score += 5
        elif f_buy_latest < 0:
            flow_score -= 5
        if f_days >= 2:
            flow_score += 5
        elif f_days <= -2:
            flow_score -= 5

        if t_buy_latest > 0:
            flow_score += 5
        elif t_buy_latest < 0:
            flow_score -= 5
        if t_days >= 2:
            flow_score += 5
        elif t_days <= -2:
            flow_score -= 5
        flow_score = max(0, min(30, flow_score))

        return f_buy_latest, t_buy_latest, f_days, t_days, f_cumsum, t_cumsum, flow_score, True
    except:
        return 0, 0, 0, 0, 0, 0, 15, False


@st.cache_data(ttl=300)
def fetch_data(ticker):
    query_ticker = f"{ticker}.TW" if not ticker.endswith(('.TW', '.TWO')) else ticker
    df = yf.download(query_ticker, period="1y", progress=False, auto_adjust=True)

    if df.empty and not ticker.endswith(('.TW', '.TWO')):
        query_ticker = f"{ticker}.TWO"
        df = yf.download(query_ticker, period="1y", progress=False, auto_adjust=True)

    if df.empty: return None
    stock_name = get_stock_name(ticker)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['MA111'] = df['Close'].rolling(111).mean()
    df['MV5'] = df['Volume'].rolling(5).mean()
    df['MV20'] = df['Volume'].rolling(20).mean()
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3

    std = df['Close'].rolling(20).std()
    df['BBU'] = df['MA20'] + (2 * std)
    df['BBL'] = df['MA20'] - (2 * std)
    df['BBW'] = (df['BBU'] - df['BBL']) / df['MA20'] * 100

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 1e-10)))

    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    df['OBV_Diff'] = df['OBV'].diff()

    raw_mf = df['TP'] * df['Volume']
    pos_flow = raw_mf.where(df['TP'] > df['TP'].shift(1), 0).rolling(14).sum()
    neg_flow = raw_mf.where(df['TP'] < df['TP'].shift(1), 0).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + (pos_flow / neg_flow).replace(0, 1e-10)))

    df['Pct_Change'] = df['Close'].pct_change() * 100

    laca = df['MA20'].iloc[-1]
    for i in range(len(df) - 1, 0, -1):
        if df['Pct_Change'].iloc[i] > 8.0:
            laca = (df['Open'].iloc[i] + df['Close'].iloc[i]) / 2
            break

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    f_buy, t_buy, f_days, t_days, f_cumsum, t_cumsum, flow_score, chip_ok = fetch_chip_data(
        ticker.replace('.TW', '').replace('.TWO', ''))
    atm_risk, macro_msg, tsm_pct, macro_score = fetch_macro_and_adr()

    ma20_shape = get_trend_shape(df['MA20'])
    rsi_shape = get_trend_shape(df['RSI'])
    mfi_shape = get_trend_shape(df['MFI'])
    obv_shape = get_trend_shape(df['OBV'])

    # ======= 裸 K 價格行為 (Price Action) =======
    pa_flags = {
        "pa1_no_limit": False, "pa2_gap_down": False, "pa3_engulf": False,
        "pa4_stagnant": False, "pa5_trap": False, "pa6_ma_break": False,
        "pa7_three_soldiers": False, "pa8_three_crows": False
    }

    upperShadow = latest['High'] - max(latest['Open'], latest['Close'])
    realBody = abs(latest['Close'] - latest['Open'])

    if len(df) >= 5:
        prev2 = df.iloc[-3]
        pa_flags["pa1_no_limit"] = (latest['High'] >= prev['Close'] * 1.07) and (
                    latest['Close'] < prev['Close'] * 1.095) and (upperShadow > realBody * 0.5)
        pa_flags["pa2_gap_down"] = (latest['Open'] <= prev['Close'] * 0.97) and (
                    latest['Close'] <= latest['Open']) and (latest['Volume'] > latest['MV5'])
        pa_flags["pa3_engulf"] = (latest['Open'] > prev['Close']) and (latest['Close'] < prev['Close'])

        high_4th = df['High'].iloc[-4]
        recent_3_highs_max = df['High'].iloc[-3:].max()
        recent_3_vol_avg = df['Volume'].iloc[-3:].mean()
        pa_flags["pa4_stagnant"] = (latest['Close'] > latest['MA20']) and (latest['RSI'] > 60) and (
                    recent_3_highs_max <= high_4th) and (recent_3_vol_avg > latest['MV20'])

        recent_5_high = df['High'].iloc[-5:].max()
        pa_flags["pa5_trap"] = (upperShadow > realBody * 2) and (latest['High'] >= recent_5_high) and (
                    latest['Volume'] > latest['MV5'])

        pa_flags["pa6_ma_break"] = (prev2['Close'] >= prev2['MA20']) and (prev['Close'] < prev['MA20']) and (
                    latest['Close'] < latest['MA20'])

        pa_flags["pa7_three_soldiers"] = (latest['Close'] > latest['Open']) and (prev['Close'] > prev['Open']) and (
                    prev2['Close'] > prev2['Open']) and \
                                         (latest['Close'] > prev['Close']) and (prev['Close'] > prev2['Close'])
        pa_flags["pa8_three_crows"] = (latest['Close'] < latest['Open']) and (prev['Close'] < prev['Open']) and (
                    prev2['Close'] < prev2['Open']) and \
                                      (latest['Close'] < prev['Close']) and (prev['Close'] < prev2['Close'])

    pa_penalty = 0
    if pa_flags["pa2_gap_down"] or pa_flags["pa6_ma_break"] or pa_flags["pa8_three_crows"]:
        pa_penalty = 25
    elif pa_flags["pa1_no_limit"] or pa_flags["pa3_engulf"] or pa_flags["pa4_stagnant"] or pa_flags["pa5_trap"]:
        pa_penalty = 15

    pa_bonus = 15 if pa_flags["pa7_three_soldiers"] else 0

    # ======= 聖杯起漲點判定 =======
    is_squeezed, is_vol_surge, is_price_breakout, is_obv_surge, is_holy_grail = False, False, False, False, False
    if len(df) > 65:
        min_bbw_recent = df['BBW'].iloc[-6:-1].min()
        min_bbw_60d = df['BBW'].iloc[-61:-1].min()
        is_squeezed = bool(min_bbw_recent <= (min_bbw_60d * 1.15))
        prev_mv20_val = df['MV20'].shift(1).iloc[-1]
        is_vol_surge = bool(latest['Volume'] > (prev_mv20_val * 2.5))
        is_price_breakout = bool((latest['Close'] > latest['BBU']) and (latest['Close'] > latest['Open']))
        prev_obv_max = df['OBV_Diff'].shift(1).rolling(20).max().iloc[-1]
        is_obv_surge = bool(df['OBV_Diff'].iloc[-1] > prev_obv_max)
        is_holy_grail = is_squeezed and is_vol_surge and is_price_breakout and is_obv_surge

    a_rank, a_desc, b_rank, b_desc, title, msg = calculate_ab_rankings(
        latest['Close'], latest['MA20'], ma20_shape, rsi_shape, mfi_shape, is_holy_grail, pa_penalty, pa_bonus
    )

    alpha_score = 0
    if a_rank in ["A+", "S+"]:
        alpha_score += 25
    elif a_rank == "A":
        alpha_score += 15
    if b_rank in ["B+", "S+"]:
        alpha_score += 25
    elif b_rank == "B":
        alpha_score += 15

    alpha_score = max(0, alpha_score - pa_penalty + pa_bonus)
    total_score = max(0, min(100, macro_score + flow_score + alpha_score))

    isChipBearish = f_buy < 0 and t_buy <= 0
    isAboveMA20 = latest['Close'] > latest['MA20']
    isAboveLACA = latest['Close'] >= laca

    isHighVolume = latest['Volume'] > (latest['MV5'] * 2 if pd.notna(latest['MV5']) else 1)
    isShootingStar = upperShadow > (realBody * 1.5) and upperShadow > (latest['Close'] * 0.01)

    isClimaxExhaustion = isHighVolume and isShootingStar and latest['Close'] > latest['MA20']
    isUpperBBPingPong = latest['High'] >= latest['BBU'] and latest['Volume'] <= (
        latest['MV5'] * 1.5 if pd.notna(latest['MV5']) else 1)
    isLowerBBRebound = latest['Low'] <= latest['BBL'] and latest['RSI'] < 45
    isTrueSqueeze = latest['Volume'] > (latest['MV5'] * 1.5 if pd.notna(latest['MV5']) else 1) and latest['Close'] > \
                    latest['BBU'] and realBody > upperShadow
    isMarginCall = latest['RSI'] < 30 and not isAboveMA20 and latest['Close'] < latest['BBL']
    isLowVolatility = abs(latest['Pct_Change']) <= 1.5
    isResting = isAboveMA20 and latest['Volume'] < (
        latest['MV5'] if pd.notna(latest['MV5']) else 1) and isLowVolatility and not isChipBearish
    isGoldenPit = latest['MA20'] > prev['MA20'] and isAboveLACA and latest['Close'] <= latest['MA20']
    isBullTrap = (isAboveMA20 and isChipBearish) or (not isAboveMA20 and isAboveLACA and isChipBearish)

    scenario_type = "default"
    if is_holy_grail:
        scenario_type = "holy_grail"
    elif isClimaxExhaustion:
        scenario_type = "climax"
    elif isMarginCall:
        scenario_type = "margin_call"
    elif isTrueSqueeze:
        scenario_type = "squeeze"
    elif isUpperBBPingPong:
        scenario_type = "upper_bb"
    elif isLowerBBRebound:
        scenario_type = "lower_bb"
    elif isGoldenPit:
        scenario_type = "golden_pit"
    elif isResting:
        scenario_type = "resting"
    elif isBullTrap:
        scenario_type = "bull_trap"
    elif isAboveMA20:
        scenario_type = "strong_attack"
    else:
        scenario_type = "dead_cat"

    if scenario_type in ["strong_attack", "squeeze"] and scenario_type != "holy_grail":
        if pa_penalty > 15:
            scenario_type = "dead_cat"
        elif pa_penalty > 0 or total_score < 45:
            scenario_type = "bull_trap"

    df.index = df.index.tz_localize(None)

    return {
        "df": df, "latest": latest, "prev": prev, "stock_name": stock_name,
        "laca": laca, "scenario": scenario_type, "pa_flags": pa_flags, "pa_penalty": pa_penalty,
        "a_rank": a_rank, "a_desc": a_desc, "b_rank": b_rank, "b_desc": b_desc, "logic_title": title, "logic_msg": msg,
        "f_buy": f_buy, "t_buy": t_buy, "f_days": f_days, "t_days": t_days, "f_cumsum": f_cumsum, "t_cumsum": t_cumsum,
        "chip_ok": chip_ok,
        "atm_risk": atm_risk, "macro_msg": macro_msg, "tsm_pct": tsm_pct,
        "macro_score": macro_score, "flow_score": flow_score, "alpha_score": alpha_score, "total_score": total_score,
        "rsi_shape": rsi_shape, "mfi_shape": mfi_shape, "obv_shape": obv_shape,
        "hg_flags": {"squeezed": is_squeezed, "vol_surge": is_vol_surge, "breakout": is_price_breakout,
                     "obv_surge": is_obv_surge}
    }


def get_unified_command(data):
    sc = data['scenario']
    vwap = data['latest']['TP']
    ma5 = data['latest']['MA5']
    ma20 = data['latest']['MA20']
    bbu = data['latest']['BBU']
    bbl = data['latest']['BBL']
    laca = data['laca']
    hg = data['hg_flags']

    if hg['squeezed'] and hg['vol_surge'] and hg['breakout'] and hg['obv_surge']:
        radar_result = "<span style='color:#dc3545; font-weight:900;'>型態符合 🚀</span>"
    elif hg['squeezed']:
        radar_result = "<span style='color:#fd7e14; font-weight:900;'>型態築底中 ⏳</span>"
    else:
        radar_result = "<span style='color:#6c757d; font-weight:900;'>型態不符 ❌</span>"

    # 【重要修復】：把前面的縮排全拿掉，避免被 Markdown 判定為程式碼區塊
    radar_html = f"""
<div style='font-size:0.95rem; color:#1a252f; background-color:#f8f9fa; padding:15px 20px; border-radius:8px; margin-top:20px; border: 1px dashed #ced4da;'>
    <div style='display: flex; align-items: center; border-bottom: 1px solid #dee2e6; padding-bottom: 8px; margin-bottom: 10px;'>
        <div style='flex-grow: 1;'><i class='fas fa-radar' style='color:#6f42c1;'></i> <b style='font-size: 1.05rem;'>聖杯型態偵測雷達</b></div>
        <div>{radar_result}</div>
    </div>
    <div style='margin-left: 5px; line-height: 1.8;'>
        {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['squeezed'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ① 布林帶寬達近 60 日極限壓縮<br>
        {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['vol_surge'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ② 爆發大於 20 日均量 2.5 倍之天量<br>
        {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['breakout'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ③ 實體紅 K 強勢貫穿布林上軌<br>
        {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['obv_surge'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ④ OBV 資金斜率突破近 20 日最高峰
    </div>
</div>
"""

    if sc == "holy_grail":
        sys_status = "<span style='color:#d4af37; font-weight:900; font-size:1.15rem;'><i class='fas fa-crown'></i> 無條件覆寫：觸發最高位階【聖杯型態】！</span>"
    elif data['atm_risk'] and data['f_buy'] < 0:
        sys_status = "<span class='text-danger fw-bold'>🔴 總經提款警戒：外資逢高結帳，台股面臨開高走低風險。</span>"
    elif data['pa_penalty'] > 0:
        sys_status = "<span class='text-danger fw-bold'>🚨 裸 K 否決權觸發：發現主力出貨或誘多之實體 K 線特徵，強制降級劇本！</span>"
    elif data['total_score'] < 45:
        sys_status = "<span class='text-warning fw-bold' style='color:#fd7e14 !important;'>🟡 權重驗證覆寫：總分偏低，宏觀或籌碼面不支持技術面突破，提防誘多！</span>"
    else:
        sys_status = "<span class='text-success fw-bold'>🟢 資金環境正常，依循 Alpha 模組與籌碼動向獨立判定。</span>"

    if sc == "holy_grail":
        title = "🌟 聖杯起漲點：極致壓縮爆發！"
        color = "#d4af37"
        msg = f"這就是波段交易者的聖杯！經歷長達一個月的極限壓縮後，今日主力以超越 2.5 倍均量的爆發力貫穿上軌 ({bbu:.2f})！請務必重倉參與，只要未跌破 5日線，此股將展開長波段主升段！"
    elif sc == "climax":
        title = "🛑 天量竭盡，立刻抽回資金！"
        color = "#dc3545"
        msg = f"天量避雷針已現，主力正在高檔無情倒貨！請立刻抽回所有資金，連盤中均價線 ({vwap:.2f}) 都不要接刀。將資金轉移至其他剛起漲標的，嚴禁留戀！"
    elif sc == "upper_bb":
        title = "⚠️ 上軌壓力，資金轉移觀望"
        color = "#ffc107"
        msg = f"撞擊箱頂壓力 ({bbu:.2f}) 且量能不濟，主力正誘多出貨。在股價回落至月線防守 ({ma20:.2f}) 之前，嚴格保持『空手觀望』的最高紀律！"
    elif sc == "lower_bb":
        title = "🧲 嚴重超跌，左側資金進場"
        color = "#0d6efd"
        msg = f"股價已觸碰下軌 ({bbl:.2f}) 嚴重超賣，賣壓徹底枯竭！這是絕佳的左側買點。請提撥部分資金大膽試單，防守線嚴格設定在今日最低點，跌破才認錯！"
    elif sc in ["squeeze", "strong_attack"]:
        title = "🚀 突破確立，核心資金集中！"
        color = "#dc3545"
        msg = f"主升段發動！請將核心資金集中於此。只要死守盤中均價線 ({vwap:.2f}) 不破，任何盤中洗盤皆是加碼點，讓利潤狂奔，切勿輕易下車！"
    elif sc == "margin_call":
        title = "🩸 血洗融資，嚴禁摸底"
        color = "#000000"
        msg = f"維持率跌破警戒，融資斷頭潮湧現！不要阻擋墜落的刀子，等散戶互相踩踏完畢再收屍，指標全數失效。"
    elif sc == "golden_pit":
        title = "💎 完美假跌破，左側重倉買點"
        color = "#0dcaf0"
        msg = f"主力刻意挖坑洗盤！現價若站穩均價線 ({vwap:.2f})，這是極難得的完美假跌破。請立刻準備左側建倉，防守線死守 LACA ({laca:.2f})，破了才走！"
    elif sc == "resting":
        title = "🛡️ 量縮洗盤，資金暫停加碼"
        color = "#198754"
        msg = f"均線上彎且量縮洗盤中，主力正在清洗浮額。請保持底倉不動，防守線設於 5日線 ({ma5:.2f})。此時嚴禁無腦加碼，等待補量上攻！"
    elif sc == "bull_trap":
        title = "⚠️ 籌碼背離誘多，準備撤退"
        color = "#fd7e14"
        msg = f"趨勢雖撐，但底層資金正在暗中抽離！這是標準的誘多陷阱。嚴禁投入新資金追高，現有獲利部位請逢急拉減碼，跌破均價線 ({vwap:.2f}) 立刻走人！"
    else:
        title = "☠️ 死貓反彈，全面棄守"
        color = "#20c997"
        msg = f"跌破月線 ({ma20:.2f}) 的無量反彈就是死貓跳！上方套牢冤魂無數，這是在抓交替。嚴禁投入任何資金接刀，立刻將現有部位清倉轉移！"

    return sys_status, title, msg, color, radar_html


def generate_execution_script(data):
    sc = data['scenario']
    latest = data['latest']
    vVWAP, vBBUpper, vBBLower = f"{latest['TP']:.2f}", f"{latest['BBU']:.2f}", f"{latest['BBL']:.2f}"
    vMA5 = f"{latest['MA5']:.2f}"

    headClass, obs, act = "", [""] * 5, [""] * 5

    if sc == "holy_grail":
        headClass = "bg-warning text-dark"
        obs = [f"開盤即出量跳空越過 {vBBUpper}", f"踩穩均價線 ({vVWAP}) 上攻", "盤中回測皆是量縮", "高檔量滾量強勢震盪",
               "大單強勢鎖死或收最高"]
        act = ["確認突破，市價敲進底倉", f"現價不破 {vVWAP} 積極加碼", f"回測 {vVWAP} 有守果斷重壓",
               "死抱不放，讓利潤奔跑", "強勢多頭確立，安心留倉"]
    elif sc == "climax":
        headClass = "bg-dark"
        obs = ["試撮大單掛漲停誘多", f"急殺破均價線 ({vVWAP})", "反彈不過早盤高點", "留下長上影線", "收出避雷針墓碑 K"]
        act = ["防範開盤拉高出貨", f"現價 < {vVWAP} 嚴禁追高！", "逢高全數獲利了結", "絕對空手觀望",
               f"明日極易跌破 {vMA5}"]
    elif sc == "upper_bb":
        headClass = "bg-warning text-dark"
        obs = ["若夜盤不佳，極易遭狙擊", f"衝撞 {vBBUpper} 量能不足", "反彈無力站回均價線", "陷入箱型震盪",
               "收盤無法鎖死"]
        act = ["底倉偏向防守", f"觸碰 {vBBUpper} 為壓力，嚴禁追高", "逢高減碼", "T+1 勝率低，不加碼",
               "空手觀望或底倉防守"]
    elif sc == "lower_bb":
        headClass = "bg-primary text-white"
        obs = ["試撮重挫，恐慌趕底", f"觸碰 {vBBLower} 後站回 {vVWAP}", "回測不破早盤低點", "量縮窒息空軍不敢追",
               "收出下影線誘空完成"]
        act = ["準備左側抄底資金", "確認跌勢放緩", f"穩在 {vVWAP} 之上，絕佳買點", "底倉抱緊", "防守線設今日最低點"]
    elif sc == "squeeze" or sc == "strong_attack":
        headClass = "bg-danger"
        obs = ["開盤即出量跳空或開高", f"踩穩均價線 ({vVWAP}) 上攻", "盤中回測皆是量縮", "高檔量滾量強勢震盪",
               "大單強勢鎖死或收最高"]
        act = ["確認多頭突破，市價建倉", f"現價不破 {vVWAP} 積極加碼", f"回測 {vVWAP} 有守果斷重壓",
               "死抱不放，讓利潤奔跑", "強勢多頭確立，安心留倉"]
    elif sc == "margin_call" or sc == "dead_cat":
        headClass = "bg-dark"
        obs = ["試撮綠油油或弱勢", f"開高瞬間跌破 {vVWAP}", "無量崩跌或反彈爆量回落", "散戶絕望，往下漂流",
               "收最低或極長下影線"]
        act = ["嚴禁開盤摸底接刀", "絕對空手！開高走低出貨盤", "看戲讓籌碼踐踏，絕佳狙擊點", "反彈皆是逃命波",
               "無天量下影線嚴禁進場"]
    elif sc == "golden_pit":
        headClass = "bg-info text-dark"
        obs = ["試撮開低製造恐慌", f"破月線後站回 {vVWAP}", "在 LACA 附近吸籌", "量縮橫盤讓市場遺忘", "拉回收長下影線"]
        act = ["觀察是否為刻意挖坑", f"站穩 {vVWAP} 是絕佳左側試單點", "趁恐慌打底分批買進", "持股耐心續抱",
               "破 LACA 停損，否則留倉"]
    elif sc == "resting":
        headClass = "bg-secondary text-white"
        obs = ["試撮平淡", f"預估量急縮，貼著 {vVWAP} 震盪", "緩跌測試均線或 LACA", "上下波動極小", "收量縮小黑或十字線"]
        act = ["預期無聊盤整，不躁進", "量縮整理，無追價價值", "支撐不破可佈局", "嚴禁此時無腦加碼",
               f"等待回測 {vMA5} 再動作"]
    elif sc == "bull_trap":
        headClass = "bg-warning text-dark"
        obs = ["試撮異常強勢掛假單", f"急拉過高後爆量破 {vVWAP}", "股價緩跌破開盤價(A轉)", "護盤防守 LACA 避免崩盤",
               "收黑K或長上影線"]
        act = ["防範拉高出貨", f"破 {vVWAP} 嚴禁追高", f"反彈不過 {vVWAP} 是逃命波", "多單準備撤退",
               "跌破生命線明日即走"]

    return headClass, obs, act


def compute_hist_ab_verify(row, prev_row, laca):
    isAboveMA20 = row['Close'] > row['MA20']
    isMomentumBull = (row['Volume'] > row['MV5']) or (row['RSI'] > 50)
    isChipBearish = row['MFI'] < 50
    if isAboveMA20:
        if isMomentumBull:
            if isChipBearish:
                return "⚠️ 誘多反彈"
            elif row['Close'] >= row['BBU']:
                return "⚠️ 觸碰上軌"
            else:
                return "🔥 雙多頭"
        else:
            return "⚠️ 多頭量縮"
    else:
        if row['Low'] <= row['BBL'] and row['RSI'] < 45:
            return "🧲 下軌超賣"
        elif prev_row['MA20'] < row['MA20'] and row['Close'] >= laca:
            return "💎 黃金坑"
        else:
            if isMomentumBull:
                return "📉 跌深反彈"
            else:
                return "☠️ 雙空頭"


def compute_hist_pattern(row):
    if row['MA5'] > row['MA10'] and row['MA10'] > row['MA20']:
        return "📈 多頭排列"
    elif row['MA5'] < row['MA10'] and row['MA10'] < row['MA20']:
        return "📉 空頭排列"
    elif row['Close'] > row['MA20']:
        return "🔄 震盪偏多"
    else:
        return "🔄 震盪偏空"


# ==========================================
# UI 介面繪製
# ==========================================
st.title("📈 全方位個股掃描系統 (V6.2)")
st.markdown(
    "<div class='disclaimer'>本程式僅供個人與朋友間參考交流之用，不涉及任何商業用途，亦不承擔因操作或使用所產生的任何責任。</div>",
    unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    ticker_input = st.text_input("股票代號 (上市/上櫃，如 2330)", "2330")
    run_btn = st.button("🎯 啟動矩陣與圖表運算", width="stretch")

if run_btn:
    with st.spinner('連線國際市場、爬取股票名稱與執行裸K分析...'):
        data = fetch_data(ticker_input)

        if not data:
            st.error("找不到該標的，請確認代碼是否正確。")
        else:
            latest = data['latest']
            stock_name = data['stock_name']
            clean_ticker = ticker_input.replace('.TW', '').replace('.TWO', '')

            if data['atm_risk'] and data['f_buy'] < 0:
                st.markdown(f"""
                <div class="atm-alert">
                    <i class="fas fa-money-bill-wave"></i> 🚨 提款機防禦觸發：<br>
                    昨夜 ADR 大漲，但外資今日竟反向倒貨 {abs(data['f_buy']):.0f} 張！<br>標準的「趁利多拉高結帳」，嚴防開高走低！
                </div>
                """, unsafe_allow_html=True)

            sys_status, verdict_title, coach_msg, verdict_color, radar_html = get_unified_command(data)

            # ====== 第一排：大一統指令 (將雷達區塊下放，並移除所有 HTML 的左側空白縮排) ======
            st.markdown(f"""
<div style='background-color: #fff; border-left: 8px solid {verdict_color}; padding: 25px 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 8px 16px rgba(0,0,0,0.06); border: 1px solid #f1f3f5;'>
    <h3 style='color: #1a252f; font-weight: 900; margin-bottom: 18px; letter-spacing: 1px;'><i class="fas fa-user-tie"></i> 操盤手大一統指令 ({stock_name} {clean_ticker})：<span style='color: {verdict_color};'>{verdict_title}</span></h3>
    <div style='font-size: 1.1rem; color: #495057; margin-bottom: 12px;'><i class="fas fa-robot"></i> <b>系統判定：</b>{sys_status}</div>
    <div style='font-size: 1.25rem; font-weight: bold; color: #212529; line-height: 1.6; background-color: rgba(0,0,0,0.02); padding: 15px; border-radius: 8px; margin-top:15px;'><i class="fas fa-bullseye" style="color: #dc3545;"></i> <b>戰略指導：</b>{coach_msg}</div>
    {radar_html}
</div>
""", unsafe_allow_html=True)

            # ====== 第二排：總分展示 (同樣移除 HTML 縮排) ======
            total = data['total_score']
            score_color = "#198754" if total >= 70 else ("#fd7e14" if total >= 45 else "#dc3545")
            st.markdown(f"""
<div style='background: #fdfdfe; border-left: 5px solid {score_color}; padding: 15px 25px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
    <h5 style='color: #1a252f; margin-bottom: 15px;'><i class="fas fa-balance-scale"></i> 系統綜合動態權重評分 (互相關聯驗證)</h5>
    <div style='display: flex; justify-content: space-between; text-align: center; align-items: center;'>
        <div><b style='color:#6c757d'>Macro 總經 (20%)</b><br><span style='font-size: 1.6rem; color: #0dcaf0; font-weight:bold'>{data['macro_score']}</span></div>
        <div style='color:#dee2e6; font-size:1.5rem;'>+</div>
        <div><b style='color:#6c757d'>Flow 籌碼 (30%)</b><br><span style='font-size: 1.6rem; color: #fd7e14; font-weight:bold'>{data['flow_score']}</span></div>
        <div style='color:#dee2e6; font-size:1.5rem;'>+</div>
        <div><b style='color:#6c757d'>Alpha 動能 (50%)</b><br><span style='font-size: 1.6rem; color: #6f42c1; font-weight:bold'>{data['alpha_score']}</span></div>
        <div style='color:#dee2e6; font-size:1.5rem;'>=</div>
        <div><b style='color:#1a252f'>評估總結算</b><br><span style='font-size: 2rem; color: {score_color}; font-weight: 900;'>{total} <span style='font-size:1rem'>/ 100</span></span></div>
    </div>
</div>
""", unsafe_allow_html=True)

            # ====== 第三排：基礎數據觀測 ======
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("##### 📊 Alpha 絕對數值")
                pct_color = "text-up" if latest['Pct_Change'] > 0 else "text-down"
                st.markdown(
                    f"<span class='big-font {pct_color}'>收盤: {latest['Close']:.2f} ({latest['Pct_Change']:+.2f}%)</span>",
                    unsafe_allow_html=True)
                st.markdown(f"**盤中均價 (VWAP):** <span class='vwap-highlight'>{latest['TP']:.2f}</span>",
                            unsafe_allow_html=True)
                st.markdown(f"**5日線 (短防):** {latest['MA5']:.2f}")
                st.markdown('</div>', unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="card card-laca">', unsafe_allow_html=True)
                st.markdown("##### 🛡️ 核心防線觀測")
                st.markdown(f"**LACA (成本):** <span style='color:#d63384;font-weight:bold'>{data['laca']:.2f}</span>",
                            unsafe_allow_html=True)
                st.markdown(f"**月線 (波段):** {latest['MA20']:.2f}")
                st.markdown(f"**布林上軌:** <span style='color:#0d6efd'>{latest['BBU']:.2f}</span>",
                            unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c3:
                st.markdown('<div class="card card-macro">', unsafe_allow_html=True)
                st.markdown("##### 🌍 Macro 即時連動")
                st.markdown(f"<div style='font-size:1.05rem; margin-top:10px;'>{data['macro_msg']}</div>",
                            unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            c4, c5, c6 = st.columns(3)
            with c4:
                if not data['chip_ok']:
                    st.markdown(f"""
<div class="card card-flow">
    <h5 style="color: #fd7e14; font-weight: bold;">💰 Flow 法人真金白銀</h5>
    <div style="margin-top: 20px; padding: 15px; background-color: #f8d7da; color: #842029; border-radius: 5px; font-size: 0.95rem; font-weight: bold; text-align:center;">
        <i class="fas fa-exclamation-triangle"></i> 無法獲取籌碼資料
    </div>
</div>
""", unsafe_allow_html=True)
                else:
                    f_act = f"連買 {data['f_days']} 天" if data['f_days'] > 0 else (
                        f"連賣 {abs(data['f_days'])} 天" if data['f_days'] < 0 else "無動靜")
                    t_act = f"連買 {data['t_days']} 天" if data['t_days'] > 0 else (
                        f"連賣 {abs(data['t_days'])} 天" if data['t_days'] < 0 else "無動靜")
                    f_buy, t_buy = data['f_buy'], data['t_buy']
                    if f_buy < 0 and t_buy > 0:
                        health_msg = "🛡️ 內資護盤 (良性換手)：外資提款，投信連續吃貨。"
                    elif f_buy > 0 and t_buy > 0:
                        health_msg = "🔥 土洋齊買 (強勢集中)：籌碼極度集中，推升動能強勁！"
                    elif f_buy < 0 and t_buy < 0:
                        health_msg = "☠️ 土洋齊賣 (失血警戒)：法人共識偏空，上檔壓力沉重。"
                    else:
                        health_msg = "⚖️ 法人分歧 (震盪沉澱)：籌碼無單一方向，短線依賴技術面。"

                    st.markdown(f"""
<div class="card card-flow">
    <h5 style="color: #fd7e14; font-weight: bold;">💰 Flow 法人真金白銀</h5>
    <div style="font-size: 0.95rem; line-height: 1.8;">
        <b>外資動向:</b> 今日 {f_buy:.0f} 張 | {f_act}<br>
        <b>投信動向:</b> 今日 {t_buy:.0f} 張 | {t_act}<br>
    </div>
    <div style="margin-top: 10px; padding: 8px; background-color: #fff3cd; color: #856404; border-radius: 5px; font-size: 0.85rem; font-weight: bold;">
        健康度: {health_msg}
    </div>
</div>
""", unsafe_allow_html=True)

            with c5:
                st.markdown(f"""
<div class="card card-mom">
    <h5 style="color: #198754; font-weight: bold;">📈 動能與轉折偵測</h5>
    <div style="font-size: 0.95rem; line-height: 2.0; margin-top: 10px;">
        <b>RSI(14):</b> {latest['RSI']:.1f} [{data['rsi_shape']}]<br>
        <b>MFI(14):</b> {latest['MFI']:.1f} [{data['mfi_shape']}]<br>
        <b>OBV動能:</b> [{data['obv_shape']}]<br>
    </div>
</div>
""", unsafe_allow_html=True)

            with c6:
                st.markdown(f"""
<div class="card card-logic">
    <h5 style="color: #6f42c1; font-weight: bold;">💡 邏輯防呆與交叉驗證</h5>
    <div style="font-size: 0.85rem; line-height: 1.6;">
        <b>均線評級:</b> <span style='color: {"#d4af37" if data["a_rank"] == "S+" else "#212529"}; font-weight:bold;'>[{data['a_rank']}]</span> {data['a_desc']}<br>
        <b>動能評級:</b> <span style='color: {"#d4af37" if data["b_rank"] in ["S+", "B-"] else "#212529"}; font-weight:bold;'>[{data['b_rank']}]</span> {data['b_desc']}<br>
    </div>
    <div style="margin-top: 8px; padding: 8px; background-color: rgba(111, 66, 193, 0.1); border-left: 3px solid #6f42c1; border-radius: 4px; font-size: 0.85rem;">
        <b>綜合判定: {data['logic_title']}</b><br>{data['logic_msg']}
    </div>
</div>
""", unsafe_allow_html=True)

            st.divider()

            # ====== 第四排：實戰操盤劇本與裸K掃描 ======
            col_t3_left, col_t3_right = st.columns([5, 4])

            with col_t3_left:
                headClass, obs, act = generate_execution_script(data)
                st.markdown(f"### ⚔️ 盤中 5 大動態決戰時刻 (Live T+1) - {stock_name}")
                st.markdown(f"""
<table class="table table-bordered exec-table mb-5">
    <thead class="{headClass}">
        <tr>
            <th style="width: 15%">時間點</th><th style="width: 45%">⚔️ 盤面表象與動態觀測</th><th style="width: 40%">🎯 操盤手防呆指令</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="fw-bold">08:50 - 09:00<br><span class="text-muted small">競價</span></td><td>{obs[0]}</td><td style="background-color: #f8f9fa">{act[0]}</td></tr>
        <tr><td class="fw-bold">09:00 - 09:30<br><span class="text-muted small">開盤</span></td><td>{obs[1]}</td><td style="background-color: #f8f9fa">{act[1]}</td></tr>
        <tr><td class="fw-bold">09:45 - 10:15<br><span class="text-muted small">洗盤</span></td><td>{obs[2]}</td><td style="background-color: #f8f9fa">{act[2]}</td></tr>
        <tr><td class="fw-bold">11:30 - 12:00<br><span class="text-muted small">真空</span></td><td>{obs[3]}</td><td style="background-color: #f8f9fa">{act[3]}</td></tr>
        <tr><td class="fw-bold">13:00 - 13:25<br><span class="text-muted small">尾盤</span></td><td>{obs[4]}</td><td style="background-color: #f8f9fa">{act[4]}</td></tr>
    </tbody>
</table>
""", unsafe_allow_html=True)

            with col_t3_right:
                pa = data['pa_flags']
                st.markdown(f"### 🕯️ 裸 K 價格行為 (V6 語義學診斷)")
                pa_html = "<div class='pa-card'>"

                # 多方加分區
                pa_html += "<div class='pa-title' style='color:#198754; font-size: 1.05rem; font-weight:900; margin-bottom:10px;'><i class='fas fa-chart-line'></i> 📈 爆發 / 反轉信號 (加分區)</div>"
                has_bull_pa = False
                if pa["pa7_three_soldiers"]:
                    has_bull_pa = True
                    pa_html += "<div class='pa-item-active' style='background-color:#d1e7dd; color:#0f5132; border-left-color:#198754;'>🚀 【紅三白兵】：連續三日紅 K 階梯式墊高，多方氣勢極強！</div>"
                if not has_bull_pa:
                    pa_html += "<div class='pa-item-inactive'>✅ 暫無特殊多頭 K 線組合</div>"

                # 空方否決區
                pa_html += "<div class='pa-title' style='color:#dc3545; font-size: 1.05rem; font-weight:900; margin-top:25px; margin-bottom:10px;'><i class='fas fa-exclamation-triangle'></i> 🚨 崩跌 / 誘多警告 (否決區)</div>"
                has_bear_pa = False
                if pa["pa1_no_limit"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-active'>⚠️ 【高位震盪出貨】：拉伸 +7% 卻無法鎖死漲停，並留下上影線！</div>"
                if pa["pa2_gap_down"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-danger'>🩸 【極度危險】：低開 -3% 且放量持續下跌，盤中毫無反彈買盤！</div>"
                if pa["pa3_engulf"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-active'>⚠️ 【多空逆轉】：早盤高開，收盤卻跌破昨日收盤 (中翻綠)！</div>"
                if pa["pa4_stagnant"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-active'>⚠️ 【高位放量滯漲】：股價連 3 日高位爆量卻無法突破前高！</div>"
                if pa["pa5_trap"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-active'>⚠️ 【誘多釣魚陷阱】：早盤急拉創高後爆量回落，留下尖銳極長上影線！</div>"
                if pa["pa6_ma_break"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-danger'>☠️ 【趨勢終結確認】：股價跌破生命線 (20MA) 且兩日內無法收回！</div>"
                if pa["pa8_three_crows"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-danger'>☠️ 【黑三烏鴉】：連續三日實體黑 K 殺跌，空軍強烈倒貨，遠離！</div>"

                if not has_bear_pa:
                    pa_html += "<div class='pa-item-inactive' style='color:#198754; font-weight:bold; background-color:#f8f9fa;'><i class='fas fa-shield-alt'></i> 未觸發任何空頭警報，實體動能健康。</div>"

                pa_html += "</div>"
                st.markdown(pa_html, unsafe_allow_html=True)

            st.divider()

            # ====== 第五排：繪製 Plotly 雙圖表 ======
            st.markdown(f"### 📊 趨勢圖表與動能資金流 - {stock_name}")

            df_plot = data['df'].tail(120).copy()
            df_plot.index = df_plot.index.strftime('%y/%m/%d')

            col_chart1, col_chart2 = st.columns([2, 1])

            with col_chart1:
                fig1 = go.Figure()
                fig1.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['Close'], name='收盤價', line=dict(color='#2c3e50', width=2),
                               marker=dict(color='#2c3e50', size=4)))
                fig1.add_trace(go.Scatter(x=df_plot.index, y=[data['laca']] * len(df_plot), name='LACA防線',
                                          line=dict(color='#d63384', width=2, dash='dash')))
                fig1.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['MA5'], name='5MA', line=dict(color='#fcd456', width=1.5)))
                fig1.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['MA20'], name='20MA', line=dict(color='#dc3545', width=1.5)))
                fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA111'], name='111DMA (Pi線)',
                                          line=dict(color='#6f42c1', width=2)))
                fig1.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['BBU'], name='布林上軌', line=dict(color='#0d6efd', width=1)))
                fig1.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['BBL'], name='布林下軌', line=dict(color='#0d6efd', width=1),
                               fill='tonexty', fillcolor='rgba(13, 110, 253, 0.05)'))

                fig1.update_layout(
                    title=dict(text="📈 股價、LACA防守線、布林通道 與 Pi線", font=dict(size=16)),
                    height=500, margin=dict(l=10, r=10, t=50, b=100), template="plotly_white", hovermode="x unified",
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
                )
                fig1.update_xaxes(tickangle=-45)
                st.plotly_chart(fig1, width="stretch")

            with col_chart2:
                fig2 = make_subplots(specs=[[{"secondary_y": True}]])
                fig2.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['RSI'], name='RSI(14)', line=dict(color='#198754', width=2)),
                    secondary_y=False)
                fig2.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['MFI'], name='MFI(14)', line=dict(color='#fd7e14', width=2)),
                    secondary_y=False)
                fig2.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['OBV'], name='OBV', line=dict(color='#0dcaf0', width=1.5)),
                    secondary_y=True)

                fig2.update_layout(
                    title=dict(text="📊 動能與資金流 (RSI / MFI / OBV)", font=dict(size=16)),
                    height=500, margin=dict(l=10, r=10, t=50, b=100), template="plotly_white", hovermode="x unified",
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
                )
                fig2.update_yaxes(range=[0, 100], secondary_y=False)
                fig2.update_yaxes(showgrid=False, secondary_y=True)
                fig2.update_xaxes(tickangle=-45)
                st.plotly_chart(fig2, width="stretch")

            # ====== 第六排：60日歷史動態回測表 ======
            col_t1, col_t2 = st.columns([4, 1])
            with col_t1:
                st.markdown(f"### 📋 {stock_name} ({clean_ticker}) 近期 60 日交易數據回測")

            df_hist = data['df'].tail(61).copy()
            csv_rows = ["日期,收盤,漲跌,漲跌幅(%),成交量(張),MA5,MA20,LACA防線,Pi線,RSI(14),MFI(14),AB驗證,型態"]
            rows_html = []

            for i in range(len(df_hist) - 1, 0, -1):
                row = df_hist.iloc[i]
                prev = df_hist.iloc[i - 1]
                date_str = df_hist.index[i].strftime('%y/%m/%d')

                c_color = "text-danger" if row['Pct_Change'] > 0 else ("text-success" if row['Pct_Change'] < 0 else "")
                change_str = f"{row['Close'] - prev['Close']:+.1f} ({row['Pct_Change']:+.2f}%)"
                vol_str = f"{int(row['Volume'] / 1000)}k"

                ab_v = compute_hist_ab_verify(row, prev, data['laca'])
                pat = compute_hist_pattern(row)

                if "黃金坑" in ab_v or "洗盤" in ab_v or "超賣" in ab_v:
                    ab_html = f"<span class='badge-hist' style='color:#d4af37; font-weight:bold;'>{ab_v}</span>"
                elif "突破" in ab_v or "雙多頭" in ab_v:
                    ab_html = f"<span class='badge-hist' style='color:#0d6efd; font-weight:bold;'>{ab_v}</span>"
                elif "竭盡" in ab_v or "壓力" in ab_v or "誘多" in ab_v:
                    ab_html = f"<span class='badge-hist bg-warning text-dark fw-bold'><i class='fas fa-exclamation-triangle'></i> {ab_v}</span>"
                else:
                    ab_html = f"<span class='badge-hist text-muted'>{ab_v}</span>"

                tr_content = f'<tr><td class="fw-bold">{date_str}</td><td class="{c_color} fw-bold">{row["Close"]:.2f}</td><td class="{c_color}">{change_str}</td><td>{vol_str}</td><td>{row["MA5"]:.2f}</td><td>{row["MA20"]:.2f}</td><td style="color:#d63384; font-weight:bold;">{data["laca"]:.2f}</td><td style="color:#6f42c1; font-weight:bold;">{row["MA111"]:.2f}</td><td>{row["RSI"]:.1f}</td><td>{row["MFI"]:.1f}</td><td>{ab_html}</td><td><small class="text-muted">{pat}</small></td></tr>'
                rows_html.append(tr_content)

                csv_ab = ab_v.replace('⚠️ ', '').replace('🔥 ', '').replace('🧲 ', '').replace('💎 ', '').replace('📉 ',
                                                                                                               '').replace(
                    '☠️ ', '')
                csv_pat = pat.replace('📈 ', '').replace('📉 ', '').replace('🔄 ', '')
                csv_rows.append(
                    f"{date_str},{row['Close']:.2f},{row['Close'] - prev['Close']:.1f},{row['Pct_Change']:.2f}%,{int(row['Volume'] / 1000)},{row['MA5']:.2f},{row['MA20']:.2f},{data['laca']:.2f},{row['MA111']:.2f},{row['RSI']:.1f},{row['MFI']:.1f},{csv_ab},{csv_pat}")

            csv_text = "\n".join(csv_rows)
            csv_bytes = ("\uFEFF" + csv_text).encode('utf-8')

            with col_t2:
                st.download_button(
                    label="📥 下載 CSV 數據",
                    data=csv_bytes,
                    file_name=f"{stock_name}_{clean_ticker}_V6.2_Analysis.csv",
                    mime="text/csv",
                    width="stretch"
                )

            hist_html = "".join(rows_html)
            table_wrapper = f"""<div style="max-height: 500px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 8px;">
<table class="table table-hover table-striped mb-0 hist-table">
<thead><tr><th>日期</th><th>收盤</th><th>漲跌</th><th>量</th><th>MA5</th><th>MA20</th><th style="color: #ff91c4;">LACA</th><th style="color: #b18de6;">Pi線</th><th>RSI(14)</th><th>MFI(14)</th><th>AB驗證</th><th>型態</th></tr></thead>
<tbody>{hist_html}</tbody>
</table>
</div>"""
            st.markdown(table_wrapper, unsafe_allow_html=True)
