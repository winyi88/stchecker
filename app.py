import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import datetime
import warnings
import re
import io
import logging
from contextlib import redirect_stdout, redirect_stderr
import plotly.graph_objects as go

warnings.simplefilter(action='ignore', category=FutureWarning)

# ==========================================
# 終極防破版 HTML 渲染函數
# ==========================================
def render_html(html_str):
    cleaned_html = re.sub(r'\s+', ' ', html_str).strip()
    st.markdown(cleaned_html, unsafe_allow_html=True)

# ==========================================
# 雙重備援 ROE 獲取引擎 (V8.10 核心修復)
# ==========================================
def get_robust_roe(ticker, tk_obj):
    """
    解決 Streamlit Cloud IP 被 Yahoo API 阻擋的問題。
    Method 1: yfinance 原生獲取 (本機端極快)。
    Method 2: 若被擋，啟動物理爬蟲直接拆解 Yahoo 台灣 HTML。
    """
    # Method 1: yfinance 原生
    try:
        roe = tk_obj.info.get('returnOnEquity', None)
        if roe is not None:
            return roe * 100
    except:
        pass
    
    # Method 2: Yahoo 台灣 HTML 暴力備援 (免疫 Cloudflare API 封鎖)
    clean_ticker = ticker.replace('.TW', '').replace('.TWO', '')
    try:
        url = f"https://tw.stock.yahoo.com/quote/{clean_ticker}/profile"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            # 尋找 "股東權益報酬率" 後面的第一個百分比數字
            match = re.search(r'股東權益報酬率.*?([0-9\.\-]+)%', res.text, re.IGNORECASE | re.DOTALL)
            if match:
                return float(match.group(1))
    except:
        pass
        
    return None

# ==========================================
# 頁面配置與自訂 CSS
# ==========================================
st.set_page_config(page_title="全方位個股掃描系統 V8.10", layout="wide", page_icon="🏦")

render_html("""
<style>
    .vwap-highlight { background-color: rgba(13, 110, 253, 0.1); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(13, 110, 253, 0.3); font-weight: bold; color: #084298;}
    .pro-card {
        background-color: #ffffff; border-radius: 12px; padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); height: 100%; min-height: 230px;
        border: 1px solid #f1f3f5; transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .pro-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.08); transform: translateY(-2px); }
    .pro-title {
        font-size: 1.1rem; font-weight: 800; color: #1a252f; margin-bottom: 12px; padding-bottom: 10px;
        border-bottom: 2px solid #f8f9fa; display: flex; align-items: center; gap: 8px;
    }
    .pro-label { font-size: 0.85rem; color: #6c757d; font-weight: 600; margin-top: 10px; margin-bottom: 4px;}
    .card-rs { border-top: 4px solid #d4af37; }
    .card-vpvr { border-top: 4px solid #6f42c1; }
    .card-atr { border-top: 4px solid #dc3545; }
    .card-flow { border-top: 4px solid #fd7e14; }
    .card-mom { border-top: 4px solid #198754; }
    .card-logic { border-top: 4px solid #343a40; }
    .card-pa { border-top: 4px solid #ffc107; min-height: unset; height: 100%;}
    .card-table { border-top: 4px solid #1a252f; min-height: unset; height: 100%;}
    .engine-desc { background-color: #f8f9fa; border-left: 4px solid #adb5bd; padding: 10px; margin-top: 12px; border-radius: 4px; font-size: 0.85rem; line-height: 1.5; color: #495057;}
    .engine-desc span { font-weight: bold; color: #1a252f; }
    .pa-item-active { padding: 8px 12px; margin-bottom: 8px; border-radius: 6px; font-weight: bold; font-size: 0.9rem; border-left: 4px solid #ffc107; background-color: #fff3cd; color: #856404;}
    .pa-item-danger { padding: 8px 12px; margin-bottom: 8px; border-radius: 6px; font-weight: bold; font-size: 0.9rem; border-left: 4px solid #dc3545; background-color: #f8d7da; color: #842029;}
    .pa-item-bull { padding: 8px 12px; margin-bottom: 8px; border-radius: 6px; font-weight: bold; font-size: 0.9rem; border-left: 4px solid #198754; background-color: #d1e7dd; color: #0f5132;}
    .pa-item-inactive { color: #adb5bd; padding: 6px 12px; margin-bottom: 6px; font-size: 0.85rem; border-left: 3px solid #e9ecef; background-color: #f8f9fa; border-radius: 6px;}
    .atm-alert { background: linear-gradient(135deg, #fff3cd 0%, #ffc107 100%); color: #856404; border-radius: 8px; padding: 12px 20px; margin-bottom: 20px; text-align: center; font-weight: bold;}
    .disclaimer { text-align: center; color: #adb5bd; font-size: 0.85rem; padding: 10px; margin-bottom: 25px; border-bottom: 1px dashed #dee2e6; }
    .exec-table th { background-color: #1a252f !important; color: #fff !important; text-align: center; vertical-align: middle; padding: 10px;}
    .exec-table td { vertical-align: middle; line-height: 1.5; padding: 10px; font-size: 0.95rem;}
    .hist-table th { position: sticky; top: 0; background-color: #1a252f !important; color: white !important; z-index: 10; text-align: center; white-space: nowrap;}
    .hist-table td { text-align: center; vertical-align: middle; font-size: 0.9rem; white-space: nowrap; padding: 8px;}
    .badge-hist { font-size: 0.8rem; padding: 4px 8px; border-radius: 4px; display: inline-block;}
</style>
""")

@st.cache_data(ttl=86400)
def get_stock_name(ticker):
    clean_ticker = ticker.replace('.TW', '').replace('.TWO', '')
    try:
        url = f"https://tw.stock.yahoo.com/quote/{clean_ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            match = re.search(r'<title>(.*?)\s*\(', res.text)
            if match: return match.group(1).replace("Yahoo奇摩股市", "").strip()
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
    if v0 > v1 and v1 > v2: return "持續上揚 ↗"
    elif v0 < v1 and v1 < v2: return "持續向下 ↘"
    elif v0 > v1 and v1 <= v2: return "向上拐彎轉折 ⤴"
    elif v0 < v1 and v1 >= v2: return "向下拐彎轉折 ⤵"
    else: return "震盪平移 →"

@st.cache_data(ttl=300)
def fetch_macro_and_adr():
    f = io.StringIO()
    with redirect_stdout(f), redirect_stderr(f):
        try:
            dji = yf.download("^DJI", period="5d", progress=False, auto_adjust=True)
            sp500 = yf.download("^GSPC", period="5d", progress=False, auto_adjust=True)
            sox = yf.download("^SOX", period="5d", progress=False, auto_adjust=True)
            n225 = yf.download("^N225", period="5d", progress=False, auto_adjust=True)
            szse = yf.download("399001.SZ", period="5d", progress=False, auto_adjust=True)
            ewt = yf.download("EWT", period="5d", progress=False, auto_adjust=True)
            usdtwd = yf.download("TWD=X", period="5d", progress=False, auto_adjust=True)

            def get_pct(df):
                try:
                    close_vals = df['Close'].squeeze()
                    if isinstance(close_vals, pd.DataFrame): close_vals = close_vals.iloc[:, 0]
                    return float((close_vals.iloc[-1] - close_vals.iloc[-2]) / close_vals.iloc[-2] * 100)
                except:
                    return 0.0

            dji_pct, sp500_pct, sox_pct = get_pct(dji), get_pct(sp500), get_pct(sox)
            n225_pct, szse_pct = get_pct(n225), get_pct(szse)
            ewt_pct, usdtwd_pct = get_pct(ewt), get_pct(usdtwd)
            expected_twii_pct = ewt_pct + usdtwd_pct

            atm_risk = (sox_pct < -2.0 or expected_twii_pct < -1.5) and (
                        datetime.datetime.now().day >= 23 or datetime.datetime.now().day <= 3)
            exp_color = "#dc3545" if expected_twii_pct < 0 else "#198754"
            ewt_color = "#dc3545" if ewt_pct < 0 else "#198754"
            usd_color = "#dc3545" if usdtwd_pct < 0 else "#198754"

            macro_msg = f"""
            <div style="font-size: 0.9rem; line-height: 1.6; margin-bottom: 10px;">
                <b>🐛 美股:</b> 道瓊 {dji_pct:+.2f}% | S&P {sp500_pct:+.2f}% | 費半 <span style="color:{'#dc3545' if sox_pct < 0 else '#198754'}">{sox_pct:+.2f}%</span><br>
                <b>🌏 亞洲:</b> 日經 {n225_pct:+.2f}% | 深圳 {szse_pct:+.2f}%
            </div>
            <div style="padding: 12px; background-color: rgba(13, 110, 253, 0.05); border-left: 4px solid #0d6efd; border-radius: 6px;">
                <div style="font-size: 0.9rem; font-weight: bold; color: #084298; margin-bottom: 4px;"><i class="fas fa-calculator"></i> 台股大盤開盤預測模型</div>
                <div style="font-size: 1.3rem; font-weight: 900; color: {exp_color}; margin-bottom: 4px;">預測大盤 ≈ {expected_twii_pct:+.2f}%</div>
                <div style="font-size: 0.8rem; color: #495057;">
                    <b>推演公式</b>：EWT 夜盤 (<span style="color:{ewt_color}">{ewt_pct:+.2f}%</span>) + USD/TWD 匯率 (<span style="color:{usd_color}">{usdtwd_pct:+.2f}%</span>)
                </div>
                <div style="font-size: 0.75rem; color: #adb5bd; margin-top: 4px;">
                    (註：外資以美元定價 EWT，換算台幣需加上匯率波動以得真實台股預期)
                </div>
            </div>
            """
            macro_score = 10 + (3 if sp500_pct >= 0.5 else (-3 if sp500_pct <= -0.5 else 0)) + \
                          (5 if sox_pct >= 1.0 else (-5 if sox_pct <= -1.0 else 0)) + \
                          (2 if expected_twii_pct >= 0.5 else (-2 if expected_twii_pct <= -0.5 else 0))
            if atm_risk: macro_score -= 10
            return atm_risk, macro_msg, max(0, min(20, macro_score))
        except Exception as e:
            return False, "國際連動暫無資料", 10

