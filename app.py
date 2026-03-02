# ==========================================
# UI 介面繪製
# ==========================================
st.title("🏦 全方位個股掃描系統 V8.6 (QuantSight)")
st.markdown("<div class='disclaimer'>本程式僅供個人及親友交流使用，不涉及商業用途。使用者須自行承擔使用過程中之風險，開發者不對任何直接或間接損害、法律責任或爭議負責。</div>", unsafe_allow_html=True)

# ====== Row 1: 搜尋列 ======
col1, col2 = st.columns([1, 3])
with col1:
    ticker_input = st.text_input("股票代號 (如 2330)", "") # 預設改為空值
    run_btn = st.button("🚀 啟動EchoScan運算", width="stretch")

if run_btn and ticker_input: # 確保有輸入才執行
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
            
            st.markdown(f"""
<div style="display:flex; background:#fff; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,0.05); border:1px solid #e9ecef; margin-top:10px; margin-bottom:25px;">
<div style="flex:1; border-right:1px solid #e9ecef; padding-right:20px;">
<div style="color:#6c757d; font-weight:bold; font-size:0.95rem; margin-bottom:5px;">📊 Alpha 最新報價與盤中基準</div>
<div style="font-size:2.8rem; font-weight:900; color:{pct_color};">{latest['Close']:.2f} <span style="font-size:1.4rem;">({sign}{latest['Pct_Change']:.2f}%)</span></div>
<div style="margin-top:12px; font-size:1.1rem; color:#495057; font-weight:600;">
<span style="margin-right:20px;">盤中均價 (VWAP): <span class="vwap-highlight">{latest['TP']:.2f}</span></span>
<span>5日線 (短防): <b style="color:#1a252f;">{latest['MA5']:.2f}</b></span>
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
""", unsafe_allow_html=True)

            if data['atm_risk'] and data['f_buy'] < 0:
                st.markdown(f"""
<div class="atm-alert">
<i class="fas fa-money-bill-wave"></i> 🚨 提款機防禦觸發：昨夜美股費半大跌，且外資今日反向倒貨 {abs(data['f_buy']):.0f} 張！標準的「趁利多拉高結帳」，嚴防開高走低！
</div>
""", unsafe_allow_html=True)

            # ====== Row 3: 大一統指令 + 雷達與Macro ======
            sys_status, verdict_title, coach_msg, verdict_color, radar_macro_html = get_unified_command(data, data['macro_msg'])

            st.markdown(f"""
<div style="background-color: #fff; border-left: 8px solid {verdict_color}; padding: 25px 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 8px 16px rgba(0,0,0,0.06); border: 1px solid #f1f3f5;">
<h3 style="color: #1a252f; font-weight: 900; margin-bottom: 18px; letter-spacing: 1px;"><i class="fas fa-user-tie"></i> 操盤手大一統指令 ({stock_name} {clean_ticker})：<span style="color: {verdict_color};">{verdict_title}</span></h3>
<div style="font-size: 1.1rem; color: #495057; margin-bottom: 12px;"><i class="fas fa-robot"></i> <b>系統判定：</b>{sys_status}</div>
<div style="font-size: 1.15rem; font-weight: bold; color: #212529; line-height: 1.6; background-color: rgba(0,0,0,0.02); padding: 15px; border-radius: 8px; margin-top:15px;"><i class="fas fa-bullseye" style="color: #dc3545;"></i> <b>戰略指導：</b>{coach_msg}</div>
{radar_macro_html}
</div>
""", unsafe_allow_html=True)

            # ====== Row 4: 系統綜合評分 ======
            total = data['total_score']
            score_color = "#198754" if total >= 70 else ("#fd7e14" if total >= 45 else "#dc3545")
            st.markdown(f"""
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
""", unsafe_allow_html=True)

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
                
                st.markdown(f"""
<div class="pro-card card-rs">
<div class="pro-title">🥇 RS 相對大盤強弱</div>
<div style="display:flex; justify-content:space-between; align-items:baseline;">
<div class="pro-label">近 60 日 vs 台灣加權</div>
<div style="font-size: 1.8rem; font-weight: 900; color: {rs_color};">{'+' if rs>0 else ''}{rs:.1f}%</div>
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
""", unsafe_allow_html=True)

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
                st.markdown(f"""
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
""", unsafe_allow_html=True)

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

                st.markdown(f"""
<div class="pro-card card-atr">
<div class="pro-title">🛡️ ATR 動態追蹤停損</div>
<div style="display:flex; justify-content:space-between; align-items:baseline;">
<div>
<div class="pro-label" style="margin-top:0;">機構級防守線</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #dc3545;">{atr_stop:.2f}</div>
</div>
<div style="text-align:right;">
<div class="pro-label" style="margin-top:0;">安全緩衝距離</div>
<div style="font-size: 1.3rem; font-weight: 900; color:{atr_color};">{'+' if atr_dist_pct>0 else ''}{atr_dist_pct:.1f}%</div>
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
""", unsafe_allow_html=True)

            # ====== Row 6: 籌碼、動能、邏輯 ======
            st.write("")
            c4, c5, c6 = st.columns(3)
            with c4:
                if not data['chip_ok']:
                    st.markdown("""
<div class="pro-card card-flow">
<div class="pro-title">💰 Flow 法人真金白銀</div>
<div style="margin-top: 20px; padding: 15px; background-color: #f8d7da; color: #842029; border-radius: 8px; font-weight: bold; text-align:center;">
<i class="fas fa-exclamation-triangle"></i> 無法獲取籌碼資料
</div>
</div>
""", unsafe_allow_html=True)
                else:
                    f_act = f"連買 {data['f_days']} 天" if data['f_days'] > 0 else (f"連賣 {abs(data['f_days'])} 天" if data['f_days'] < 0 else "無動靜")
                    t_act = f"連買 {data['t_days']} 天" if data['t_days'] > 0 else (f"連賣 {abs(data['t_days'])} 天" if data['t_days'] < 0 else "無動靜")
                    f_buy, t_buy = data['f_buy'], data['t_buy']
                    if f_buy < 0 and t_buy > 0: health_msg = "🛡️ 內資護盤 (良性換手)"
                    elif f_buy > 0 and t_buy > 0: health_msg = "🔥 土洋齊買 (強勢集中)"
                    elif f_buy < 0 and t_buy < 0: health_msg = "☠️ 土洋齊賣 (失血警戒)"
                    else: health_msg = "⚖️ 法人分歧 (震盪沉澱)"

                    st.markdown(f"""
<div class="pro-card card-flow">
<div class="pro-title">💰 Flow 法人真金白銀</div>
<div style="display:flex; justify-content:space-between; margin-bottom:20px;">
<div><div class="pro-label">外資動向</div><div class="pro-text" style="color:{'#dc3545' if f_buy>0 else '#198754'};">今日 {f_buy:.0f} 張 | {f_act}</div></div>
<div><div class="pro-label">投信動向</div><div class="pro-text" style="color:{'#dc3545' if t_buy>0 else '#198754'};">今日 {t_buy:.0f} 張 | {t_act}</div></div>
</div>
<div style="padding: 12px; background-color: #fff3cd; color: #856404; border-radius: 8px; font-size: 0.95rem; font-weight: bold; line-height: 1.5; text-align:center;">
健康度: {health_msg}
</div>
</div>
""", unsafe_allow_html=True)

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
                
                st.markdown(f"""
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
""", unsafe_allow_html=True)

            with c6:
                cross_alert = ""
                if data['scenario'] == "holy_grail" and data['rs_outperform'] < 0:
                    cross_alert = f"<div style='margin-top: 10px; padding: 8px; background-color: #fff3cd; border-left: 4px solid #fd7e14; border-radius: 4px; font-size: 0.85rem; color: #856404; font-weight:bold;'>⚠️ 跨模組警示：本檔觸發聖杯，但 RS 落後大盤，屬【資金輪動補漲】，爆發力恐不如主流股！</div>"
                    
                st.markdown(f"""
<div class="pro-card card-logic">
<div class="pro-title">💡 邏輯防呆與交叉驗證</div>
<div style="margin-bottom:8px;"><span class="pro-label">均線評級:</span> <span style="color: {'#d4af37' if data['a_rank'] == 'S+' else '#212529'}; font-weight:900; font-size:1.05rem;">[{data['a_rank']}]</span> <span class="pro-text" style="font-size:0.9rem;">{data['a_desc']}</span></div>
<div style="margin-bottom:12px;"><span class="pro-label">動能評級:</span> <span style="color: {'#d4af37' if data['b_rank'] in ['S+','B-'] else '#212529'}; font-weight:900; font-size:1.05rem;">[{data['b_rank']}]</span> <span class="pro-text" style="font-size:0.9rem;">{data['b_desc']}</span></div>
<div style="padding: 10px; background-color: rgba(111, 66, 193, 0.05); border-left: 4px solid #6f42c1; border-radius: 6px; font-size: 0.9rem; line-height: 1.5;">
<b style="color:#6f42c1;">綜合判定: {data['logic_title']}</b><br><span style="color:#495057;">{data['logic_msg']}</span>
</div>
{cross_alert}
</div>
""", unsafe_allow_html=True)

            st.divider()

            # ====== Row 7: Live T+1 與 裸K診斷 ======
            col_t3_left, col_t3_right = st.columns([5, 4])

            with col_t3_left:
                obs, act = generate_execution_script(data)
                st.markdown(f"""
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
""", unsafe_allow_html=True)

            with col_t3_right:
                pa = data['pa_flags']
                bull_power = (15 if pa["pa7_three_soldiers"] else 0) + (20 if pa["pa9_bull_pinbar"] else 0) + (25 if pa["pa10_bull_engulfing"] else 0)
                bear_power = (10 if pa["pa1_no_limit"] else 0) + (25 if pa["pa2_gap_down"] else 0) + (15 if pa["pa3_engulf"] else 0) + (15 if pa["pa4_stagnant"] else 0) + (20 if pa["pa5_trap"] else 0) + (25 if pa["pa6_ma_break"] else 0) + (25 if pa["pa8_three_crows"] else 0)
                total_power = bull_power + bear_power
                bull_pct = (bull_power / total_power * 100) if total_power > 0 else 50
                bear_pct = (bear_power / total_power * 100) if total_power > 0 else 50

                pa_html = f"""
<div class='pro-card card-pa'>
<div class='pro-title'>🕯️ 裸 K 價格行為 (V8.6 語義學診斷)</div>
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
                st.markdown(pa_html, unsafe_allow_html=True)

            st.divider()

            # ====== Row 8: 滿版圖表 ======
            st.markdown(f"<h3 style='color:#1a252f; font-weight:800;'><i class='fas fa-chart-area'></i> 主力籌碼堆疊與 ATR 追蹤圖 - {stock_name}</h3>", unsafe_allow_html=True)

            df_plot = data['df'].tail(120).copy()
            df_plot.index = df_plot.index.strftime('%y/%m/%d')

            fig1 = go.Figure()
            fig1.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name='K線'))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['ATR_Stop'], name='ATR 動態防守線', line=dict(color='#dc3545', width=2, dash='dot')))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=[data['poc_price']]*len(df_plot), name='VPVR 籌碼控制點 (POC)', line=dict(color='#6f42c1', width=3)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA5'], name='5MA', line=dict(color='#fcd456', width=1.5)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA20'], name='20MA', line=dict(color='#212529', width=1.5)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BBU'], name='布林上軌', line=dict(color='#0d6efd', width=1)))
            fig1.add_trace(go.Scatter(x=df_plot.index, y=df_plot['BBL'], name='布林下軌', line=dict(color='#0d6efd', width=1), fill='tonexty', fillcolor='rgba(13, 110, 253, 0.05)'))

            fig1.update_layout(
                height=550, margin=dict(l=10, r=10, t=30, b=50), template="plotly_white", hovermode="x unified",
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig1, width="stretch")

            st.divider()
            
            # ====== Row 9: 120 日歷史動態回測表 ======
            col_t1, col_t2 = st.columns([8, 2])
            with col_t1:
                st.markdown(f"<h3 style='color:#1a252f; font-weight:800;'><i class='fas fa-table'></i> {stock_name} ({clean_ticker}) 近期 120 日交易數據回測</h3>", unsafe_allow_html=True)

            df_hist = data['df'].tail(121).copy()
            csv_rows = ["日期,收盤,漲跌,漲跌幅(%),成交量(張),MA5,MA20,VPVR_POC,ATR防守價,RSI(14),MFI(14),AB驗證,型態"]
            rows_html = []

            for i in range(len(df_hist) - 1, 0, -1):
                row = df_hist.iloc[i]
                prev = df_hist.iloc[i - 1]
                date_str = df_hist.index[i].strftime('%y/%m/%d')

                c_color = "text-danger" if row['Pct_Change'] > 0 else ("text-success" if row['Pct_Change'] < 0 else "")
                change_str = f"{row['Close'] - prev['Close']:+.1f} ({row['Pct_Change']:+.2f}%)"
                vol_str = f"{int(row['Volume'] / 1000)}k"

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
                st.download_button(label="📥 下載 CSV 數據", data=csv_bytes, file_name=f"{stock_name}_{clean_ticker}_V8.6_Analysis.csv", mime="text/csv", width="stretch")

            hist_html = "".join(rows_html)
            table_wrapper = f"""
<div style="max-height: 600px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); width: 100%;">
<table class="table table-hover table-striped mb-0 hist-table" style="width: 100%;">
<thead>
<tr><th>日期</th><th>收盤</th><th>漲跌</th><th>量</th><th>MA5</th><th>MA20</th><th style="color: #ff91c4;">VPVR(POC)</th><th style="color: #ff91c4;">ATR防守</th><th>RSI(14)</th><th>MFI(14)</th><th>AB驗證</th><th>型態</th></tr>
</thead>
<tbody>{hist_html}</tbody>
</table>
</div>
"""
            st.markdown(table_wrapper, unsafe_allow_html=True)
