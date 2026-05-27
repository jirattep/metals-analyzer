"""
SCALP ANALYZER - Pure Price Action Edition
============================================
XAU/USD และ XAG/USD Scalping Analyzer (5-15 นาที/ไม้)

หลักการ:
- กราฟล้วน 100% — ไม่ใช้ข่าว, ไม่ใช้ sentiment
- เน้น M1/M5/M15 (scalping timeframes)
- Time-to-Target — ประเมินว่าราคาถึง TP ใน 15 นาทีไหม
- Pullback entry — เข้าตอนราคาย่อ ไม่ไล่ราคา
- EMA Ribbon + VWAP + Micro structure

Install:
    pip install streamlit yfinance pandas numpy plotly

Run:
    streamlit run scalp_analyzer.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, timezone
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Scalp Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# INSTRUMENT CONFIGS
# ============================================================
INSTRUMENTS = {
    "XAUUSD": {
        "name": "GOLD", "symbol": "XAU/USD", "yf_symbol": "GC=F",
        "ounces_per_lot": 100, "typical_spread": 0.20,
        "color_primary": "#f4c542", "color_secondary": "#a87f2c",
        "emoji": "🥇",
    },
    "XAGUSD": {
        "name": "SILVER", "symbol": "XAG/USD", "yf_symbol": "SI=F",
        "ounces_per_lot": 5000, "typical_spread": 0.025,
        "color_primary": "#d8dde6", "color_secondary": "#8b95a3",
        "emoji": "🥈",
    },
}


# ============================================================
# CSS
# ============================================================
def inject_css(instrument_key):
    cfg = INSTRUMENTS[instrument_key]
    color = cfg["color_primary"]
    color_dark = cfg["color_secondary"]

    if instrument_key == "XAUUSD":
        bg = "#100c06"
        bg2 = "#1c1610"
        border = "#4a3a1f"
        text = "#f7ecd9"
        muted = "#9c8560"
        glow_rgb = "244, 197, 66"
        accent_soft = "#3d2f15"
    else:
        bg = "#0c0e12"
        bg2 = "#161a21"
        border = "#2e343f"
        text = "#eef1f5"
        muted = "#8b95a3"
        glow_rgb = "216, 221, 230"
        accent_soft = "#22272f"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@600;700;800&family=Orbitron:wght@700;900&display=swap');

        /* ===== BACKGROUND ===== */
        .stApp {{
            background:
                radial-gradient(ellipse 80% 50% at 50% -10%, rgba({glow_rgb}, 0.12) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 100% 100%, rgba({glow_rgb}, 0.06) 0%, transparent 50%),
                linear-gradient(180deg, {bg} 0%, #000 100%);
        }}
        html, body, [class*="css"] {{
            font-family: 'JetBrains Mono', monospace !important;
            color: {text};
        }}
        h1, h2, h3 {{ font-family: 'Syne', sans-serif !important; color: {color} !important; }}

        /* ===== HIDE STREAMLIT BRANDING ===== */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        /* ===== BUTTON ===== */
        .stButton > button {{
            background: linear-gradient(135deg, {color} 0%, {color_dark} 100%);
            color: #0a0a0a; border: none; padding: 16px 24px;
            font-family: 'Syne', sans-serif; font-weight: 800;
            font-size: 15px; letter-spacing: 0.25em; text-transform: uppercase;
            border-radius: 3px;
            box-shadow: 0 4px 24px rgba({glow_rgb}, 0.35),
                        inset 0 1px 0 rgba(255,255,255,0.4);
            width: 100%; transition: all 0.25s ease;
        }}
        .stButton > button:hover {{
            box-shadow: 0 6px 36px rgba({glow_rgb}, 0.55),
                        inset 0 1px 0 rgba(255,255,255,0.5);
            transform: translateY(-2px);
        }}
        .stButton > button:active {{ transform: translateY(0); }}

        /* ===== TITLE ===== */
        .main-title {{
            font-family: 'Orbitron', sans-serif !important;
            font-size: 54px !important; font-weight: 900 !important;
            margin: 0 !important; line-height: 1 !important;
            letter-spacing: 0.03em;
            background: linear-gradient(135deg,
                #ffffff 0%, {color} 35%, {color_dark} 70%, {color} 100%);
            background-size: 200% auto;
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 2px 12px rgba({glow_rgb}, 0.4));
            animation: shine 6s linear infinite;
        }}
        @keyframes shine {{
            0%{{background-position:0% center}}
            100%{{background-position:200% center}}
        }}

        /* ===== VERDICT ===== */
        .verdict-buy {{
            font-family: 'Orbitron', sans-serif; font-size: 60px; font-weight: 900;
            color: {color}; text-shadow: 0 0 40px rgba({glow_rgb}, 0.8); margin: 0;
            letter-spacing: 0.02em;
        }}
        .verdict-sell {{
            font-family: 'Orbitron', sans-serif; font-size: 60px; font-weight: 900;
            color: #ff4d6d; text-shadow: 0 0 40px rgba(255,77,109,0.8); margin: 0;
            letter-spacing: 0.02em;
        }}
        .verdict-none {{
            font-family: 'Orbitron', sans-serif; font-size: 52px; font-weight: 900;
            color: {muted}; margin: 0; letter-spacing: 0.02em;
        }}

        /* ===== SECTION HEADER ===== */
        .section-header {{
            font-size: 11px; letter-spacing: 0.3em; color: {color};
            text-transform: uppercase; margin: 24px 0 14px 0;
            padding-bottom: 10px; font-weight: 700;
            border-bottom: 1px solid {border};
            position: relative;
        }}
        .section-header::after {{
            content: ''; position: absolute; bottom: -1px; left: 0;
            width: 60px; height: 2px;
            background: {color}; box-shadow: 0 0 8px {color};
        }}

        /* ===== METRIC CARDS ===== */
        [data-testid="stMetric"] {{
            background: linear-gradient(145deg, {bg2} 0%, {bg} 100%);
            border: 1px solid {border};
            border-radius: 4px; padding: 16px 18px;
            transition: all 0.2s ease;
        }}
        [data-testid="stMetric"]:hover {{
            border-color: {color};
            box-shadow: 0 0 20px rgba({glow_rgb}, 0.15);
        }}
        [data-testid="stMetricLabel"] {{
            font-size: 10px !important; letter-spacing: 0.15em;
            color: {muted} !important; text-transform: uppercase;
        }}
        [data-testid="stMetricValue"] {{
            font-family: 'Syne', sans-serif !important;
            font-size: 24px !important; font-weight: 800 !important;
            color: {text} !important;
        }}

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {bg2} 0%, {bg} 100%);
            border-right: 1px solid {border};
        }}
        [data-testid="stSidebar"] h3 {{
            font-size: 13px !important; letter-spacing: 0.2em;
            color: {color} !important;
        }}

        /* ===== INPUTS ===== */
        [data-testid="stNumberInput"] input,
        [data-testid="stSelectbox"] > div > div {{
            background: {bg} !important;
            border: 1px solid {border} !important;
            color: {color} !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 700 !important;
        }}

        /* ===== EXPANDER ===== */
        [data-testid="stExpander"] {{
            border: 1px solid {border} !important;
            border-radius: 4px;
            background: {bg2};
        }}

        /* ===== PROGRESS BAR ===== */
        [data-testid="stProgress"] > div > div > div {{
            background: linear-gradient(90deg, {color_dark}, {color}) !important;
        }}

        /* ===== ALERTS ===== */
        [data-testid="stAlert"] {{
            border-radius: 4px;
            border-left: 3px solid {color};
        }}

        /* ===== ANIMATIONS ===== */
        .live-dot {{
            display: inline-block; width: 9px; height: 9px; border-radius: 50%;
            background: {color}; box-shadow: 0 0 12px {color}, 0 0 4px #fff;
            animation: pulse 1.8s ease-in-out infinite; margin-right: 8px;
        }}
        @keyframes pulse {{
            0%,100%{{opacity:1; transform:scale(1)}}
            50%{{opacity:0.4; transform:scale(0.85)}}
        }}
        @keyframes shimmer {{
            0%{{background-position:-200% 0}}
            100%{{background-position:200% 0}}
        }}
        @keyframes fadeIn {{
            from{{opacity:0; transform:translateY(8px)}}
            to{{opacity:1; transform:translateY(0)}}
        }}

        /* ===== CARD COMPONENTS ===== */
        .hero-card {{
            border: 1px solid {border};
            border-radius: 6px;
            padding: 28px 32px;
            position: relative;
            overflow: hidden;
            animation: fadeIn 0.4s ease;
        }}
        .hero-card::before {{
            content: ''; position: absolute; top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, {color}, transparent);
            background-size: 200% 100%;
            animation: shimmer 3s linear infinite;
        }}
        .badge {{
            display: inline-block; padding: 5px 12px;
            font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
            border: 1px solid {border}; border-radius: 3px;
            color: {muted}; background: {bg};
        }}
        .badge-live {{
            color: {color}; border-color: {color};
            background: rgba({glow_rgb}, 0.08);
        }}
        .tag-row {{
            font-size: 11px; letter-spacing: 0.12em; color: {muted};
            display: flex; gap: 18px; flex-wrap: wrap;
        }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# INDICATORS
# ============================================================
def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(series, fast)
    ema_slow = calc_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line


def calc_atr(df, period=14):
    high, low, close = df['High'], df['Low'], df['Close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(),
                    (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calc_vwap(df):
    """Volume Weighted Average Price — reset รายวัน"""
    typical = (df['High'] + df['Low'] + df['Close']) / 3
    if 'Volume' in df.columns and df['Volume'].sum() > 0:
        vol = df['Volume']
    else:
        vol = pd.Series(1, index=df.index)  # ถ้าไม่มี volume ใช้ 1
    # Reset daily
    dates = df.index.date if df.index.tz is None else df.index.tz_convert('UTC').date
    df_temp = pd.DataFrame({'tp': typical, 'vol': vol, 'date': dates})
    df_temp['tpv'] = df_temp['tp'] * df_temp['vol']
    cum_tpv = df_temp.groupby('date')['tpv'].cumsum()
    cum_vol = df_temp.groupby('date')['vol'].cumsum()
    return cum_tpv / cum_vol.replace(0, np.nan)


def find_swings(df, lookback=5):
    """หา swing high/low — แท่งที่สูง/ต่ำกว่าข้างเคียง lookback แท่ง"""
    highs = df['High'].values
    lows = df['Low'].values
    swing_highs = []
    swing_lows = []
    for i in range(lookback, len(df) - lookback):
        is_high = all(highs[i] >= highs[i - j] for j in range(1, lookback + 1)) and \
                  all(highs[i] >= highs[i + j] for j in range(1, lookback + 1))
        is_low = all(lows[i] <= lows[i - j] for j in range(1, lookback + 1)) and \
                 all(lows[i] <= lows[i + j] for j in range(1, lookback + 1))
        if is_high:
            swing_highs.append((i, highs[i]))
        if is_low:
            swing_lows.append((i, lows[i]))
    return swing_highs, swing_lows


def market_structure(df, lookback=5):
    """วิเคราะห์ market structure จาก swing points"""
    sh, sl = find_swings(df, lookback)
    if len(sh) < 2 or len(sl) < 2:
        return "UNCLEAR", None, None

    last_highs = [v for _, v in sh[-2:]]
    last_lows = [v for _, v in sl[-2:]]

    higher_high = last_highs[-1] > last_highs[-2]
    higher_low = last_lows[-1] > last_lows[-2]
    lower_high = last_highs[-1] < last_highs[-2]
    lower_low = last_lows[-1] < last_lows[-2]

    if higher_high and higher_low:
        structure = "UPTREND"      # HH + HL
    elif lower_high and lower_low:
        structure = "DOWNTREND"    # LH + LL
    else:
        structure = "RANGE"

    nearest_resistance = sh[-1][1] if sh else None
    nearest_support = sl[-1][1] if sl else None
    return structure, nearest_resistance, nearest_support


# ============================================================
# DATA FETCHING
# ============================================================
def _download_retry(symbol, interval, period, retries=3):
    """ดาวน์โหลดพร้อม retry"""
    import time
    for attempt in range(retries):
        try:
            df = yf.download(symbol, interval=interval, period=period,
                             progress=False, auto_adjust=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df is not None and len(df) > 5:
                return df
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(1.5)
    return None


def _resample(df, rule):
    """แปลง timeframe เช่น M5 -> M15"""
    if df is None or len(df) == 0:
        return None
    agg = {'Open': 'first', 'High': 'max', 'Low': 'min',
           'Close': 'last', 'Volume': 'sum'}
    cols = {k: v for k, v in agg.items() if k in df.columns}
    out = df.resample(rule).agg(cols).dropna()
    return out


@st.cache_data(ttl=60, show_spinner=False)
def fetch_scalp_data(yf_symbol):
    """ดึงข้อมูล M1, M5, M15 — มี fallback หลายชั้น"""
    # M5 เป็นแกนหลัก (เสถียรสุด)
    m5 = _download_retry(yf_symbol, "5m", "5d")
    if m5 is None or len(m5) < 30:
        return None, None, None

    # M1 — ลองดึง ถ้าไม่ได้ใช้ M5 แทน (จะแม่นน้อยลงนิด)
    m1 = _download_retry(yf_symbol, "1m", "1d", retries=2)
    if m1 is None or len(m1) < 30:
        m1 = m5  # fallback: ใช้ M5 เป็น M1

    # M15 — ลองดึง ถ้าไม่ได้ resample จาก M5
    m15 = _download_retry(yf_symbol, "15m", "5d", retries=2)
    if m15 is None or len(m15) < 30:
        m15_resampled = _resample(m5, '15min')
        if m15_resampled is not None and len(m15_resampled) >= 30:
            m15 = m15_resampled
        else:
            m15 = m5  # fallback สุดท้าย

    return m1, m5, m15


# ============================================================
# SCALP ANALYSIS
# ============================================================
def analyze_scalp(m1, m5, m15, cfg, settings):
    result = {}

    # ===== ราคาปัจจุบัน =====
    current = float(m5['Close'].iloc[-1])
    result['current_price'] = current

    # ===== EMA RIBBON (8/13/21) บน M5 =====
    m5_close = m5['Close']
    ema8 = calc_ema(m5_close, 8)
    ema13 = calc_ema(m5_close, 13)
    ema21 = calc_ema(m5_close, 21)

    e8 = float(ema8.iloc[-1])
    e13 = float(ema13.iloc[-1])
    e21 = float(ema21.iloc[-1])

    # Ribbon เรียงตัว: 8>13>21 = bull, 8<13<21 = bear
    if e8 > e13 > e21:
        ribbon = "BULL"
    elif e8 < e13 < e21:
        ribbon = "BEAR"
    else:
        ribbon = "MIXED"
    result['ribbon'] = ribbon
    result['ema8'] = e8
    result['ema13'] = e13
    result['ema21'] = e21

    # ===== M15 trend (เทรนด์อ้างอิง) =====
    m15_close = m15['Close']
    ema21_m15 = calc_ema(m15_close, 21)
    ema50_m15 = calc_ema(m15_close, 50)
    m15_price = float(m15_close.iloc[-1])
    m15_e21 = float(ema21_m15.iloc[-1])
    m15_e50 = float(ema50_m15.iloc[-1])
    m15_slope = float(ema21_m15.iloc[-1] - ema21_m15.iloc[-5]) if len(ema21_m15) >= 5 else 0

    if m15_price > m15_e21 > m15_e50 and m15_slope > 0:
        m15_trend = "UP"
    elif m15_price < m15_e21 < m15_e50 and m15_slope < 0:
        m15_trend = "DOWN"
    else:
        m15_trend = "SIDEWAYS"
    result['m15_trend'] = m15_trend

    # ===== Market Structure (M5) =====
    structure, resistance, support = market_structure(m5, lookback=4)
    result['structure'] = structure
    result['resistance'] = resistance
    result['support'] = support

    # ===== M1 momentum (จังหวะเข้า) =====
    m1_close = m1['Close']
    ema8_m1 = calc_ema(m1_close, 8)
    m1_last = float(m1_close.iloc[-1])
    m1_prev = float(m1_close.iloc[-2])
    m1_e8 = float(ema8_m1.iloc[-1])
    m1_e8_prev = float(ema8_m1.iloc[-2])

    # M1 cross
    if m1_prev <= m1_e8_prev and m1_last > m1_e8:
        m1_signal = "BULL_CROSS"
    elif m1_prev >= m1_e8_prev and m1_last < m1_e8:
        m1_signal = "BEAR_CROSS"
    elif m1_last > m1_e8:
        m1_signal = "ABOVE_EMA"
    else:
        m1_signal = "BELOW_EMA"
    result['m1_signal'] = m1_signal

    # ===== RSI (M5) =====
    rsi_m5 = calc_rsi(m5_close, 14)
    last_rsi = float(rsi_m5.iloc[-1])
    result['rsi_m5'] = last_rsi

    # ===== MACD (M5) =====
    macd_line, macd_sig, macd_hist = calc_macd(m5_close)
    last_hist = float(macd_hist.iloc[-1])
    prev_hist = float(macd_hist.iloc[-2])
    result['macd_hist'] = last_hist
    macd_rising = last_hist > prev_hist
    result['macd_rising'] = macd_rising

    # ===== VWAP (M5) =====
    try:
        vwap = calc_vwap(m5)
        last_vwap = float(vwap.iloc[-1])
        result['vwap'] = last_vwap
        result['above_vwap'] = current > last_vwap
    except Exception:
        result['vwap'] = current
        result['above_vwap'] = True

    # ===== ATR & Velocity =====
    atr_m1 = calc_atr(m1, 14)
    atr_m5 = calc_atr(m5, 14)
    last_atr_m1 = float(atr_m1.iloc[-1]) if not pd.isna(atr_m1.iloc[-1]) else cfg['typical_spread'] * 2
    last_atr_m5 = float(atr_m5.iloc[-1]) if not pd.isna(atr_m5.iloc[-1]) else cfg['typical_spread'] * 4
    result['atr_m1'] = last_atr_m1
    result['atr_m5'] = last_atr_m5

    # ===== TP/SL distance =====
    usd_per_move = settings['lot_size'] * settings['ounces_per_lot']
    tp_distance = settings['tp_usd'] / usd_per_move  # ระยะราคาที่ต้องวิ่ง
    result['tp_distance'] = tp_distance

    # ===== TIME-TO-TARGET (หัวใจของ scalp) =====
    # ราคาวิ่งเฉลี่ย ATR M1 ต่อนาที → ต้องใช้กี่นาทีถึง TP
    # แต่ราคาไม่ได้วิ่งทางเดียว ใช้ factor 0.5 (net movement)
    net_velocity = last_atr_m1 * 0.5  # ระยะ net ต่อ 1 นาที
    minutes_to_tp = tp_distance / net_velocity if net_velocity > 0 else 999
    result['minutes_to_tp'] = minutes_to_tp

    # ===== Recent velocity (5 แท่ง M1 ล่าสุด) =====
    recent_m1 = m1_close.tail(6).values
    recent_move = abs(recent_m1[-1] - recent_m1[0])
    recent_velocity = recent_move / 5  # ต่อนาที
    result['recent_velocity'] = recent_velocity

    # ===== Spread check =====
    spread = cfg['typical_spread']
    spread_ratio = spread / tp_distance  # spread กินกี่ % ของ TP
    result['spread_ratio'] = spread_ratio

    # ===== Pullback detection =====
    # ราคาอยู่ใกล้ EMA13 ไหม (โซน entry ที่ดี)
    dist_to_ema13 = abs(current - e13) / current
    is_pullback_zone = dist_to_ema13 < 0.0008  # ภายใน 0.08%
    result['is_pullback_zone'] = is_pullback_zone
    result['dist_to_ema13_pct'] = dist_to_ema13 * 100

    # ============================================================
    # SCORING
    # ============================================================
    direction = None
    if m1_signal in ["BULL_CROSS", "ABOVE_EMA"] and ribbon != "BEAR":
        direction = "BUY"
    elif m1_signal in ["BEAR_CROSS", "BELOW_EMA"] and ribbon != "BULL":
        direction = "SELL"

    score = 0
    score_details = []

    if direction == "BUY":
        # M15 trend alignment
        if m15_trend == "UP":
            score += 20; score_details.append("✓ M15 ขาขึ้น (+20)")
        elif m15_trend == "DOWN":
            score -= 25; score_details.append("✗ M15 ขาลง สวนทาง (-25)")
        else:
            score += 0; score_details.append("− M15 sideways (0)")

        # EMA Ribbon
        if ribbon == "BULL":
            score += 18; score_details.append("✓ EMA Ribbon เรียง bull (+18)")
        elif ribbon == "MIXED":
            score += 0; score_details.append("− Ribbon mixed (0)")

        # Market structure
        if structure == "UPTREND":
            score += 15; score_details.append("✓ Structure HH-HL (+15)")
        elif structure == "DOWNTREND":
            score -= 20; score_details.append("✗ Structure LH-LL สวน (-20)")

        # M1 signal
        if m1_signal == "BULL_CROSS":
            score += 12; score_details.append("✓ M1 ตัด EMA ขึ้น (+12)")
        elif m1_signal == "ABOVE_EMA":
            score += 6; score_details.append("✓ M1 เหนือ EMA (+6)")

        # MACD
        if last_hist > 0 and macd_rising:
            score += 10; score_details.append("✓ MACD บวก+เร่ง (+10)")
        elif last_hist < 0:
            score -= 8; score_details.append("✗ MACD ลบ (-8)")

        # RSI — scalp ต้องไม่ overbought
        if 45 < last_rsi < 68:
            score += 8; score_details.append(f"✓ RSI {last_rsi:.0f} โซนดี (+8)")
        elif last_rsi >= 72:
            score -= 12; score_details.append(f"✗ RSI {last_rsi:.0f} overbought (-12)")
        elif last_rsi <= 35:
            score -= 6; score_details.append(f"− RSI {last_rsi:.0f} อ่อนแอ (-6)")

        # VWAP
        if result['above_vwap']:
            score += 8; score_details.append("✓ เหนือ VWAP (+8)")
        else:
            score -= 6; score_details.append("✗ ใต้ VWAP (-6)")

        # Pullback entry
        if is_pullback_zone:
            score += 10; score_details.append("✓ ราคาย่อแตะ EMA13 — จุดเข้าดี (+10)")

    elif direction == "SELL":
        if m15_trend == "DOWN":
            score += 20; score_details.append("✓ M15 ขาลง (+20)")
        elif m15_trend == "UP":
            score -= 25; score_details.append("✗ M15 ขาขึ้น สวนทาง (-25)")
        else:
            score_details.append("− M15 sideways (0)")

        if ribbon == "BEAR":
            score += 18; score_details.append("✓ EMA Ribbon เรียง bear (+18)")
        elif ribbon == "MIXED":
            score_details.append("− Ribbon mixed (0)")

        if structure == "DOWNTREND":
            score += 15; score_details.append("✓ Structure LH-LL (+15)")
        elif structure == "UPTREND":
            score -= 20; score_details.append("✗ Structure HH-HL สวน (-20)")

        if m1_signal == "BEAR_CROSS":
            score += 12; score_details.append("✓ M1 ตัด EMA ลง (+12)")
        elif m1_signal == "BELOW_EMA":
            score += 6; score_details.append("✓ M1 ใต้ EMA (+6)")

        if last_hist < 0 and not macd_rising:
            score += 10; score_details.append("✓ MACD ลบ+เร่ง (+10)")
        elif last_hist > 0:
            score -= 8; score_details.append("✗ MACD บวก (-8)")

        if 32 < last_rsi < 55:
            score += 8; score_details.append(f"✓ RSI {last_rsi:.0f} โซนดี (+8)")
        elif last_rsi <= 28:
            score -= 12; score_details.append(f"✗ RSI {last_rsi:.0f} oversold (-12)")
        elif last_rsi >= 65:
            score -= 6; score_details.append(f"− RSI {last_rsi:.0f} แข็งเกิน (-6)")

        if not result['above_vwap']:
            score += 8; score_details.append("✓ ใต้ VWAP (+8)")
        else:
            score -= 6; score_details.append("✗ เหนือ VWAP (-6)")

        if is_pullback_zone:
            score += 10; score_details.append("✓ ราคาเด้งแตะ EMA13 — จุดเข้าดี (+10)")

    # ===== Time-to-Target check (สำคัญมากสำหรับ scalp) =====
    if minutes_to_tp <= 15:
        score += 12
        score_details.append(f"✓ คาดถึง TP ใน {minutes_to_tp:.0f} นาที (+12)")
    elif minutes_to_tp <= 25:
        score += 0
        score_details.append(f"− TP ใช้เวลา {minutes_to_tp:.0f} นาที (0)")
    else:
        score -= 15
        score_details.append(f"✗ TP ไกลเกิน — {minutes_to_tp:.0f} นาที (-15)")

    # ===== Spread check =====
    if spread_ratio > 0.25:
        score -= 10
        score_details.append(f"✗ Spread กิน {spread_ratio*100:.0f}% ของ TP (-10)")

    result['direction'] = direction
    result['score'] = score
    result['score_details'] = score_details

    # ===== Probability =====
    prob = 1 / (1 + np.exp(-score / 22))
    prob = max(0.05, min(0.92, prob))
    result['probability'] = prob
    result['ev'] = prob * settings['tp_usd'] - (1 - prob) * settings['sl_usd']

    # ===== Decision =====
    blocks = []
    if not direction:
        blocks.append("ไม่มีทิศทางชัด (M1 + Ribbon ไม่ตรงกัน)")
    if minutes_to_tp > 25:
        blocks.append(f"ราคาวิ่งช้าเกิน — คาดใช้ {minutes_to_tp:.0f} นาทีถึง TP")
    if structure == "RANGE":
        blocks.append("ตลาด sideways (range) — scalp ยาก")
    if spread_ratio > 0.30:
        blocks.append(f"Spread กว้างเกิน — กิน {spread_ratio*100:.0f}% ของกำไร")
    if direction == "BUY" and m15_trend == "DOWN":
        blocks.append("M15 ขาลง — ไม่ควร BUY สวนเทรนด์")
    if direction == "SELL" and m15_trend == "UP":
        blocks.append("M15 ขาขึ้น — ไม่ควร SELL สวนเทรนด์")
    if direction == "BUY" and last_rsi >= 72:
        blocks.append(f"RSI {last_rsi:.0f} overbought — เสี่ยงย่อ")
    if direction == "SELL" and last_rsi <= 28:
        blocks.append(f"RSI {last_rsi:.0f} oversold — เสี่ยงเด้ง")
    if prob < 0.58:
        blocks.append(f"Probability {prob*100:.0f}% ต่ำกว่า 58%")
    if result['ev'] < 0:
        blocks.append("Expected Value ติดลบ")

    if not blocks and direction:
        result['action'] = direction
        result['reasons'] = [
            f"M15 {m15_trend} + Ribbon {ribbon} align",
            f"Structure: {structure}",
            f"M1: {m1_signal}",
            f"คาดถึง TP ใน {minutes_to_tp:.0f} นาที",
            f"Probability {prob*100:.0f}%",
        ]
    else:
        result['action'] = "NO_TRADE"
        result['reasons'] = blocks if blocks else ["ไม่ผ่านเงื่อนไข"]

    # Entry/TP/SL
    result['entry'] = current
    if result['action'] == "BUY":
        result['tp'] = current + tp_distance
        result['sl'] = current - tp_distance
    elif result['action'] == "SELL":
        result['tp'] = current - tp_distance
        result['sl'] = current + tp_distance
    else:
        result['tp'] = None
        result['sl'] = None

    return result


# ============================================================
# CHART
# ============================================================
def make_scalp_chart(m5, cfg, result):
    close = m5['Close']
    ema8 = calc_ema(close, 8)
    ema13 = calc_ema(close, 13)
    ema21 = calc_ema(close, 21)
    rsi = calc_rsi(close, 14)
    vwap = calc_vwap(m5)

    recent = m5.tail(80).copy()
    recent['ema8'] = ema8.tail(80)
    recent['ema13'] = ema13.tail(80)
    recent['ema21'] = ema21.tail(80)
    recent['rsi'] = rsi.tail(80)
    recent['vwap'] = vwap.tail(80)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.72, 0.28], vertical_spacing=0.04,
    )

    # Candles
    fig.add_trace(go.Candlestick(
        x=recent.index, open=recent['Open'], high=recent['High'],
        low=recent['Low'], close=recent['Close'], name="Price",
        increasing_line_color=cfg['color_primary'],
        decreasing_line_color='#ff3b6b',
    ), row=1, col=1)

    # EMA Ribbon
    for col, c, w in [('ema8', '#ffb84d', 1), ('ema13', cfg['color_primary'], 1.5), ('ema21', '#888', 1)]:
        fig.add_trace(go.Scatter(
            x=recent.index, y=recent[col], name=col.upper(),
            line=dict(color=c, width=w),
        ), row=1, col=1)

    # VWAP
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['vwap'], name="VWAP",
        line=dict(color='#58a6ff', width=1.5, dash='dash'),
    ), row=1, col=1)

    # TP/SL
    if result['action'] != 'NO_TRADE':
        fig.add_hline(y=result['tp'], line_dash="dash", line_color=cfg['color_primary'],
                      annotation_text="TP", row=1, col=1)
        fig.add_hline(y=result['sl'], line_dash="dash", line_color="#ff3b6b",
                      annotation_text="SL", row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['rsi'], name="RSI",
        line=dict(color='#bc8cff', width=1.5),
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#ff3b6b", row=2, col=1, opacity=0.4)
    fig.add_hline(y=50, line_dash="dot", line_color="#888", row=2, col=1, opacity=0.3)
    fig.add_hline(y=30, line_dash="dot", line_color=cfg['color_primary'], row=2, col=1, opacity=0.4)

    fig.update_layout(
        height=520, xaxis_rangeslider_visible=False, showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.3)',
        font=dict(family="JetBrains Mono", color="#e6edf3", size=10),
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.update_xaxes(gridcolor='rgba(100,100,100,0.1)')
    fig.update_yaxes(gridcolor='rgba(100,100,100,0.1)')
    return fig


def get_session():
    h = datetime.now(timezone.utc).hour
    s = []
    if h >= 23 or h < 8: s.append("ASIAN")
    if 7 <= h < 16: s.append("LONDON")
    if 12 <= h < 21: s.append("NY")
    overlap = len(s) > 1
    main = s[-1] if s else "QUIET"
    return main + (" OVERLAP" if overlap else "")


# ============================================================
# MAIN
# ============================================================
def main():
    with st.sidebar:
        st.markdown("### ⚙️ CONFIGURATION")
        instrument_key = st.selectbox(
            "INSTRUMENT", options=list(INSTRUMENTS.keys()),
            format_func=lambda k: f"{INSTRUMENTS[k]['emoji']} {INSTRUMENTS[k]['symbol']}",
        )
        cfg = INSTRUMENTS[instrument_key]

        st.markdown("---")
        st.markdown("### 📊 POSITION")
        lot_size = st.number_input("Lot Size", value=0.01, step=0.01, format="%.2f")
        ounces_per_lot = st.number_input("Oz / Lot", value=cfg['ounces_per_lot'], step=10)
        tp_usd = st.number_input("TP (USD)", value=20.0, step=5.0)
        sl_usd = st.number_input("SL (USD)", value=20.0, step=5.0)

        st.markdown("---")
        st.caption(f"💡 1 lot = {ounces_per_lot} oz")
        usd_per_move = lot_size * ounces_per_lot
        if usd_per_move > 0:
            st.caption(f"⚡ TP distance: ${tp_usd/usd_per_move:.3f}/oz")
        st.caption(f"📏 Typical spread: ${cfg['typical_spread']}/oz")
        st.markdown("---")
        st.caption("**SCALP MODE** — กราฟล้วน 100%")
        st.caption("ไม่ใช้ข่าว · เน้น M1/M5/M15")
        st.caption("เป้าหมาย: ไม้ละ 5-15 นาที")

    inject_css(instrument_key)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f'<div style="font-size:11px; letter-spacing:0.3em; margin-bottom:6px;">'
            f'<span class="live-dot"></span>'
            f'<span style="color:{cfg["color_primary"]}; font-weight:700;">SCALP TERMINAL</span>'
            f'<span style="color:#666;"> · PURE PRICE ACTION</span></div>',
            unsafe_allow_html=True)
        st.markdown(f'<h1 class="main-title">{cfg["emoji"]} {cfg["name"]} SCALP</h1>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="tag-row" style="margin-top:8px;">'
            '<span>◆ M1 / M5 / M15</span>'
            '<span>◆ EMA RIBBON</span>'
            '<span>◆ VWAP</span>'
            '<span>◆ STRUCTURE</span>'
            '<span>◆ TIME-TO-TARGET</span></div>',
            unsafe_allow_html=True)
    with col2:
        bkk = datetime.now(timezone(timedelta(hours=7)))
        utc = datetime.now(timezone.utc)
        st.markdown(f"""
        <div style="text-align:right; font-size:11px; margin-top:16px;
                    font-family:'JetBrains Mono',monospace;">
            <div style="color:{cfg['color_primary']}; font-weight:700; font-size:18px;
                        letter-spacing:0.1em;">🇹🇭 {bkk.strftime('%H:%M:%S')}</div>
            <div style="color:#888; margin-top:4px;">UTC · {utc.strftime('%H:%M:%S')}</div>
            <div style="color:#666; margin-top:4px; letter-spacing:0.1em;">
                {get_session()}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<hr style='border-color:rgba(255,255,255,0.06); margin:18px 0;'>",
                unsafe_allow_html=True)

    if not st.button("⚡ SCAN FOR SCALP SETUP", use_container_width=True):
        border_c = '#4a3a1f' if instrument_key == 'XAUUSD' else '#1f3a35'
        st.markdown(f"""
        <div style="border:1px dashed {border_c}; border-radius:6px;
                    padding:60px 20px; text-align:center; margin-top:8px;">
            <div style="font-size:42px; filter:drop-shadow(0 0 12px {cfg['color_primary']});">⚡</div>
            <div style="font-size:11px; letter-spacing:0.35em; margin:14px 0 6px;
                        color:{cfg['color_primary']}; font-weight:700;">READY TO SCAN</div>
            <div style="font-size:13px; color:#888;">
                กดปุ่มด้านบนเพื่อสแกนหา scalp setup</div>
            <div style="font-size:11px; color:#555; margin-top:4px;">
                ใช้เวลา ~3-5 วินาที · กราฟล้วน 100%</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Execute
    progress = st.progress(0, text="📊 Fetching M1/M5/M15...")
    m1, m5, m15 = fetch_scalp_data(cfg['yf_symbol'])

    if m5 is None or len(m5) < 30:
        progress.empty()
        st.error("❌ Yahoo Finance ดึงข้อมูลไม่ได้ชั่วคราว")
        st.info("""
        **วิธีแก้:**
        1. รอ 30-60 วินาที แล้วกด **SCAN** ใหม่ (Yahoo rate limit)
        2. หรือกดปุ่มด้านล่างเพื่อล้าง cache แล้วลองใหม่
        3. ช่วงตลาดปิด (เสาร์-อาทิตย์) ข้อมูลอาจไม่อัปเดต
        """)
        if st.button("🔄 ล้าง Cache แล้วลองใหม่"):
            st.cache_data.clear()
            st.rerun()
        return

    if m1 is m5:
        st.toast("⚠ M1 ไม่พร้อม — ใช้ M5 แทน (ผลวิเคราะห์ยังใช้ได้)", icon="⚠️")

    progress.progress(60, text="🧮 Analyzing price action...")
    settings = {'lot_size': lot_size, 'ounces_per_lot': ounces_per_lot,
                'tp_usd': tp_usd, 'sl_usd': sl_usd}
    try:
        r = analyze_scalp(m1, m5, m15, cfg, settings)
    except Exception as e:
        st.error(f"❌ Analysis error: {e}")
        return

    progress.progress(100, text="✓ Done")
    progress.empty()

    # ===== VERDICT =====
    action_color = cfg['color_primary'] if r['action'] == 'BUY' else '#ff4d6d' if r['action'] == 'SELL' else '#8b949e'
    vclass = 'verdict-buy' if r['action'] == 'BUY' else 'verdict-sell' if r['action'] == 'SELL' else 'verdict-none'
    vtext = '▲ BUY' if r['action'] == 'BUY' else '▼ SELL' if r['action'] == 'SELL' else '— NO TRADE'
    prob_pct = r['probability'] * 100

    cv1, cv2 = st.columns([2, 3])
    with cv1:
        st.markdown(f"""
        <div class="hero-card" style="border-color:{action_color};
             background:linear-gradient(150deg, {action_color}1a 0%, transparent 65%);">
            <div style="font-size:10px; letter-spacing:0.35em; color:{cfg['color_primary']};
                        font-weight:700; margin-bottom:8px;">⚡ SCALP VERDICT</div>
            <div class="{vclass}">{vtext}</div>
            <div style="margin-top:18px;">
                <div style="display:flex; justify-content:space-between;
                            font-size:10px; letter-spacing:0.15em; color:#999;
                            margin-bottom:6px;">
                    <span>PROBABILITY</span><span style="color:{action_color};
                          font-weight:700;">{prob_pct:.0f}%</span>
                </div>
                <div style="height:6px; background:rgba(255,255,255,0.08);
                            border-radius:3px; overflow:hidden;">
                    <div style="height:100%; width:{prob_pct:.0f}%;
                                background:linear-gradient(90deg, {cfg['color_secondary']}, {action_color});
                                box-shadow:0 0 10px {action_color};"></div>
                </div>
                <div style="font-size:10px; letter-spacing:0.15em; color:#777;
                            margin-top:10px;">CONFLUENCE SCORE: <span style="color:{action_color};
                            font-weight:700;">{r['score']:.0f}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with cv2:
        st.markdown('<div class="section-header">เหตุผล / REASONING</div>', unsafe_allow_html=True)
        for reason in r['reasons']:
            icon = "🔴" if r['action'] == 'NO_TRADE' else "🟢"
            st.markdown(f"""<div style="padding:8px 0; font-size:13px;
                         border-bottom:1px solid rgba(255,255,255,0.05);">
                         {icon}&nbsp;&nbsp;{reason}</div>""", unsafe_allow_html=True)

    # ===== TRADE DETAILS =====
    if r['action'] != 'NO_TRADE':
        st.markdown('<div class="section-header">TRADE SETUP</div>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("ENTRY", f"${r['entry']:.2f}")
        c2.metric("TAKE PROFIT", f"${r['tp']:.2f}", f"+${tp_usd:.0f}")
        c3.metric("STOP LOSS", f"${r['sl']:.2f}", f"-${sl_usd:.0f}", delta_color="inverse")
        c4.metric("คาดถึง TP", f"~{r['minutes_to_tp']:.0f} นาที")
        c5.metric("PROBABILITY", f"{r['probability']*100:.0f}%")

    # ===== KEY METRICS =====
    st.markdown('<div class="section-header">PRICE ACTION SNAPSHOT</div>', unsafe_allow_html=True)
    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    m_c1.metric("PRICE", f"${r['current_price']:.2f}")
    m_c2.metric("M15 TREND", r['m15_trend'])
    m_c3.metric("EMA RIBBON", r['ribbon'])
    m_c4.metric("STRUCTURE", r['structure'])

    m_d1, m_d2, m_d3, m_d4 = st.columns(4)
    m_d1.metric("M1 SIGNAL", r['m1_signal'])
    m_d2.metric("RSI M5", f"{r['rsi_m5']:.0f}")
    vwap_status = "ABOVE ✓" if r['above_vwap'] else "BELOW ✗"
    m_d3.metric("VS VWAP", vwap_status)
    m_d4.metric("MACD HIST", f"{r['macd_hist']:.4f}",
                "rising" if r['macd_rising'] else "falling")

    # ===== VELOCITY =====
    st.markdown('<div class="section-header">⚡ SCALP METRICS — VELOCITY & TIMING</div>', unsafe_allow_html=True)
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("ATR M1", f"${r['atr_m1']:.3f}", help="ความผันผวนต่อนาที")
    v2.metric("Recent Velocity", f"${r['recent_velocity']:.3f}/min",
              help="ความเร็วราคา 5 นาทีล่าสุด")
    v3.metric("TP Distance", f"${r['tp_distance']:.3f}",
              help="ระยะที่ราคาต้องวิ่ง")
    v4.metric("Spread กิน", f"{r['spread_ratio']*100:.0f}%",
              help="spread คิดเป็น % ของ TP")

    # ===== CHART =====
    st.markdown('<div class="section-header">M5 CHART · EMA RIBBON + VWAP</div>', unsafe_allow_html=True)
    st.plotly_chart(make_scalp_chart(m5, cfg, r), use_container_width=True)

    # ===== SCORE BREAKDOWN =====
    with st.expander("🔍 ดูรายละเอียดการให้คะแนน (Score Breakdown)"):
        for detail in r['score_details']:
            st.markdown(f"- {detail}")
        st.markdown(f"**รวม: {r['score']:.0f} คะแนน → Probability {r['probability']*100:.0f}%**")

    st.markdown("---")
    st.caption("⚡ SCALP MODE · PURE PRICE ACTION · NO NEWS · FOR EDUCATIONAL USE ONLY")


if __name__ == "__main__":
    main()