@st.cache_data(ttl=60)
def fetch_chip_data(stock_id):
    url = "https://api.finmindtrade.com/api/v4/data"
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=25)).strftime("%Y-%m-%d")
    params = {"dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_id": str(stock_id), "start_date": start_date, "end_date": end_date}
    try:
        res = requests.get(url, params=params, timeout=5).json()
        if not res.get("data"): return 0, 0, 0, 0, 15, False
        df = pd.DataFrame(res["data"])
        df['Net_Buy'] = (df['buy'] - df['sell']) / 1000
        pivot = df.pivot_table(index='date', columns='name', values='Net_Buy', aggfunc='sum').fillna(0)
        f_series = pivot.get('Foreign_Investor', pd.Series([0]))
        t_series = pivot.get('Investment_Trust', pd.Series([0]))
        f_buy, t_buy = f_series.iloc[-1] if not f_series.empty else 0, t_series.iloc[-1] if not t_series.empty else 0
        f_days, _ = get_consecutive_trend(f_series)
        t_days, _ = get_consecutive_trend(t_series)
        flow_score = 15 + (5 if f_buy > 0 else (-5 if f_buy < 0 else 0)) + (5 if f_days >= 2 else (-5 if f_days <= -2 else 0)) + \
                     (5 if t_buy > 0 else (-5 if t_buy < 0 else 0)) + (5 if t_days >= 2 else (-5 if t_days <= -2 else 0))
        return f_buy, t_buy, f_days, t_days, max(0, min(30, flow_score)), True
    except:
        return 0, 0, 0, 0, 15, False

@st.cache_data(ttl=300)
def fetch_data(ticker):
    yf_logger = logging.getLogger('yfinance')
    original_level = yf_logger.level
    yf_logger.setLevel(logging.CRITICAL)
    
    f = io.StringIO()
    with redirect_stdout(f), redirect_stderr(f):
        query_ticker = f"{ticker}.TW" if not ticker.endswith(('.TW', '.TWO')) else ticker
        
        # 【V8.10 新增】強制注入真實瀏覽器 Header Session 降低雲端被擋機率
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        tk_obj = yf.Ticker(query_ticker, session=session)
        df = tk_obj.history(period="1y", auto_adjust=True)
        
        if df.empty and not ticker.endswith(('.TW', '.TWO')):
            query_ticker = f"{ticker}.TWO"
            tk_obj = yf.Ticker(query_ticker, session=session)
            df = tk_obj.history(period="1y", auto_adjust=True)
            
        twii = yf.download("^TWII", period="1y", progress=False, auto_adjust=True)
        
    yf_logger.setLevel(original_level)

    if df.empty: return None
    stock_name = get_stock_name(ticker)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    if isinstance(twii.columns, pd.MultiIndex): twii.columns = twii.columns.get_level_values(0)

    # 【V8.10 新增】調用雙重備援 ROE 引擎
    roe_val = get_robust_roe(ticker, tk_obj)

    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    
    df['MV5'] = df['Volume'].rolling(5).mean()
    df['MV20'] = df['Volume'].rolling(20).mean()
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
    std = df['Close'].rolling(20).std()
    df['BBU'] = df['MA20'] + (2 * std)
    df['BBL'] = df['MA20'] - (2 * std)
    df['BBW'] = (df['BBU'] - df['BBL']) / df['MA20'] * 100
    df['Pct_Change'] = df['Close'].pct_change() * 100

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

    recent_120 = df.tail(120)
    hist, bin_edges = np.histogram(recent_120['Close'], bins=20, weights=recent_120['Volume'])
    max_bin_idx = np.argmax(hist)
    poc_price = (bin_edges[max_bin_idx] + bin_edges[max_bin_idx + 1]) / 2

    df['TR'] = np.maximum((df['High'] - df['Low']),
                          np.maximum(abs(df['High'] - df['Close'].shift(1)), abs(df['Low'] - df['Close'].shift(1))))
    df['ATR'] = df['TR'].rolling(14).mean()
    df['ATR_Stop'] = df['High'].rolling(10).max() - (2.5 * df['ATR'])

    stock_60d_ret = (df['Close'].iloc[-1] - df['Close'].iloc[-60]) / df['Close'].iloc[-60] * 100 if len(df) >= 60 else 0
    twii_60d_ret = (twii['Close'].iloc[-1] - twii['Close'].iloc[-60]) / twii['Close'].iloc[-60] * 100 if not twii.empty and len(twii) >= 60 else 0
    rs_outperform = stock_60d_ret - twii_60d_ret

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    f_buy, t_buy, f_days, t_days, flow_score, chip_ok = fetch_chip_data(ticker.replace('.TW', '').replace('.TWO', ''))
    atm_risk, macro_msg, macro_score = fetch_macro_and_adr()

    ma20_shape = get_trend_shape(df['MA20'])
    rsi_shape = get_trend_shape(df['RSI'])
    mfi_shape = get_trend_shape(df['MFI'])
    obv_shape = get_trend_shape(df['OBV'])

    n_shape_data = {'is_valid': False, 'first_bottom': 0, 'first_high': 0, 'second_bottom': 0, 'fib_1x': 0, 'fib_1618': 0}
    if len(df) >= 60:
        recent_60_df = df.iloc[-60:]
        first_bottom = recent_60_df['Low'].min()
        idx_bottom = recent_60_df['Low'].idxmin()
        after_bottom_df = df.loc[idx_bottom:]
        if len(after_bottom_df) > 5:
            first_high = after_bottom_df['High'].max()
            idx_high = after_bottom_df['High'].idxmax()
            after_high_df = df.loc[idx_high:]
            if len(after_high_df) > 1:
                second_bottom = after_high_df['Low'].min()
                if (second_bottom > first_bottom) and (first_high > first_bottom * 1.05) and (latest['Close'] > second_bottom):
                    n_shape_data['is_valid'] = True
                    n_shape_data['first_bottom'] = first_bottom
                    n_shape_data['first_high'] = first_high
                    n_shape_data['second_bottom'] = second_bottom
                    n_shape_data['fib_1x'] = second_bottom + (first_high - first_bottom) * 1.0
                    n_shape_data['fib_1618'] = second_bottom + (first_high - first_bottom) * 1.618

    pa_flags = {
        "pa1_no_limit": False, "pa2_gap_down": False, "pa3_engulf": False, "pa4_stagnant": False, "pa5_trap": False,
        "pa6_ma_break": False, "pa7_three_soldiers": False, "pa8_three_crows": False, "pa9_bull_pinbar": False,
        "pa10_bull_engulfing": False
    }
    upperShadow = latest['High'] - max(latest['Open'], latest['Close'])
    lowerShadow = min(latest['Open'], latest['Close']) - latest['Low']
    realBody = abs(latest['Close'] - latest['Open'])

    if len(df) >= 5:
        prev2 = df.iloc[-3]
        pa_flags["pa1_no_limit"] = (latest['High'] >= prev['Close'] * 1.07) and (latest['Close'] < prev['Close'] * 1.095) and (upperShadow > realBody * 0.5)
        pa_flags["pa2_gap_down"] = (latest['Open'] <= prev['Close'] * 0.97) and (latest['Close'] <= latest['Open']) and (latest['Volume'] > latest['MV5'])
        pa_flags["pa3_engulf"] = (latest['Open'] > prev['Close']) and (latest['Close'] < prev['Close'])
        recent_3_highs_max = df['High'].iloc[-3:].max()
        pa_flags["pa4_stagnant"] = (latest['Close'] > latest['MA20']) and (latest['RSI'] > 60) and (recent_3_highs_max <= df['High'].iloc[-4]) and (df['Volume'].iloc[-3:].mean() > latest['MV20'])
        pa_flags["pa5_trap"] = (upperShadow > realBody * 2) and (latest['High'] >= df['High'].iloc[-5:].max()) and (latest['Volume'] > latest['MV5']) and latest['RSI'] > 65
        pa_flags["pa6_ma_break"] = (prev2['Close'] >= prev2['MA20']) and (prev['Close'] < prev['MA20']) and (latest['Close'] < latest['MA20'])
        pa_flags["pa7_three_soldiers"] = (latest['Close'] > latest['Open']) and (prev['Close'] > prev['Open']) and (prev2['Close'] > prev2['Open']) and (latest['Close'] > prev['Close'])
        pa_flags["pa8_three_crows"] = (latest['Close'] < latest['Open']) and (prev['Close'] < prev['Open']) and (prev2['Close'] < prev2['Open']) and (latest['Close'] < prev['Close'])
        pa_flags["pa9_bull_pinbar"] = (lowerShadow > realBody * 2) and ((latest['Low'] <= latest['BBL'] * 1.01) or (latest['Low'] <= latest['MA60'])) and latest['RSI'] < 35
        pa_flags["pa10_bull_engulfing"] = (prev['Close'] < prev['Open']) and (latest['Open'] < prev['Close']) and (latest['Close'] > prev['Open']) and (latest['Close'] > latest['Open']) and latest['RSI'] < 50

    pa_penalty = 25 if (pa_flags["pa2_gap_down"] or pa_flags["pa6_ma_break"] or pa_flags["pa8_three_crows"]) else (15 if (pa_flags["pa1_no_limit"] or pa_flags["pa3_engulf"] or pa_flags["pa4_stagnant"] or pa_flags["pa5_trap"]) else 0)
    pa_bonus = 20 if (pa_flags["pa9_bull_pinbar"] or pa_flags["pa10_bull_engulfing"]) else (10 if pa_flags["pa7_three_soldiers"] else 0)

    is_squeezed = False
    is_vol_surge = False
    is_price_breakout = False
    is_obv_surge = False
    is_holy_grail = False
    if len(df) > 65:
        is_squeezed = bool(df['BBW'].iloc[-6:-1].min() <= (df['BBW'].iloc[-61:-1].min() * 1.15))
        is_vol_surge = bool(latest['Volume'] > (df['MV20'].shift(1).iloc[-1] * 2.5))
        is_price_breakout = bool((latest['Close'] > latest['BBU']) and (latest['Close'] > latest['Open']))
        is_obv_surge = bool(df['OBV_Diff'].iloc[-1] > df['OBV_Diff'].shift(1).rolling(20).max().iloc[-1])
        is_holy_grail = is_squeezed and is_vol_surge and is_price_breakout and is_obv_surge

    ma_up = "上揚" in ma20_shape or "向上" in ma20_shape
    ma_down = "向下" in ma20_shape
    if latest['Close'] >= latest['MA20'] and ma_up: a_rank, a_desc = "A+", "20日線上升且現價站穩月線"
    elif latest['Close'] < latest['MA20'] and ma_down: a_rank, a_desc = "A-", "20日線下彎且跌破月線"
    else: a_rank, a_desc = "A", "均線平移或方向分歧"

    up_count = sum(1 for s in [rsi_shape, mfi_shape] if "上揚" in s or "向上" in s)
    down_count = sum(1 for s in [rsi_shape, mfi_shape] if "向下" in s)
    if up_count == 2 or (up_count == 1 and down_count == 0): b_rank, b_desc = "B+", "RSI/MFI 買盤動能共振向上"
    elif down_count == 2 or (down_count == 1 and up_count == 0): b_rank, b_desc = "B-", "RSI/MFI 賣壓動能共振向下"
    else: b_rank, b_desc = "B", "RSI/MFI 動能分歧或平移震盪"

    if pa_penalty > 0: a_rank, b_rank = "A-", "B-"
    elif pa_bonus > 0: a_rank, b_rank = "A+", "B+"

    if a_rank == "A+" and b_rank == "B+": title, msg = "趨勢動能共振 (強勢攻擊)", "大結構偏多且短線買盤強勁。"
    elif a_rank == "A+" and b_rank in ["B", "B-"]: title, msg = "多頭回檔洗盤 (長多短空)", "主因：20MA反映長線『趨勢』仍在墊高；RSI/MFI反映近幾日『短線震盪』。"
    elif a_rank == "A-" and b_rank in ["B+", "B"]: title, msg = "左側背離潛伏 (長空短多)", "主因：長線趨勢雖偏空，但底層動能率先發動。"
    elif a_rank == "A-" and b_rank == "B-": title, msg = "空頭共振探底 (極度弱勢)", "長線與短線同步下殺。切勿阻擋墜落的刀子！"
    elif a_rank == "A" and b_rank == "B+": title, msg = "震盪轉強突破 (醞釀表態)", "長線處於過渡期，短線資金點火。"
    elif a_rank == "A" and b_rank == "B-": title, msg = "震盪轉弱防守 (面臨考驗)", "動能衰退，需嚴格防守下方支撐。"
    else: title, msg = "多空分歧沉澱 (方向未明)", "趨勢與動能尚無共識，觀望為主。"

    alpha_score = max(0, (25 if a_rank in ["A+", "S+"] else (15 if a_rank == "A" else 0)) + (25 if b_rank in ["B+", "S+"] else (15 if b_rank == "B" else 0)) - pa_penalty + pa_bonus)
    total_score = max(0, min(100, macro_score + flow_score + alpha_score))

    scenario_type = "default"
    if is_holy_grail: scenario_type = "holy_grail"
    elif pa_flags["pa9_bull_pinbar"] or pa_flags["pa10_bull_engulfing"]: scenario_type = "golden_pit"
    elif latest['Close'] > latest['MA20'] and t_buy >= 0: scenario_type = "strong_attack"
    elif latest['Close'] > latest['MA20'] and f_buy < 0 and t_buy < 0: scenario_type = "bull_trap"
    else: scenario_type = "dead_cat"

    df.index = df.index.tz_localize(None)
    return {
        "df": df, "latest": latest, "prev": prev, "stock_name": stock_name,
        "scenario": scenario_type, "pa_flags": pa_flags, "pa_penalty": pa_penalty,
        "a_rank": a_rank, "a_desc": a_desc, "b_rank": b_rank, "b_desc": b_desc, "logic_title": title, "logic_msg": msg,
        "f_buy": f_buy, "t_buy": t_buy, "f_days": f_days, "t_days": t_days, "chip_ok": chip_ok,
        "atm_risk": atm_risk, "macro_msg": macro_msg, "macro_score": macro_score, "flow_score": flow_score,
        "alpha_score": alpha_score, "total_score": total_score,
        "rsi_shape": rsi_shape, "mfi_shape": mfi_shape, "obv_shape": obv_shape,
        "hg_flags": {"squeezed": is_squeezed, "vol_surge": is_vol_surge, "breakout": is_price_breakout, "obv_surge": is_obv_surge},
        "n_shape": n_shape_data, "roe": roe_val, "poc_price": poc_price, "atr_stop": latest['ATR_Stop'],
        "rs_outperform": rs_outperform
    }

def get_unified_command(data, macro_html):
    sc = data['scenario']
    vwap = data['latest']['TP']
    poc = data['poc_price']
    atr_s = data['atr_stop']
    hg = data['hg_flags']
    rs = data['rs_outperform']
    
    latest_vol = data['latest']['Volume']
    mv20 = data['latest']['MV20']
    vol_ratio = latest_vol / mv20 if pd.notna(mv20) and mv20 > 0 else 1

    if vol_ratio < 0.5:
        vol_state, vol_desc, vol_color = "低量", f"僅20日均量 {vol_ratio*100:.0f}%", "#6c757d"
    elif vol_ratio < 0.85:
        vol_state, vol_desc, vol_color = "偏低", f"約20日均量 {vol_ratio*100:.0f}%", "#adb5bd"
    elif vol_ratio <= 1.15:
        vol_state, vol_desc, vol_color = "20日平均", "量能持平", "#1a252f"
    elif vol_ratio <= 2.0:
        vol_state, vol_desc, vol_color = "平均之上", f"達20日均量 {vol_ratio*100:.0f}%", "#fd7e14"
    else:
        vol_state, vol_desc, vol_color = "放量", f"高達20日均量 {vol_ratio:.1f} 倍", "#dc3545"

    vol_badge = f"<div style='display:inline-block; background-color:{vol_color}15; color:{vol_color}; padding:4px 10px; border-radius:6px; font-size:0.95rem; margin-top:8px; border:1px solid {vol_color}40;'><i class='fas fa-water'></i> 當日量能狀態：<b>{vol_state}</b> ({vol_desc})</div>"

    if hg['squeezed'] and hg['vol_surge'] and hg['breakout'] and hg['obv_surge']: radar_result = "<span style='color:#dc3545; font-weight:900;'>型態符合 🚀</span>"
    elif hg['squeezed']: radar_result = "<span style='color:#fd7e14; font-weight:900;'>型態築底中 ⏳</span>"
    else: radar_result = "<span style='color:#6c757d; font-weight:900;'>型態不符 ❌</span>"

    radar_macro_html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px; align-items: stretch;">
        <div style="flex: 1; min-width: 350px; background-color: #fdfdfe; padding: 15px 20px; border-radius: 8px; border: 1px dashed #ced4da; display: flex; flex-direction: column;">
            <div style="display: flex; align-items: center; border-bottom: 1px solid #dee2e6; padding-bottom: 8px; margin-bottom: 10px;">
                <div style="flex-grow: 1;"><i class="fas fa-radar" style="color:#6f42c1;"></i> <b style="font-size: 1.05rem;">聖杯型態偵測雷達</b></div>
                <div>{radar_result}</div>
            </div>
            <div style="line-height: 1.8; font-size: 0.95rem; color:#1a252f;">
                {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['squeezed'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ① 布林帶寬達近 60 日極限壓縮<br>
                {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['vol_surge'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ② 爆發大於 20 日均量 2.5 倍之天量<br>
                {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['breakout'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ③ 實體紅 K 強勢貫穿布林上軌<br>
                {'<span style="color:#198754; font-weight:bold;">✅</span>' if hg['obv_surge'] else '<span style="color:#dc3545; font-weight:bold;">❌</span>'} ④ OBV 資金斜率突破近 20 日最高峰
            </div>
        </div>
        <div style="flex: 1; min-width: 350px; background-color: #f0f8ff; padding: 15px 20px; border-radius: 8px; border: 1px dashed #b6d4fe; display: flex; flex-direction: column;">
            <div style="border-bottom: 1px solid #dee2e6; padding-bottom: 8px; margin-bottom: 10px;">
                <i class="fas fa-globe-asia" style="color:#0dcaf0;"></i> <b style="font-size: 1.05rem; color:#1a252f;">Macro 亞洲共振連動</b>
            </div>
            <div style="line-height: 1.8; font-size: 0.95rem; color:#1a252f;">
                {macro_html}
            </div>
        </div>
    </div>
    """

    if sc == "holy_grail":
        if rs > 0:
            sys_status = "<span style='color:#d4af37; font-weight:900; font-size:1.15rem;'><i class='fas fa-crown'></i> 強勢領頭羊：觸發【聖杯型態】且 RS 大於 0！</span>"
            title, color = "🌟 聖杯起漲點：極致壓縮爆發！", "#d4af37"
            msg = f"這是一次<b style='color:#dc3545;'>極高勝率</b>的聖杯突破！股價已踩在 VPVR 籌碼鐵底 ({poc:.2f}) 之上，且 RS 跑贏大盤。請重倉買進，並以 ATR 停損價 ({atr_s:.2f}) 作為底線，讓利潤狂奔！"
        else:
            sys_status = "<span style='color:#fd7e14; font-weight:900; font-size:1.15rem;'><i class='fas fa-exclamation-circle'></i> 補漲型聖杯：觸發【聖杯型態】但 RS 落後大盤！</span>"
            title, color = "🐢 底部補漲突破：嚴防假突破", "#fd7e14"
            msg = f"【跨模組警告】本檔觸發聖杯，但其 RS 落後大盤 {abs(rs):.1f}%。這代表它並非市場主力領頭羊，而是『資金輪動補漲』。爆發力可能較弱，建議縮小倉位，採取打短平快策略，嚴防一日行情！"
    elif data['atm_risk'] and data['f_buy'] < 0:
        sys_status = "<span class='text-danger fw-bold'>🔴 總經提款警戒：外資逢高結帳，台股面臨開高走低風險。</span>"
        title, color, msg = "🚨 外資提款，嚴格觀望", "#dc3545", "國際股市動盪且外資倒貨，今日極易開高走低，嚴禁進場！"
    elif data['pa_penalty'] > 0:
        sys_status = "<span class='text-danger fw-bold'>🚨 裸 K 否決權觸發：發現主力出貨或誘多特徵，強制降級劇本！</span>"
        title, color, msg = "☠️ 裸K動能轉弱，準備撤退", "#dc3545", "實體 K 線出現危險特徵，請立刻減碼，跌破 ATR 停損即刻清倉。"
    else:
        sys_status = "<span class='text-success fw-bold'>🟢 資金環境正常，依循 Alpha 與籌碼模組判定。</span>"
        if data['latest']['Close'] < poc:
            title, color = "☠️ 跌破主力成本區，極度危險！", "#dc3545"
            msg = f"股價已跌破過去半年的最大成交密集區 (POC: {poc:.2f})，上方全數變為套牢賣壓。嚴禁接刀！"
        elif sc == "strong_attack":
            title, color, msg = "🚀 穩站籌碼鐵底，多頭延續", "#0d6efd", f"目前股價踩在主力大本營 ({poc:.2f}) 上。只要不跌破 ATR 動態防守線 ({atr_s:.2f})，請死抱不放！"
        elif sc == "golden_pit":
            title, color, msg = "💎 完美底部洗盤，左側試單", "#0dcaf0", f"主力刻意挖坑！現價若站穩均價線 ({vwap:.2f})，這是極難得的黃金左側買點。請立刻準備建倉！"
        elif sc == "bull_trap":
            title, color, msg = "⚠️ 籌碼背離誘多，準備撤退", "#fd7e14", f"趨勢雖撐，但底層資金抽離！嚴禁投入新資金追高，跌破均價線立刻走人！"
        else:
            title, color, msg = "⚖️ 震盪盤整：等待方向表態", "#1a252f", f"股價反覆測試，多空勢均力敵。建議空手觀望，等待帶量脫離此區域再行佈局。"

    final_sys_status = f"{sys_status}<br>{vol_badge}"
    return final_sys_status, title, msg, color, radar_macro_html

def generate_execution_script(data):
    sc = data['scenario']
    latest = data['latest']
    vVWAP = f"{latest['TP']:.2f}"
    vBBUpper = f"{latest['BBU']:.2f}"

    if sc in ["holy_grail", "strong_attack"]:
        obs = [f"開盤即出量跳空越過 {vBBUpper}", f"踩穩均價線 ({vVWAP}) 上攻", "盤中回測皆是量縮", "高檔量滾量強勢震盪", "大單強勢鎖死或收最高"]
        act = ["確認突破，市價敲進底倉", f"現價不破 {vVWAP} 積極加碼", f"回測 {vVWAP} 有守果斷重壓", "死抱不放，讓利潤奔跑", "強勢多頭確立，安心留倉"]
    elif sc == "golden_pit":
        obs = ["試撮開低製造恐慌", f"破底後強勢站回 {vVWAP}", "在 POC 附近吸籌", "量縮橫盤讓市場遺忘", "拉回收長下影線或吞噬紅K"]
        act = ["觀察是否為刻意洗盤", f"站穩 {vVWAP} 是絕佳左側試單點", "趁恐慌打底分批買進", "持股耐心續抱", "破今日低點停損，否則留倉"]
    else:
        obs = ["試撮異常強勢掛假單", f"急拉過高後爆量破 {vVWAP}", "股價緩跌破開盤價(A轉)", "護盤防守避免崩盤", "收黑K或長上影線"]
        act = ["防範拉高出貨", f"破 {vVWAP} 嚴禁追高", f"反彈不過 {vVWAP} 是逃命波", "多單準備撤退", "跌破生命線明日即走"]
    return obs, act

def compute_hist_ab_verify(row, prev_row, poc_price):
    isAboveMA20 = row['Close'] > row['MA20']
    isMomentumBull = (row['Volume'] > row['MV5']) or (row['RSI'] > 50)
    isChipBearish = row['MFI'] < 50
    if isAboveMA20:
        if isMomentumBull: return "⚠️ 誘多反彈" if isChipBearish else ("⚠️ 觸碰上軌" if row['Close'] >= row['BBU'] else "🔥 雙多頭")
        else: return "⚠️ 多頭量縮"
    else:
        if row['Low'] <= row['BBL'] and row['RSI'] < 45: return "🧲 下軌超賣"
        elif prev_row['MA20'] < row['MA20'] and row['Close'] >= poc_price: return "💎 黃金坑"
        else: return "📉 跌深反彈" if isMomentumBull else "☠️ 雙空頭"

def compute_hist_pattern(row):
    if row['MA5'] > row['MA10'] and row['MA10'] > row['MA20']: return "📈 多頭排列"
    elif row['MA5'] < row['MA10'] and row['MA10'] < row['MA20']: return "📉 空頭排列"
    elif row['Close'] > row['MA20']: return "🔄 震盪偏多"
    else: return "🔄 震盪偏空"

# ==========================================
# UI 介面繪製
# ==========================================
st.title("🏦 全方位個股掃描系統 V8.10 (QuantSight)")
render_html("<div class='disclaimer'>本程式僅供個人及親友交流使用，不涉及商業用途。使用者須自行承擔使用過程中之風險，開發者不對任何直接或間接損害、法律責任或爭議負責。</div>")

col1, col2 = st.columns([1, 3])
with col1:
    ticker_input = st.text_input("股票代號 (如 2330)", "")
    run_btn = st.button("🚀 啟動EchoScan運算", width="stretch")

if run_btn and ticker_input:
    with st.spinner('連線五大指數、繪製動能儀表板與執行 3D 機構矩陣...'):
        data = fetch_data(ticker_input)

        if not data:
            st.error("找不到該標的，請確認代碼是否正確。")
        else:
            latest = data['latest']
            stock_name = data['stock_name']
            clean_ticker = ticker_input.replace('.TW', '').replace('.TWO', '')

            # ====== Row 2: Hero Banner ======
            roe = data['roe']
            if roe is not None:
                if roe >= 15: light, color, desc = "🟢", "#198754", "極佳 (獲利資優生)"
                elif roe >= 12: light, color, desc = "🟢", "#198754", "好公司 (符合標準)"
                elif roe >= 8: light, color, desc = "🟡", "#fd7e14", "普通 (尚可接受)"
                else: light, color, desc = "🔴", "#dc3545", "偏弱 (資金效率低)"
                roe_display = f"{roe:.2f}%"
            else:
                light, color, desc, roe_display = "⚪", "#6c757d", "無資料", "--"

            pct_color = "#dc3545" if latest['Pct_Change'] > 0 else "#20c997"
            sign = "+" if latest['Pct_Change'] > 0 else ""
            latest_vol_sheets = int(latest['Volume'] / 1000)

            render_html(f"""
            <div style="display:flex; background:#fff; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,0.05); border:1px solid #e9ecef; margin-top:10px; margin-bottom:25px;">
                <div style="flex:1; border-right:1px solid #e9ecef; padding-right:20px;">
                    <div style="color:#6c757d; font-weight:bold; font-size:0.95rem; margin-bottom:5px;">📊 Alpha 最新報價與盤中基準</div>
                    <div style="font-size:2.8rem; font-weight:900; color:{pct_color};">{latest['Close']:.2f} <span style="font-size:1.4rem;">({sign}{latest['Pct_Change']:.2f}%)</span></div>
                    <div style="margin-top:12px; font-size:1.1rem; color:#495057; font-weight:600;">
                        <span style="margin-right:20px;">盤中均價 (VWAP): <span class="vwap-highlight">{latest['TP']:.2f}</span></span>
                        <span style="margin-right:20px;">5日線 (短防): <b style="color:#1a252f;">{latest['MA5']:.2f}</b></span>
                        <span>成交量: <b style="color:#0d6efd;">{latest_vol_sheets:,} 張</b></span>
                    </div>
                </div>
                <div style="flex:1; padding-left:30px; display:flex; flex-direction:column; justify-content:center;">
                    <div style="color:#6c757d; font-weight:bold; font-size:0.95rem; margin-bottom:5px;">🛡️ 基本面護城河 (ROE 股東權益報酬率)</div>
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-top:5px;">
                        <div style="font-size:2.8rem; font-weight:900; color:{color};">{light} {roe_display}</div>
                        <div style="background:{color}15; color:#212529; padding:10px 20px; border-radius:30px; font-weight:800; font-size:1.15rem; border:1px solid {color}30;">{desc}</div>
                    </div>
                </div>
            </div>
            """)

            if data['atm_risk'] and data['f_buy'] < 0:
                render_html(f"""
                <div class="atm-alert">
                    <i class="fas fa-money-bill-wave"></i> 🚨 提款機防禦觸發：昨夜美股費半大跌，且外資今日反向倒貨 {abs(data['f_buy']):.0f} 張！標準的「趁利多拉高結帳」，嚴防開高走低！
                </div>
                """)

            # ====== Row 3: 大一統指令 ======
            sys_status, verdict_title, coach_msg, verdict_color, radar_macro_html = get_unified_command(data, data['macro_msg'])

            render_html(f"""
            <div style="background-color: #fff; border-left: 8px solid {verdict_color}; padding: 25px 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 8px 16px rgba(0,0,0,0.06); border: 1px solid #f1f3f5;">
                <h3 style="color: #1a252f; font-weight: 900; margin-bottom: 18px; letter-spacing: 1px;"><i class="fas fa-user-tie"></i> 操盤手大一統指令 ({stock_name} {clean_ticker})：<span style="color: {verdict_color};">{verdict_title}</span></h3>
                <div style="font-size: 1.1rem; color: #495057; margin-bottom: 12px; line-height: 1.6;"><i class="fas fa-robot"></i> <b>系統判定：</b>{sys_status}</div>
                <div style="font-size: 1.15rem; font-weight: bold; color: #212529; line-height: 1.6; background-color: rgba(0,0,0,0.02); padding: 15px; border-radius: 8px; margin-top:15px;"><i class="fas fa-bullseye" style="color: #dc3545;"></i> <b>戰略指導：</b>{coach_msg}</div>
                {radar_macro_html}
            </div>
            """)

            # ====== Row 4: 系統綜合評分 ======
            total = data['total_score']
            score_color = "#198754" if total >= 70 else ("#fd7e14" if total >= 45 else "#dc3545")
            render_html(f"""
            <div style="background: #fdfdfe; border-left: 5px solid {score_color}; padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #e9ecef;">
                <h5 style="color: #1a252f; margin-bottom: 15px; font-weight:800;"><i class="fas fa-balance-scale"></i> 系統綜合動態權重評分 (互相關聯驗證)</h5>
                <div style="display: flex; justify-content: space-between; text-align: center; align-items: center;">
                    <div><b style="color:#6c757d; font-size:0.9rem;">Macro 總經 (20%)</b><br><span style="font-size: 1.8rem; color: #0dcaf0; font-weight:900;">{data['macro_score']}</span></div>
                    <div style="color:#dee2e6; font-size:1.5rem;">+</div>
                    <div><b style="color:#6c757d; font-size:0.9rem;">Flow 籌碼 (30%)</b><br><span style="font-size: 1.8rem; color: #fd7e14; font-weight:900;">{data['flow_score']}</span></div>
                    <div style="color:#dee2e6; font-size:1.5rem;">+</div>
                    <div><b style="color:#6c757d; font-size:0.9rem;">Alpha 動能 (50%)</b><br><span style="font-size: 1.8rem; color: #6f42c1; font-weight:900;">{data['alpha_score']}</span></div>
                    <div style="color:#dee2e6; font-size:1.5rem;">=</div>
                    <div style="background:{score_color}10; padding:10px 20px; border-radius:8px;"><b style="color:#1a252f">評估總結算</b><br><span style="font-size: 2.2rem; color: {score_color}; font-weight: 900;">{total} <span style="font-size:1.2rem">/ 100</span></span></div>
                </div>
            </div>
            """)

            # ====== Row 5: V8 機構級三大核心引擎 ======
            st.markdown(f"<h3 style='color:#1a252f; margin-top:10px; margin-bottom:15px; font-weight:800;'><i class='fas fa-cogs'></i> V8 機構級 3D 立體戰略引擎</h3>", unsafe_allow_html=True)
            ce1, ce2, ce3 = st.columns(3)
            with ce1:
                rs = data['rs_outperform']
                rs_color = "#dc3545" if rs > 0 else "#198754"
                max_bar = 30.0
                rs_w_right = min(max(0, rs) / max_bar * 50, 50)
                rs_w_left = min(max(0, -rs) / max_bar * 50, 50)
                rs_desc = "🔥 <b>強勢領漲</b>：資金高度青睞的市場領頭羊！" if rs > 0 else "🐢 <b>弱勢落後</b>：資金未進駐，若有上漲多屬跌深反彈。"
                
                render_html(f"""
                <div class="pro-card card-rs">
                    <div class="pro-title">🥇 RS 相對大盤強弱</div>
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <div class="pro-label">近 60 日 vs 台灣加權</div>
                        <div style="font-size: 1.8rem; font-weight: 900; color: {rs_color};">{'+' if rs > 0 else ''}{rs:.1f}%</div>
                    </div>
                    <div style="width: 100%; height: 8px; background-color: #e9ecef; border-radius: 4px; position: relative; margin-top: 5px; margin-bottom: 12px;">
                        <div style="position: absolute; left: 50%; top: -3px; bottom: -3px; width: 2px; background-color: #1a252f; z-index: 2;"></div>
                        <div style="position: absolute; left: 50%; width: {rs_w_right}%; height: 100%; background-color: #dc3545; border-radius: 0 4px 4px 0;"></div>
                        <div style="position: absolute; right: 50%; width: {rs_w_left}%; height: 100%; background-color: #198754; border-radius: 4px 0 0 4px;"></div>
                    </div>
                    <div style="font-size:0.85rem; color:#495057; text-align:center; margin-bottom:10px;">{rs_desc}</div>
                    <div class="engine-desc">
                        <span>【責任範圍】</span>：負責<b>『選股』</b>。過濾跟風股，專找贏過大盤的領頭羊。
                    </div>
                </div>
                """)

            with ce2:
                vpvr_status = "🟢 踩在鐵底上 (支撐)" if latest['Close'] >= data['poc_price'] else "🔴 跌破籌碼區 (壓力)"
                n_shape = data['n_shape']
                if n_shape['is_valid']:
                    n_html = f"""
                    <div style="margin-top:15px; padding-top:12px; border-top:1px dashed #dee2e6;">
                        <div class="pro-label" style="margin-top:0;">🌊 N 字波段測幅 (已打出第二腳)</div>
                        <div style="font-size: 1.4rem; font-weight: 900; color: #dc3545; display:flex; align-items:center; gap:8px;">
                            🎯 {n_shape['fib_1618']:.2f} 
                            <span style="font-size:0.75rem; color:#198754; font-weight:bold; background:#d1e7dd; padding:3px 6px; border-radius:4px;"><i class="fas fa-check"></i> N字成型</span>
                        </div>
                    </div>
                    """
                else:
                    n_html = f"""
                    <div style="margin-top:15px; padding-top:12px; border-top:1px dashed #dee2e6;">
                        <div class="pro-label" style="margin-top:0;">🌊 N 字波段測幅</div>
                        <div style="font-size: 1.05rem; font-weight: bold; color: #6c757d; margin-bottom:4px;">⏳ 未達 N 字條件</div>
                        <div style="font-size: 0.8rem; color: #adb5bd; line-height:1.4;">
                            (尚未打出墊高支撐的第二隻腳，或處於空頭/初升段，無法預測)
                        </div>
                    </div>
                    """
                render_html(f"""
                <div class="pro-card card-vpvr">
                    <div class="pro-title">🧱 籌碼鐵底與 N 字目標</div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <div class="pro-label" style="margin-top:0;">VPVR 籌碼控制點</div>
                            <div style="font-size: 1.8rem; font-weight: 900; color: #6f42c1;">{data['poc_price']:.2f}</div>
                            <div class="pro-label" style="margin-top:5px; color:#212529;">現價: <b>{vpvr_status}</b></div>
                        </div>
                        <div style="width: 50%; padding-left:10px;">
                            {n_html}
                        </div>
                    </div>
                    <div class="engine-desc" style="margin-top:12px;">
                        <span>【責任範圍】</span>：負責<b>『定底與預測』</b>。VPVR 找主力大本營；N 字過濾是否具備主升段。
                    </div>
                </div>
                """)

            with ce3:
                atr_stop = data['atr_stop']
                c_price = latest['Close']
                atr_dist_pct = (c_price - atr_stop) / c_price * 100

                atr_bar_w = min(max(0, atr_dist_pct) / 10.0 * 100, 100)
                if atr_dist_pct > 5:
                    atr_color = "#198754"
                    atr_msg = "🟢 距離防線尚遠，安全抱單"
                elif atr_dist_pct > 0:
                    atr_color = "#fd7e14"
                    atr_msg = "🟡 靠近停損防線，高度警戒"
                else:
                    atr_color = "#dc3545"
                    atr_bar_w = 0
                    atr_msg = "🔴 已跌破防線，建議立刻離場"

                render_html(f"""
                <div class="pro-card card-atr">
                    <div class="pro-title">🛡️ ATR 動態追蹤停損</div>
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <div>
                            <div class="pro-label" style="margin-top:0;">機構級防守線</div>
                            <div style="font-size: 1.8rem; font-weight: 900; color: #dc3545;">{atr_stop:.2f}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="pro-label" style="margin-top:0;">安全緩衝距離</div>
                            <div style="font-size: 1.3rem; font-weight: 900; color:{atr_color};">{'+' if atr_dist_pct > 0 else ''}{atr_dist_pct:.1f}%</div>
                        </div>
                    </div>
                    <div style="width: 100%; height: 6px; background-color: #e9ecef; border-radius: 3px; margin-top: 5px; position: relative;">
                        <div style="position: absolute; right: 0; width: {atr_bar_w}%; height: 100%; background-color: {atr_color}; border-radius: 3px;"></div>
                    </div>
                    <div style="font-size: 0.85rem; color: {atr_color}; text-align: right; margin-top: 4px; font-weight:bold;">{atr_msg}</div>
                    <div class="engine-desc" style="margin-top:10px;">
                        <span>【定義】</span>：近10日最高價 - (2.5 × ATR波動率)。<br>
                        <span>【責任範圍】</span>：負責<b>『讓利潤狂奔』</b>。自動給予合理洗盤空間，不會輕易被甩下車。
                    </div>
                </div>
                """)

            # ====== Row 6: 籌碼、動能、邏輯 ======
            st.write("")
            c4, c5, c6 = st.columns(3)
            with c4:
                if not data['chip_ok']:
                    render_html("""
                    <div class="pro-card card-flow">
                        <div class="pro-title">💰 Flow 法人真金白銀</div>
                        <div style="margin-top: 20px; padding: 15px; background-color: #f8d7da; color: #842029; border-radius: 8px; font-weight: bold; text-align:center;">
                            <i class="fas fa-exclamation-triangle"></i> 無法獲取籌碼資料
                        </div>
                    </div>
                    """)
                else:
                    f_act = f"連買 {data['f_days']} 天" if data['f_days'] > 0 else (f"連賣 {abs(data['f_days'])} 天" if data['f_days'] < 0 else "無動靜")
                    t_act = f"連買 {data['t_days']} 天" if data['t_days'] > 0 else (f"連賣 {abs(data['t_days'])} 天" if data['t_days'] < 0 else "無動靜")
                    f_buy, t_buy = data['f_buy'], data['t_buy']
                    if f_buy < 0 and t_buy > 0: health_msg = "🛡️ 內資護盤 (良性換手)"
                    elif f_buy > 0 and t_buy > 0: health_msg = "🔥 土洋齊買 (強勢集中)"
                    elif f_buy < 0 and t_buy < 0: health_msg = "☠️ 土洋齊賣 (失血警戒)"
                    else: health_msg = "⚖️ 法人分歧 (震盪沉澱)"

                    render_html(f"""
                    <div class="pro-card card-flow">
                        <div class="pro-title">💰 Flow 法人真金白銀</div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                            <div><div class="pro-label">外資動向</div><div class="pro-text" style="color:{'#dc3545' if f_buy > 0 else '#198754'};">今日 {f_buy:.0f} 張 | {f_act}</div></div>
                            <div><div class="pro-label">投信動向</div><div class="pro-text" style="color:{'#dc3545' if t_buy > 0 else '#198754'};">今日 {t_buy:.0f} 張 | {t_act}</div></div>
                        </div>
                        <div style="padding: 12px; background-color: #fff3cd; color: #856404; border-radius: 8px; font-size: 0.95rem; font-weight: bold; line-height: 1.5; text-align:center;">
                            健康度: {health_msg}
                        </div>
                    </div>
                    """)

            with c5:
                rsi_val = latest['RSI']
                mfi_val = latest['MFI']
                obv_shape = data['obv_shape']
                rsi_shape = data['rsi_shape']
                mfi_shape = data['mfi_shape']

                def get_trend_color(shape_str):
                    if "上揚" in shape_str or "向上" in shape_str: return "#198754"
                    if "向下" in shape_str or "下彎" in shape_str: return "#dc3545"
                    return "#6c757d"

                rsi_color = get_trend_color(rsi_shape)
                mfi_color = get_trend_color(mfi_shape)
                obv_color = get_trend_color(obv_shape)

                render_html(f"""
                <div class="pro-card card-mom">
                    <div class="pro-title">📈 動能與轉折偵測 (儀表板)</div>
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: bold; color: #495057; margin-bottom: 4px;">
                            <span>RSI(14) <span style="color:{rsi_color}; font-size:0.8rem; margin-left:4px;">({rsi_shape})</span></span>
                            <span style="color:#212529; font-size: 1.05rem;">{rsi_val:.1f}</span>
                        </div>
                        <div style="width: 100%; height: 8px; display: flex; border-radius: 4px; overflow: hidden;">
                            <div style="width: 30%; background-color: #0dcaf0;"></div>
                            <div style="width: 40%; background-color: #e9ecef;"></div>
                            <div style="width: 30%; background-color: #dc3545;"></div>
                        </div>
                        <div style="position: relative; top: -11px; left: {rsi_val}%; margin-left: -4px; width: 8px; height: 14px; background-color: #1a252f; border-radius: 2px; border: 1px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>
                    </div>
                    <div style="margin-bottom: 18px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: bold; color: #495057; margin-bottom: 4px;">
                            <span>MFI(14) 資金流 <span style="color:{mfi_color}; font-size:0.8rem; margin-left:4px;">({mfi_shape})</span></span>
                            <span style="color:#212529; font-size: 1.05rem;">{mfi_val:.1f}</span>
                        </div>
                        <div style="width: 100%; height: 8px; display: flex; border-radius: 4px; overflow: hidden;">
                            <div style="width: 30%; background-color: #0dcaf0;"></div>
                            <div style="width: 40%; background-color: #e9ecef;"></div>
                            <div style="width: 30%; background-color: #dc3545;"></div>
                        </div>
                        <div style="position: relative; top: -11px; left: {mfi_val}%; margin-left: -4px; width: 8px; height: 14px; background-color: #1a252f; border-radius: 2px; border: 1px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; background-color: #f8f9fa; padding: 10px 15px; border-radius: 8px; border: 1px solid #e9ecef;">
                        <span style="font-weight: bold; color: #495057; font-size: 0.9rem;">OBV 實體資金動向</span>
                        <span style="font-weight: 900; color: {obv_color}; font-size: 1.05rem;">{obv_shape}</span>
                    </div>
                </div>
                """)

            with c6:
                cross_alert = ""
                if data['scenario'] == "holy_grail" and data['rs_outperform'] < 0:
                    cross_alert = f"<div style='margin-top: 10px; padding: 8px; background-color: #fff3cd; border-left: 4px solid #fd7e14; border-radius: 4px; font-size: 0.85rem; color: #856404; font-weight:bold;'>⚠️ 跨模組警示：本檔觸發聖杯，但 RS 落後大盤，屬【資金輪動補漲】，爆發力恐不如主流股！</div>"

                render_html(f"""
                <div class="pro-card card-logic">
                    <div class="pro-title">💡 邏輯防呆與交叉驗證</div>
                    <div style="margin-bottom:8px;"><span class="pro-label">均線評級:</span> <span style="color: {'#d4af37' if data['a_rank'] == 'S+' else '#212529'}; font-weight:900; font-size:1.05rem;">[{data['a_rank']}]</span> <span class="pro-text" style="font-size:0.9rem;">{data['a_desc']}</span></div>
                    <div style="margin-bottom:12px;"><span class="pro-label">動能評級:</span> <span style="color: {'#d4af37' if data['b_rank'] in ['S+', 'B-'] else '#212529'}; font-weight:900; font-size:1.05rem;">[{data['b_rank']}]</span> <span class="pro-text" style="font-size:0.9rem;">{data['b_desc']}</span></div>
                    <div style="padding: 10px; background-color: rgba(111, 66, 193, 0.05); border-left: 4px solid #6f42c1; border-radius: 6px; font-size: 0.9rem; line-height: 1.5;">
                        <b style="color:#6f42c1;">綜合判定: {data['logic_title']}</b><br><span style="color:#495057;">{data['logic_msg']}</span>
                    </div>
                    {cross_alert}
                </div>
                """)

            st.divider()

            # ====== Row 7: Live T+1 與 裸K診斷 ======
            col_t3_left, col_t3_right = st.columns([5, 4])

            with col_t3_left:
                obs, act = generate_execution_script(data)
                render_html(f"""
                <div class="pro-card card-table">
                    <div class="pro-title">⚔️ 盤中 5 大動態決戰時刻 (Live T+1) - {stock_name}</div>
                    <table class="table table-hover table-bordered exec-table mb-0" style="width: 100%; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <thead>
                            <tr>
                                <th style="width: 15%; background-color:#1a252f; color:white;">時間點</th>
                                <th style="width: 45%; background-color:#1a252f; color:white;">⚔️ 盤面表象與動態觀測</th>
                                <th style="width: 40%; background-color:#1a252f; color:white;">🎯 操盤手防呆指令</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td style="font-weight:bold; text-align:center;">08:50 - 09:00<br><span style="color:#adb5bd; font-size:0.8rem;">競價</span></td><td>{obs[0]}</td><td style="background-color: #f8f9fa">{act[0]}</td></tr>
                            <tr><td style="font-weight:bold; text-align:center;">09:00 - 09:30<br><span style="color:#adb5bd; font-size:0.8rem;">開盤</span></td><td>{obs[1]}</td><td style="background-color: #f8f9fa">{act[1]}</td></tr>
                            <tr><td style="font-weight:bold; text-align:center;">09:45 - 10:15<br><span style="color:#adb5bd; font-size:0.8rem;">洗盤</span></td><td>{obs[2]}</td><td style="background-color: #f8f9fa">{act[2]}</td></tr>
                            <tr><td style="font-weight:bold; text-align:center;">11:30 - 12:00<br><span style="color:#adb5bd; font-size:0.8rem;">真空</span></td><td>{obs[3]}</td><td style="background-color: #f8f9fa">{act[3]}</td></tr>
                            <tr><td style="font-weight:bold; text-align:center;">13:00 - 13:25<br><span style="color:#adb5bd; font-size:0.8rem;">尾盤</span></td><td>{obs[4]}</td><td style="background-color: #f8f9fa">{act[4]}</td></tr>
                        </tbody>
                    </table>
                </div>
                """)

            with col_t3_right:
                pa = data['pa_flags']
                bull_power = (15 if pa["pa7_three_soldiers"] else 0) + (20 if pa["pa9_bull_pinbar"] else 0) + (25 if pa["pa10_bull_engulfing"] else 0)
                bear_power = (10 if pa["pa1_no_limit"] else 0) + (25 if pa["pa2_gap_down"] else 0) + (15 if pa["pa3_engulf"] else 0) + (15 if pa["pa4_stagnant"] else 0) + (20 if pa["pa5_trap"] else 0) + (25 if pa["pa6_ma_break"] else 0) + (25 if pa["pa8_three_crows"] else 0)
                total_power = bull_power + bear_power
                bull_pct = (bull_power / total_power * 100) if total_power > 0 else 50
                bear_pct = (bear_power / total_power * 100) if total_power > 0 else 50

                pa_html = f"""
                <div class='pro-card card-pa'>
                    <div class='pro-title'>🕯️ 裸 K 價格行為 (V8.10 語義學診斷)</div>
                    <div style="margin-bottom: 25px; padding: 15px; background-color: #fdfdfe; border-radius: 8px; border: 1px solid #dee2e6; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: 800; font-size: 0.95rem;">
                            <span style="color: #198754;"><i class="fas fa-arrow-up"></i> 多方攻擊力道 ({bull_power})</span>
                            <span style="color: #dc3545;">空方出貨力道 ({bear_power}) <i class="fas fa-arrow-down"></i></span>
                        </div>
                        <div style="width: 100%; height: 16px; background-color: #e9ecef; border-radius: 8px; overflow: hidden; display: flex;">
                            <div style="width: {bull_pct}%; background-color: #20c997; height: 100%; transition: width 1s ease;"></div>
                            <div style="width: {bear_pct}%; background-color: #ff6b6b; height: 100%; transition: width 1s ease;"></div>
                        </div>
                    </div>
                """
                pa_html += "<div style='color:#198754; font-size: 1.05rem; font-weight:900; margin-bottom:10px;'><i class='fas fa-chart-line'></i> 📈 爆發 / 反轉信號 (加分區)</div>"
                has_bull_pa = False
                if pa["pa7_three_soldiers"]:
                    has_bull_pa = True
                    pa_html += "<div class='pa-item-bull'>🚀 【紅三白兵】：連續三日紅 K 階梯式墊高，多方氣勢極強！</div>"
                if pa["pa9_bull_pinbar"]:
                    has_bull_pa = True
                    pa_html += "<div class='pa-item-bull'>🧲 【底部探底神針】：極度超賣區留下超長下影線，主力強勢洗盤測底成功！</div>"
                if pa["pa10_bull_engulfing"]:
                    has_bull_pa = True
                    pa_html += "<div class='pa-item-bull'>💎 【破底翻吞噬】：昨日殺跌破底，今日開低走高以實體紅 K 強勢包覆，完美誘空軋空！</div>"
                if not has_bull_pa:
                    pa_html += "<div class='pa-item-inactive'>✅ 暫無特殊多頭 K 線組合</div>"

                pa_html += "<div style='color:#dc3545; font-size: 1.05rem; font-weight:900; margin-top:25px; margin-bottom:10px;'><i class='fas fa-exclamation-triangle'></i> 🚨 崩跌 / 誘多警告 (否決區)</div>"
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
                    pa_html += "<div class='pa-item-active'>⚠️ 【高位避雷針誘多】：高位階急拉創高後爆量回落，留下尖銳極長上影線，跟風必套！</div>"
                if pa["pa6_ma_break"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-danger'>☠️ 【趨勢終結確認】：股價跌破生命線 (20MA) 且兩日內無法收回！</div>"
                if pa["pa8_three_crows"]:
                    has_bear_pa = True
                    pa_html += "<div class='pa-item-danger'>☠️ 【黑三烏鴉】：連續三日實體黑 K 殺跌，空軍強烈倒貨，遠離！</div>"
                if not has_bear_pa:
                    pa_html += "<div class='pa-item-inactive' style='color:#198754; font-weight:bold; background-color:#f8f9fa;'><i class='fas fa-shield-alt'></i> 未觸發任何空頭警報，實體動能健康。</div>"

                pa_html += "</div>"
                render_html(pa_html)

            st.divider()

            # ====== Row 8: 滿版圖表 ======
            render_html(f"<h3 style='color:#1a252f; font-weight:800;'><i class='fas fa-chart-area'></i> 主力籌碼堆疊與 ATR 追蹤圖 - {stock_name}</h3>")

            df_plot = data['df'].tail(120).copy()
            df_plot.index = df_plot.index.strftime('%y/%m/%d')

            fig1 = go.Figure()
            fig1.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name='K線'))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ATR_Stop'], name='ATR 動態防守線', line=dict(color='#dc3545', width=2, dash='dot')))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=[data['poc_price']] * len(df_plot), name='VPVR 籌碼控制點 (POC)', line=dict(color='#6f42c1', width=3)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA5'], name='5MA', line=dict(color='#fcd456', width=1.5)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA20'], name='20MA', line=dict(color='#212529', width=1.5)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BBU'], name='布林上軌', line=dict(color='#0d6efd', width=1)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BBL'], name='布林下軌', line=dict(color='#0d6efd', width=1), fill='tonexty', fillcolor='rgba(13, 110, 253, 0.05)'))

            fig1.update_layout(
                height=550, margin=dict(l=10, r=10, t=30, b=50), template="plotly_white", hovermode="x unified",
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig1, width="stretch")

            st.divider()

            # ====== Row 9: 120 日歷史動態回測表 ======
            col_t1, col_t2 = st.columns([8, 2])
            with col_t1:
                render_html(f"<h3 style='color:#1a252f; font-weight:800;'><i class='fas fa-table'></i> {stock_name} ({clean_ticker}) 近期 120 日交易數據回測</h3>")

            df_hist = data['df'].tail(121).copy()
            csv_rows = ["日期,收盤,漲跌,漲跌幅(%),成交量(張),MA5,MA20,VPVR_POC,ATR防守價,RSI(14),MFI(14),AB驗證,型態"]
            rows_html = []

            for i in range(len(df_hist) - 1, 0, -1):
                row = df_hist.iloc[i]
                prev = df_hist.iloc[i - 1]
                date_str = df_hist.index[i].strftime('%y/%m/%d')

                c_color = "text-danger" if row['Pct_Change'] > 0 else ("text-success" if row['Pct_Change'] < 0 else "")
                change_str = f"{row['Close'] - prev['Close']:+.1f} ({row['Pct_Change']:+.2f}%)"
                
                vol_str = f"{int(row['Volume'] / 1000):,}"

                ab_v = compute_hist_ab_verify(row, prev, data['poc_price'])
                pat = compute_hist_pattern(row)

                if "黃金坑" in ab_v or "洗盤" in ab_v or "超賣" in ab_v:
                    ab_html = f"<span class='badge-hist' style='background-color:#fff3cd; color:#856404; font-weight:bold; border: 1px solid #ffeeba;'>{ab_v}</span>"
                elif "突破" in ab_v or "雙多頭" in ab_v:
                    ab_html = f"<span class='badge-hist' style='background-color:#cfe2ff; color:#084298; font-weight:bold; border: 1px solid #b6d4fe;'>{ab_v}</span>"
                elif "竭盡" in ab_v or "壓力" in ab_v or "誘多" in ab_v:
                    ab_html = f"<span class='badge-hist' style='background-color:#f8d7da; color:#842029; font-weight:bold; border: 1px solid #f5c2c7;'><i class='fas fa-exclamation-triangle'></i> {ab_v}</span>"
                else:
                    ab_html = f"<span class='badge-hist' style='background-color:#f8f9fa; color:#6c757d; border: 1px solid #dee2e6;'>{ab_v}</span>"

                tr_content = f'<tr><td class="fw-bold">{date_str}</td><td class="{c_color} fw-bold">{row["Close"]:.2f}</td><td class="{c_color}">{change_str}</td><td>{vol_str}</td><td>{row["MA5"]:.2f}</td><td>{row["MA20"]:.2f}</td><td style="color:#6f42c1; font-weight:bold;">{data["poc_price"]:.2f}</td><td style="color:#dc3545; font-weight:bold;">{row["ATR_Stop"]:.2f}</td><td>{row["RSI"]:.1f}</td><td>{row["MFI"]:.1f}</td><td>{ab_html}</td><td><small class="text-muted">{pat}</small></td></tr>'
                rows_html.append(tr_content)

                csv_ab = ab_v.replace('⚠️ ', '').replace('🔥 ', '').replace('🧲 ', '').replace('💎 ', '').replace('📉 ', '').replace('☠️ ', '')
                csv_pat = pat.replace('📈 ', '').replace('📉 ', '').replace('🔄 ', '')
                csv_rows.append(f"{date_str},{row['Close']:.2f},{row['Close'] - prev['Close']:.1f},{row['Pct_Change']:.2f}%,{int(row['Volume'] / 1000)},{row['MA5']:.2f},{row['MA20']:.2f},{data['poc_price']:.2f},{row['ATR_Stop']:.2f},{row['RSI']:.1f},{row['MFI']:.1f},{csv_ab},{csv_pat}")

            csv_text = "\n".join(csv_rows)
            csv_bytes = ("\uFEFF" + csv_text).encode('utf-8')

            with col_t2:
                st.download_button(label="📥 下載 CSV 數據", data=csv_bytes, file_name=f"{stock_name}_{clean_ticker}_V8.10_Analysis.csv", mime="text/csv", width="stretch")

            hist_html = "".join(rows_html)
            table_wrapper = f"""
            <div style="max-height: 600px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); width: 100%;">
                <table class="table table-hover table-striped mb-0 hist-table" style="width: 100%;">
                    <thead>
                        <tr><th>日期</th><th>收盤</th><th>漲跌</th><th>量(張)</th><th>MA5</th><th>MA20</th><th style="color: #ff91c4;">VPVR(POC)</th><th style="color: #ff91c4;">ATR防守</th><th>RSI(14)</th><th>MFI(14)</th><th>AB驗證</th><th>型態</th></tr>
                    </thead>
                    <tbody>{hist_html}</tbody>
                </table>
            </div>
            """
            render_html(table_wrapper)
