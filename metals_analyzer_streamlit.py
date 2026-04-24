"""
METALS ANALYZER PRO - Streamlit Edition
=========================================
XAU/USD และ XAG/USD Multi-Timeframe Trading Analyzer

Features:
- Real-time price via Yahoo Finance (yfinance)
- Claude AI sentiment analysis (Anthropic API)
- Multi-timeframe analysis (H4/H1/M15/M5)
- Technical indicators: RSI, MACD, BB, ADX, ATR, Pivots
- Interactive charts with Plotly
- Probability model (Brownian + confluence)

Install:
    pip install streamlit yfinance pandas numpy plotly anthropic

Run:
    streamlit run metals_analyzer.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, timezone
import json
import re
import requests
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Metals Analyzer PRO",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# INSTRUMENT CONFIGS
# ============================================================
INSTRUMENTS = {
    "XAUUSD": {
        "name": "GOLD",
        "symbol": "XAU/USD",
        "yf_symbol": "GC=F",
        "ounces_per_lot": 100,
        "typical_atr": 2.5,
        "color_primary": "#ffd700",
        "color_secondary": "#b8860b",
        "emoji": "🥇",
    },
    "XAGUSD": {
        "name": "SILVER",
        "symbol": "XAG/USD",
        "yf_symbol": "SI=F",
        "ounces_per_lot": 5000,
        "typical_atr": 0.08,
        "color_primary": "#00ff9f",
        "color_secondary": "#00b87a",
        "emoji": "🥈",
    },
}

# ============================================================
# CUSTOM CSS
# ============================================================
def inject_css(instrument_key):
    cfg = INSTRUMENTS[instrument_key]
    color = cfg["color_primary"]
    color_dark = cfg["color_secondary"]

    bg = "#0a0705" if instrument_key == "XAUUSD" else "#010409"
    border = "#3d2f1f" if instrument_key == "XAUUSD" else "#30363d"
    text = "#f5e6d3" if instrument_key == "XAUUSD" else "#e6edf3"
    muted = "#8b7355" if instrument_key == "XAUUSD" else "#8b949e"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@700;800&family=Cormorant+Garamond:wght@700;800&display=swap');

        .stApp {{
            background: radial-gradient(ellipse at top, {bg} 0%, #000 100%);
        }}

        html, body, [class*="css"] {{
            font-family: 'JetBrains Mono', monospace !important;
            color: {text};
        }}

        h1, h2, h3 {{
            font-family: {"'Cormorant Garamond', serif" if instrument_key == "XAUUSD" else "'Syne', sans-serif"} !important;
            color: {color} !important;
            letter-spacing: -0.02em;
        }}

        .metric-box {{
            border: 1px solid {border};
            background: rgba(0,0,0,0.4);
            padding: 14px 18px;
            margin-bottom: 8px;
        }}

        .metric-label {{
            font-size: 10px;
            color: {muted};
            letter-spacing: 0.15em;
            margin-bottom: 6px;
            text-transform: uppercase;
        }}

        .metric-value {{
            font-size: 22px;
            font-weight: 700;
            color: {color};
        }}

        .stButton > button {{
            background: linear-gradient(135deg, {color} 0%, {color_dark} 100%);
            color: #010409;
            border: none;
            padding: 14px 24px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            box-shadow: 0 0 20px {color}50;
            width: 100%;
        }}

        .stButton > button:hover {{
            box-shadow: 0 0 30px {color}80;
            transform: translateY(-1px);
        }}

        .live-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {color};
            box-shadow: 0 0 8px {color};
            animation: pulse 2s ease-in-out infinite;
            margin-right: 8px;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .header-badge {{
            font-size: 11px;
            letter-spacing: 0.3em;
            color: {color};
            text-transform: uppercase;
            margin-bottom: 8px;
        }}

        .main-title {{
            font-family: {"'Cormorant Garamond', serif" if instrument_key == "XAUUSD" else "'Syne', sans-serif"} !important;
            font-size: 56px !important;
            font-weight: 800 !important;
            margin: 0 !important;
            line-height: 1 !important;
            font-style: {"italic" if instrument_key == "XAUUSD" else "normal"};
            background: linear-gradient(135deg, {color} 0%, {color_dark} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 20px {color}40);
        }}

        .verdict-buy {{
            font-family: {"'Cormorant Garamond', serif" if instrument_key == "XAUUSD" else "'Syne', sans-serif"};
            font-size: 72px;
            font-weight: 800;
            color: {color};
            text-shadow: 0 0 30px {color}80;
            margin: 0;
            font-style: {"italic" if instrument_key == "XAUUSD" else "normal"};
        }}

        .verdict-sell {{
            font-family: {"'Cormorant Garamond', serif" if instrument_key == "XAUUSD" else "'Syne', sans-serif"};
            font-size: 72px;
            font-weight: 800;
            color: #ff3b6b;
            text-shadow: 0 0 30px #ff3b6b80;
            margin: 0;
            font-style: {"italic" if instrument_key == "XAUUSD" else "normal"};
        }}

        .verdict-none {{
            font-family: {"'Cormorant Garamond', serif" if instrument_key == "XAUUSD" else "'Syne', sans-serif"};
            font-size: 64px;
            font-weight: 800;
            color: {muted};
            margin: 0;
            font-style: {"italic" if instrument_key == "XAUUSD" else "normal"};
        }}

        .section-header {{
            font-size: 11px;
            letter-spacing: 0.2em;
            color: {muted};
            text-transform: uppercase;
            margin: 16px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid {border};
        }}

        [data-testid="stSidebar"] {{
            background: {bg};
            border-right: 1px solid {border};
        }}

        hr {{
            border-color: {border} !important;
        }}

        .stAlert {{
            border-left: 3px solid {color};
        }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# TECHNICAL INDICATORS
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
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def calc_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calc_adx(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    plus_dm = (high.diff()).where((high.diff() > low.diff().abs()) & (high.diff() > 0), 0)
    minus_dm = (-low.diff()).where((low.diff().abs() > high.diff()) & (low.diff() < 0), 0)
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * plus_dm.rolling(period).mean() / atr
    minus_di = 100 * minus_dm.rolling(period).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(period).mean()


def calc_bollinger(series, period=20, std=2):
    sma = series.rolling(period).mean()
    rolling_std = series.rolling(period).std()
    upper = sma + std * rolling_std
    lower = sma - std * rolling_std
    return upper, sma, lower


def calc_pivots(df_prev_day):
    """Calculate daily pivot points from previous day's data"""
    if len(df_prev_day) == 0:
        return None
    prev_high = df_prev_day['High'].max()
    prev_low = df_prev_day['Low'].min()
    prev_close = df_prev_day['Close'].iloc[-1]
    pivot = (prev_high + prev_low + prev_close) / 3
    return {
        'pivot': pivot,
        'r1': 2 * pivot - prev_low,
        'r2': pivot + (prev_high - prev_low),
        's1': 2 * pivot - prev_high,
        's2': pivot - (prev_high - prev_low),
    }


def detect_candle_pattern(df):
    """Simple candle pattern detection on last 2 bars"""
    if len(df) < 2:
        return "none"
    c1 = df.iloc[-2]
    c2 = df.iloc[-1]

    body2 = abs(c2['Close'] - c2['Open'])
    range2 = c2['High'] - c2['Low']
    upper_shadow = c2['High'] - max(c2['Open'], c2['Close'])
    lower_shadow = min(c2['Open'], c2['Close']) - c2['Low']

    # Bullish engulfing
    if c1['Close'] < c1['Open'] and c2['Close'] > c2['Open']:
        if c2['Open'] < c1['Close'] and c2['Close'] > c1['Open']:
            return "bullish_engulfing"
    # Bearish engulfing
    if c1['Close'] > c1['Open'] and c2['Close'] < c2['Open']:
        if c2['Open'] > c1['Close'] and c2['Close'] < c1['Open']:
            return "bearish_engulfing"
    # Hammer
    if body2 > 0 and lower_shadow >= 2 * body2 and upper_shadow < body2:
        return "hammer"
    # Shooting star
    if body2 > 0 and upper_shadow >= 2 * body2 and lower_shadow < body2:
        return "shooting_star"
    # Doji
    if range2 > 0 and body2 < range2 * 0.1:
        return "doji"
    return "none"


# ============================================================
# DATA FETCHING
# ============================================================
@st.cache_data(ttl=120, show_spinner=False)
def fetch_price_data(yf_symbol):
    """Fetch multi-timeframe data from Yahoo Finance"""
    try:
        m5 = yf.download(yf_symbol, interval="5m", period="5d",
                         progress=False, auto_adjust=False)
        h1 = yf.download(yf_symbol, interval="60m", period="30d",
                         progress=False, auto_adjust=False)
        h4 = yf.download(yf_symbol, interval="1h", period="60d",
                         progress=False, auto_adjust=False)

        # Flatten multi-level columns
        for df in [m5, h1, h4]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

        return m5, h1, h4
    except Exception as e:
        st.error(f"yfinance error: {e}")
        return None, None, None


# ============================================================
# CLAUDE API
# ============================================================
def call_claude(api_key, system_prompt, user_prompt, max_tokens=1000, timeout=20):
    """Call Claude API directly (no CORS issues in Python)"""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    response = requests.post(url, headers=headers, json=body, timeout=timeout)
    if response.status_code != 200:
        raise Exception(f"API {response.status_code}: {response.text[:200]}")
    data = response.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def parse_json_loose(text):
    """Parse JSON from text, handling markdown fences and prose"""
    cleaned = re.sub(r'```json\s*', '', text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON found")
    return json.loads(cleaned[start:end + 1])


def ai_sentiment_analysis(api_key, cfg, tech_data, session_label):
    """Get sentiment + setup quality from Claude"""
    system = "You are a metals market analyst. Return ONLY valid JSON."
    prompt = f"""{cfg['name']} technical snapshot:
- Price: ${tech_data['current_price']:.2f} ({tech_data['price_change_24h_pct']:+.2f}% 24h)
- H4: {tech_data['h4_trend']}, H1: {tech_data['h1_trend']} (ADX {tech_data['h1_adx']:.0f}), M5: {tech_data['m5_signal']}
- RSI H1/M5: {tech_data['rsi_h1']:.0f}/{tech_data['rsi_m5']:.0f}
- MACD hist: {tech_data['macd_hist_m5']:.4f}
- BB M5: {tech_data['bb_position_m5']}{'  SQUEEZE' if tech_data.get('bb_squeeze') else ''}
- Session: {session_label}
- UTC: {datetime.now(timezone.utc).isoformat()}

Analyze based on this data. Return JSON:
{{
  "setup_quality": "A_PLUS"|"B"|"C"|"AVOID",
  "setup_reasoning": "<2 sentences in Thai>",
  "confluence_bullish": <0-10>,
  "confluence_bearish": <0-10>,
  "news_sentiment": "BULLISH"|"NEUTRAL"|"BEARISH",
  "sentiment_score": <-10 to +10>,
  "sentiment_reason": "<2 sentences in Thai>",
  "has_high_impact_in_1h": <bool>,
  "geopolitical_risk": "HIGH"|"ELEVATED"|"NORMAL"|"LOW",
  "positioning": "EXTREME_LONG"|"LONG"|"NEUTRAL"|"SHORT"|"EXTREME_SHORT",
  "dxy_trend": "STRONG"|"WEAK"|"NEUTRAL"
}}
Output JSON only, no explanation."""

    try:
        text = call_claude(api_key, system, prompt, max_tokens=800, timeout=20)
        return parse_json_loose(text)
    except Exception as e:
        st.warning(f"AI analysis failed: {e}")
        return {
            "setup_quality": "B",
            "setup_reasoning": "ใช้การวิเคราะห์จาก technical อย่างเดียว (AI ไม่ได้)",
            "confluence_bullish": 5,
            "confluence_bearish": 5,
            "news_sentiment": "NEUTRAL",
            "sentiment_score": 0,
            "sentiment_reason": "ไม่สามารถดึงข้อมูล sentiment ได้",
            "has_high_impact_in_1h": False,
            "geopolitical_risk": "NORMAL",
            "positioning": "NEUTRAL",
            "dxy_trend": "NEUTRAL",
        }


# ============================================================
# COMPUTE TECHNICALS
# ============================================================
def compute_technicals(m5, h1, h4):
    # M5 indicators
    m5_close = m5['Close']
    ema20_m5 = calc_ema(m5_close, 20)
    rsi_m5_series = calc_rsi(m5_close)
    macd_m5, signal_m5, hist_m5 = calc_macd(m5_close)
    atr_m5_series = calc_atr(m5)
    bb_upper, bb_mid, bb_lower = calc_bollinger(m5_close)

    current = float(m5_close.iloc[-1])
    last_rsi_m5 = float(rsi_m5_series.iloc[-1])
    last_macd_hist = float(hist_m5.iloc[-1])
    prev_macd_hist = float(hist_m5.iloc[-2])
    last_atr = float(atr_m5_series.iloc[-1])
    last_bb_upper = float(bb_upper.iloc[-1])
    last_bb_lower = float(bb_lower.iloc[-1])
    last_ema20 = float(ema20_m5.iloc[-1])
    prev_ema20 = float(ema20_m5.iloc[-2])
    prev_close = float(m5_close.iloc[-2])

    # M5 signal
    if prev_close <= prev_ema20 and current > last_ema20:
        m5_signal = "BUY_SIGNAL"
    elif current > last_ema20 and current > prev_close:
        m5_signal = "BUY_BIAS"
    elif prev_close >= prev_ema20 and current < last_ema20:
        m5_signal = "SELL_SIGNAL"
    elif current < last_ema20 and current < prev_close:
        m5_signal = "SELL_BIAS"
    else:
        m5_signal = "NEUTRAL"

    # MACD cross
    if last_macd_hist > 0 and prev_macd_hist <= 0:
        macd_signal_status = "BULL_CROSS"
    elif last_macd_hist < 0 and prev_macd_hist >= 0:
        macd_signal_status = "BEAR_CROSS"
    else:
        macd_signal_status = "NONE"

    # BB position
    bb_range = last_bb_upper - last_bb_lower
    bb_pct = (current - last_bb_lower) / bb_range if bb_range > 0 else 0.5
    if bb_pct > 0.9:
        bb_pos = "UPPER"
    elif bb_pct > 0.6:
        bb_pos = "MIDDLE_UP"
    elif bb_pct < 0.1:
        bb_pos = "LOWER"
    elif bb_pct < 0.4:
        bb_pos = "MIDDLE_DOWN"
    else:
        bb_pos = "MIDDLE"

    # BB squeeze
    bb_widths = (bb_upper - bb_lower).tail(20).dropna()
    avg_bb_width = bb_widths.mean() if len(bb_widths) > 0 else bb_range
    bb_squeeze = bool(bb_range < avg_bb_width * 0.8) if avg_bb_width > 0 else False

    # H1
    h1_close = h1['Close']
    ema50_h1 = calc_ema(h1_close, 50)
    ema200_h1 = calc_ema(h1_close, 200) if len(h1_close) >= 200 else ema50_h1
    rsi_h1_series = calc_rsi(h1_close)
    adx_h1_series = calc_adx(h1)

    last_h1_price = float(h1_close.iloc[-1])
    last_ema50_h1 = float(ema50_h1.iloc[-1])
    last_ema200_h1 = float(ema200_h1.iloc[-1])
    last_rsi_h1 = float(rsi_h1_series.iloc[-1])
    last_adx_h1 = float(adx_h1_series.iloc[-1]) if not pd.isna(adx_h1_series.iloc[-1]) else 15

    h1_slope = float(ema50_h1.iloc[-1] - ema50_h1.iloc[-10]) if len(ema50_h1) >= 10 else 0

    if last_h1_price > last_ema50_h1 and last_ema50_h1 > last_ema200_h1 and h1_slope > 0:
        h1_trend = "STRONG_UP"
    elif last_h1_price > last_ema50_h1 and h1_slope > 0:
        h1_trend = "UP"
    elif last_h1_price < last_ema50_h1 and last_ema50_h1 < last_ema200_h1 and h1_slope < 0:
        h1_trend = "STRONG_DOWN"
    elif last_h1_price < last_ema50_h1 and h1_slope < 0:
        h1_trend = "DOWN"
    else:
        h1_trend = "SIDEWAYS"

    # H4
    h4_close = h4['Close']
    ema50_h4 = calc_ema(h4_close, 50)
    last_h4_price = float(h4_close.iloc[-1])
    last_ema50_h4 = float(ema50_h4.iloc[-1])
    h4_slope = float(ema50_h4.iloc[-1] - ema50_h4.iloc[-5]) if len(ema50_h4) >= 5 else 0

    if last_h4_price > last_ema50_h4 and h4_slope > 0.5:
        h4_trend = "STRONG_UP"
    elif last_h4_price > last_ema50_h4 and h4_slope > 0:
        h4_trend = "UP"
    elif last_h4_price < last_ema50_h4 and h4_slope < -0.5:
        h4_trend = "STRONG_DOWN"
    elif last_h4_price < last_ema50_h4 and h4_slope < 0:
        h4_trend = "DOWN"
    else:
        h4_trend = "SIDEWAYS"

    # M15 momentum (ใช้ recent 5 M5 bars)
    recent5 = m5_close.tail(5).values
    trend_val = recent5[-1] - recent5[0]
    volatility = max(recent5) - min(recent5)
    if volatility > 0 and trend_val > volatility * 0.3:
        m15_momentum = "BULLISH"
    elif volatility > 0 and trend_val < -volatility * 0.3:
        m15_momentum = "BEARISH"
    else:
        m15_momentum = "NEUTRAL"

    # Daily high/low (approx from m5)
    today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_bars = m5[m5.index.tz_convert('UTC') >= today_utc] if m5.index.tz is not None else m5.tail(288)
    if len(today_bars) > 0:
        daily_high = float(today_bars['High'].max())
        daily_low = float(today_bars['Low'].min())
    else:
        daily_high = float(m5.tail(288)['High'].max())
        daily_low = float(m5.tail(288)['Low'].min())

    # Pivots from previous day (h1)
    prev_day_bars = h1.iloc[-24:-1] if len(h1) >= 24 else h1.iloc[:-1]
    pivots = calc_pivots(prev_day_bars) or {
        'pivot': current, 'r1': None, 'r2': None, 's1': None, 's2': None
    }

    # Price change 24h
    price_24h = float(m5_close.iloc[-288]) if len(m5_close) >= 288 else float(m5_close.iloc[0])
    price_change_24h = ((current - price_24h) / price_24h) * 100

    # Candle pattern
    pattern = detect_candle_pattern(m5)

    # Volume
    if 'Volume' in m5.columns and m5['Volume'].sum() > 0:
        avg_vol = m5['Volume'].tail(20).mean()
        last_vol = m5['Volume'].iloc[-1]
        if last_vol > avg_vol * 1.5:
            volume_status = "HIGH"
        elif last_vol < avg_vol * 0.5:
            volume_status = "LOW"
        else:
            volume_status = "NORMAL"
    else:
        volume_status = "NORMAL"

    return {
        "current_price": current,
        "price_change_24h_pct": price_change_24h,
        "daily_high": daily_high,
        "daily_low": daily_low,
        "h4_trend": h4_trend,
        "h1_trend": h1_trend,
        "h1_adx": last_adx_h1,
        "m15_momentum": m15_momentum,
        "m5_signal": m5_signal,
        "m5_candle_pattern": pattern,
        "rsi_h1": last_rsi_h1,
        "rsi_m5": last_rsi_m5,
        "macd_hist_m5": last_macd_hist,
        "macd_signal_m5": macd_signal_status,
        "bb_position_m5": bb_pos,
        "bb_squeeze": bb_squeeze,
        "atr_m5": last_atr,
        "volume_vs_avg": volume_status,
        "pivot_daily": pivots['pivot'],
        "r1": pivots['r1'], "r2": pivots['r2'],
        "s1": pivots['s1'], "s2": pivots['s2'],
    }


# ============================================================
# DECISION LOGIC
# ============================================================
def compute_decision(tech, ai, settings, session_overlap, session_quiet, instrument):
    usd_per_move = settings['lot_size'] * settings['ounces_per_lot']
    price_move_needed = settings['tp_usd'] / usd_per_move
    current = tech['current_price']
    atr = tech['atr_m5']
    bars_to_tp = price_move_needed / atr if atr > 0 else 999

    # Direction
    direction = None
    if "BUY" in tech['m5_signal']:
        direction = "BUY"
    elif "SELL" in tech['m5_signal']:
        direction = "SELL"

    # Alignments
    h4_bull = tech['h4_trend'] in ["STRONG_UP", "UP"]
    h4_bear = tech['h4_trend'] in ["STRONG_DOWN", "DOWN"]
    h1_bull = tech['h1_trend'] in ["STRONG_UP", "UP"]
    h1_bear = tech['h1_trend'] in ["STRONG_DOWN", "DOWN"]
    m15_bull = tech['m15_momentum'] == "BULLISH"
    m15_bear = tech['m15_momentum'] == "BEARISH"

    mtf_bull = h4_bull and h1_bull and m15_bull
    mtf_bear = h4_bear and h1_bear and m15_bear

    rsi_h1 = tech['rsi_h1']
    rsi_m5 = tech['rsi_m5']
    rsi_bull = 50 < rsi_h1 and 50 < rsi_m5 < 75
    rsi_bear = rsi_h1 < 50 and 25 < rsi_m5 < 50

    macd_bull = tech['macd_hist_m5'] > 0 or tech['macd_signal_m5'] == "BULL_CROSS"
    macd_bear = tech['macd_hist_m5'] < 0 or tech['macd_signal_m5'] == "BEAR_CROSS"

    adx_strong = tech['h1_adx'] > 20
    adx_very_strong = tech['h1_adx'] > 25

    # Score
    score = 0
    if direction == "BUY":
        if mtf_bull: score += 25
        elif h4_bull and h1_bull: score += 15
        elif h1_bull: score += 8
        elif h4_bear or h1_bear: score -= 20

        if adx_very_strong: score += 10
        elif adx_strong: score += 5
        else: score -= 8

        if rsi_bull: score += 10
        if rsi_m5 > 75: score -= 5

        if macd_bull: score += 8
        elif macd_bear: score -= 10

        if tech['volume_vs_avg'] == "HIGH": score += 5
        if tech['bb_squeeze']: score += 5
        if tech['bb_position_m5'] == "UPPER": score -= 3

        score += ai.get('sentiment_score', 0) * 1.2

        if ai.get('dxy_trend') == "WEAK": score += 6
        if ai.get('dxy_trend') == "STRONG": score -= 8

        if ai.get('positioning') == "EXTREME_LONG": score -= 6
        if ai.get('positioning') == "EXTREME_SHORT": score += 6

        if tech['m5_candle_pattern'] in ['bullish_engulfing', 'hammer']: score += 6
        if tech['m5_candle_pattern'] in ['bearish_engulfing', 'shooting_star']: score -= 10

    elif direction == "SELL":
        if mtf_bear: score += 25
        elif h4_bear and h1_bear: score += 15
        elif h1_bear: score += 8
        elif h4_bull or h1_bull: score -= 20

        if adx_very_strong: score += 10
        elif adx_strong: score += 5
        else: score -= 8

        if rsi_bear: score += 10
        if rsi_m5 < 25: score -= 5

        if macd_bear: score += 8
        elif macd_bull: score -= 10

        if tech['volume_vs_avg'] == "HIGH": score += 5
        if tech['bb_squeeze']: score += 5
        if tech['bb_position_m5'] == "LOWER": score -= 3

        score -= ai.get('sentiment_score', 0) * 1.2

        if ai.get('dxy_trend') == "STRONG": score += 6
        if ai.get('dxy_trend') == "WEAK": score -= 8

        if ai.get('positioning') == "EXTREME_SHORT": score -= 6
        if ai.get('positioning') == "EXTREME_LONG": score += 6

        if tech['m5_candle_pattern'] in ['bearish_engulfing', 'shooting_star']: score += 6
        if tech['m5_candle_pattern'] in ['bullish_engulfing', 'hammer']: score -= 10

    if session_overlap: score += 3
    if session_quiet: score -= 5
    if bars_to_tp > 25: score -= 10
    elif bars_to_tp < 2: score -= 5

    if ai.get('setup_quality') == "A_PLUS": score += 8
    elif ai.get('setup_quality') == "AVOID": score -= 15

    # Probability via sigmoid
    prob = 1 / (1 + np.exp(-score / 25))
    prob = max(0.05, min(0.90, prob))
    ev = prob * settings['tp_usd'] - (1 - prob) * settings['sl_usd']

    # Blocks
    action = "NO_TRADE"
    reasons = []
    blocks = []

    if not direction: blocks.append("M5 ไม่มีสัญญาณชัด")
    if ai.get('setup_quality') == "AVOID": blocks.append("Setup quality = AVOID")
    if ai.get('has_high_impact_in_1h'): blocks.append("ข่าวแรงใน 1 ชม.")
    if not adx_strong: blocks.append(f"ADX {tech['h1_adx']:.0f} < 20 (sideways)")
    if bars_to_tp > 30: blocks.append(f"TP ไกล ({int(bars_to_tp)} แท่ง)")

    if direction == "BUY":
        if h4_bear: blocks.append(f"H4 {tech['h4_trend']} สวน BUY")
        if tech['bb_position_m5'] == "UPPER" and rsi_m5 > 70: blocks.append("Overbought")
    elif direction == "SELL":
        if h4_bull: blocks.append(f"H4 {tech['h4_trend']} สวน SELL")
        if tech['bb_position_m5'] == "LOWER" and rsi_m5 < 30: blocks.append("Oversold")

    if prob < 0.55: blocks.append(f"Probability {prob*100:.0f}% < 55%")
    if ev < 0: blocks.append("EV ติดลบ")

    if not blocks and direction:
        action = direction
        reasons = [
            "MTF align ทุก timeframe",
            f"ADX {tech['h1_adx']:.0f} > 20 (trending)",
            f"Confluence {ai.get('confluence_bullish', 5)}↑ / {ai.get('confluence_bearish', 5)}↓",
            f"Setup quality: {ai.get('setup_quality', 'B')}",
            f"Probability {prob*100:.0f}%",
        ]
    else:
        reasons = blocks

    # Entry/TP/SL
    entry = current
    tp = sl = None
    if action == "BUY":
        tp = current + price_move_needed
        sl = current - price_move_needed
    elif action == "SELL":
        tp = current - price_move_needed
        sl = current + price_move_needed

    return {
        "action": action,
        "reasons": reasons,
        "score": score,
        "probability": prob,
        "ev": ev,
        "rr_ratio": settings['tp_usd'] / settings['sl_usd'],
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "price_move_needed": price_move_needed,
        "bars_to_tp": bars_to_tp,
        "direction_guess": direction,
    }


# ============================================================
# SESSION DETECTION
# ============================================================
def get_session():
    utc_hour = datetime.now(timezone.utc).hour
    sessions = []
    if utc_hour >= 23 or utc_hour < 8: sessions.append("ASIAN")
    if 7 <= utc_hour < 16: sessions.append("LONDON")
    if 12 <= utc_hour < 21: sessions.append("NY")
    overlap = len(sessions) > 1
    main = sessions[-1] if sessions else "QUIET"
    label = main + (" OVERLAP" if overlap else "")
    return {"main": main, "overlap": overlap, "label": label}


# ============================================================
# CHART
# ============================================================
def make_chart(m5, cfg, decision):
    close = m5['Close']
    ema20 = calc_ema(close, 20)
    rsi_series = calc_rsi(close)
    macd_line, macd_sig, macd_hist = calc_macd(close)
    bb_upper, bb_mid, bb_lower = calc_bollinger(close)

    recent = m5.tail(120).copy()
    recent['ema20'] = ema20.tail(120)
    recent['bb_u'] = bb_upper.tail(120)
    recent['bb_l'] = bb_lower.tail(120)
    recent['rsi'] = rsi_series.tail(120)
    recent['macd'] = macd_line.tail(120)
    recent['macd_sig'] = macd_sig.tail(120)
    recent['macd_hist'] = macd_hist.tail(120)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.03,
        subplot_titles=(None, None, None),
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=recent.index,
        open=recent['Open'], high=recent['High'],
        low=recent['Low'], close=recent['Close'],
        name="Price",
        increasing_line_color=cfg['color_primary'],
        decreasing_line_color='#ff3b6b',
    ), row=1, col=1)

    # EMA20
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['ema20'],
        line=dict(color='#ffb84d', width=1.5),
        name="EMA20",
    ), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['bb_u'],
        line=dict(color=cfg['color_primary'], width=1, dash='dot'),
        name="BB Upper", opacity=0.4,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['bb_l'],
        line=dict(color=cfg['color_primary'], width=1, dash='dot'),
        name="BB Lower", opacity=0.4,
        fill='tonexty', fillcolor=f"rgba(255,215,0,0.05)",
    ), row=1, col=1)

    # TP/SL lines
    if decision['action'] != 'NO_TRADE':
        fig.add_hline(y=decision['tp'], line_dash="dash",
                      line_color=cfg['color_primary'],
                      annotation_text="TP", row=1, col=1)
        fig.add_hline(y=decision['sl'], line_dash="dash",
                      line_color="#ff3b6b",
                      annotation_text="SL", row=1, col=1)
        fig.add_hline(y=decision['entry'], line_dash="dot",
                      line_color="#ffb84d",
                      annotation_text="ENTRY", row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['rsi'],
        line=dict(color='#bc8cff', width=1.5),
        name="RSI(14)",
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ff3b6b", row=2, col=1, opacity=0.4)
    fig.add_hline(y=50, line_dash="dot", line_color="#888", row=2, col=1, opacity=0.3)
    fig.add_hline(y=30, line_dash="dash", line_color=cfg['color_primary'], row=2, col=1, opacity=0.4)

    # MACD
    colors = [cfg['color_primary'] if v >= 0 else '#ff3b6b' for v in recent['macd_hist']]
    fig.add_trace(go.Bar(
        x=recent.index, y=recent['macd_hist'],
        marker_color=colors, name="MACD Hist", opacity=0.5,
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['macd'],
        line=dict(color='#58a6ff', width=1.2),
        name="MACD",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent['macd_sig'],
        line=dict(color='#ff3b6b', width=1.2),
        name="Signal",
    ), row=3, col=1)

    fig.update_layout(
        height=650,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.3)',
        font=dict(family="JetBrains Mono", color="#e6edf3", size=10),
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.update_xaxes(gridcolor='rgba(100,100,100,0.1)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(100,100,100,0.1)', showgrid=True)
    return fig


# ============================================================
# MAIN APP
# ============================================================
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ CONFIGURATION")

        instrument_key = st.selectbox(
            "INSTRUMENT",
            options=list(INSTRUMENTS.keys()),
            format_func=lambda k: f"{INSTRUMENTS[k]['emoji']} {INSTRUMENTS[k]['symbol']}",
        )
        cfg = INSTRUMENTS[instrument_key]

        st.markdown("---")
        st.markdown("### 📊 POSITION SIZE")
        lot_size = st.number_input("Lot Size", value=0.01, step=0.01, format="%.2f")
        ounces_per_lot = st.number_input("Oz / Lot", value=cfg['ounces_per_lot'], step=10)
        tp_usd = st.number_input("TP (USD)", value=20.0, step=5.0)
        sl_usd = st.number_input("SL (USD)", value=20.0, step=5.0)

        st.markdown("---")
        st.markdown("### 🔑 CLAUDE API")

        use_ai = st.checkbox("Use Claude for sentiment", value=True)
        if use_ai:
            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="sk-ant-api03-...",
                help="Get free key at console.anthropic.com"
            )
        else:
            api_key = ""

        st.markdown("---")
        st.caption(f"💡 1 lot = {ounces_per_lot} oz")
        price_move = tp_usd / (lot_size * ounces_per_lot) if lot_size * ounces_per_lot > 0 else 0
        st.caption(f"⚡ TP distance: ${price_move:.3f}/oz")

    # Inject CSS
    inject_css(instrument_key)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f'<div class="header-badge"><span class="live-dot"></span>PRO TERMINAL · LIVE YAHOO + CLAUDE AI</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<h1 class="main-title">{cfg["name"]} · {cfg["symbol"]}</h1>',
            unsafe_allow_html=True
        )
        st.caption("MULTI-TIMEFRAME · H4/H1/M15/M5 · ADX · CONFLUENCE · SESSION ANALYSIS")

    with col2:
        now = datetime.now()
        bkk = now.astimezone(timezone(timedelta(hours=7)))
        utc = datetime.now(timezone.utc)
        st.markdown(f"""
        <div style="text-align:right; color:#8b949e; font-size:11px; letter-spacing:0.15em; margin-top:20px;">
            <div style="color:{cfg['color_primary']}; font-weight:700;">🇹🇭 BKK · {bkk.strftime('%H:%M:%S')}</div>
            <div style="margin-top:4px;">UTC · {utc.strftime('%H:%M:%S')}</div>
            <div style="margin-top:4px; opacity:0.6;">{bkk.strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Run button
    run = st.button("▶ EXECUTE ANALYSIS", use_container_width=True)

    if not run:
        st.markdown(f"""
        <div style="border:1px dashed {'#3d2f1f' if instrument_key == 'XAUUSD' else '#30363d'};
                     padding:60px 20px; text-align:center; color:#6e7681;">
            <div style="font-size:32px; margin-bottom:20px;">🧠</div>
            <div style="font-size:11px; letter-spacing:0.3em; margin-bottom:12px;">AWAITING COMMAND</div>
            <div style="font-size:14px;">กด EXECUTE ANALYSIS เพื่อเริ่มวิเคราะห์</div>
            <div style="font-size:11px; margin-top:8px; opacity:0.6;">ใช้เวลาประมาณ 5-10 วินาที</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ========== EXECUTE ==========
    progress_bar = st.progress(0, text="Starting...")

    # Step 1: Fetch price
    progress_bar.progress(20, text="📊 Fetching price data from Yahoo Finance...")
    m5, h1, h4 = fetch_price_data(cfg['yf_symbol'])

    if m5 is None or h1 is None or len(m5) < 50 or len(h1) < 50:
        st.error("❌ ไม่สามารถดึงข้อมูลราคาได้ — ลองรันใหม่อีกครั้ง")
        return

    st.toast(f"✓ Got M5: {len(m5)} bars · H1: {len(h1)} bars · H4: {len(h4)} bars", icon="✅")

    # Step 2: Compute technicals
    progress_bar.progress(50, text="🧮 Computing indicators...")
    try:
        tech = compute_technicals(m5, h1, h4)
    except Exception as e:
        st.error(f"❌ Error computing indicators: {e}")
        return

    # Step 3: AI analysis
    session = get_session()
    if use_ai and api_key:
        progress_bar.progress(70, text="🧠 Claude analyzing sentiment...")
        ai = ai_sentiment_analysis(api_key, cfg, tech, session['label'])
    else:
        ai = {
            "setup_quality": "B",
            "setup_reasoning": "ใช้การวิเคราะห์จาก technical อย่างเดียว",
            "confluence_bullish": 5,
            "confluence_bearish": 5,
            "news_sentiment": "NEUTRAL",
            "sentiment_score": 0,
            "sentiment_reason": "ปิด AI analysis",
            "has_high_impact_in_1h": False,
            "geopolitical_risk": "NORMAL",
            "positioning": "NEUTRAL",
            "dxy_trend": "NEUTRAL",
        }

    # Step 4: Decision
    progress_bar.progress(90, text="🎯 Computing edge...")
    settings = {
        "lot_size": lot_size,
        "ounces_per_lot": ounces_per_lot,
        "tp_usd": tp_usd,
        "sl_usd": sl_usd,
    }
    decision = compute_decision(tech, ai, settings, session['overlap'], session['main'] == 'QUIET', instrument_key)

    progress_bar.progress(100, text="✓ Done!")
    progress_bar.empty()

    # ========== DISPLAY RESULTS ==========
    action_color = cfg['color_primary'] if decision['action'] == 'BUY' else '#ff3b6b' if decision['action'] == 'SELL' else '#8b949e'

    # Verdict hero
    verdict_class = 'verdict-buy' if decision['action'] == 'BUY' else 'verdict-sell' if decision['action'] == 'SELL' else 'verdict-none'
    verdict_text = '▲ BUY' if decision['action'] == 'BUY' else '▼ SELL' if decision['action'] == 'SELL' else '— NO TRADE'

    col_v1, col_v2 = st.columns([2, 3])
    with col_v1:
        st.markdown(f"""
        <div style="border:2px solid {action_color}; padding:32px; margin-bottom:16px;
                    background:linear-gradient(135deg, {action_color}15 0%, transparent 60%);">
            <div style="font-size:11px; letter-spacing:0.3em; color:#8b949e; margin-bottom:8px;">
                FINAL VERDICT · {session['label']}
            </div>
            <div class="{verdict_class}">{verdict_text}</div>
            <div style="font-size:12px; color:#8b949e; margin-top:12px; letter-spacing:0.1em;">
                CONFLUENCE SCORE: {decision['score']:.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_v2:
        st.markdown('<div class="section-header">REASONING</div>', unsafe_allow_html=True)
        for r in decision['reasons']:
            icon = "✗" if decision['action'] == 'NO_TRADE' else "✓"
            st.markdown(f"- {icon} {r}")

        if ai.get('setup_reasoning'):
            st.info(f"💡 {ai['setup_reasoning']}")

    # Trade details
    if decision['action'] != 'NO_TRADE':
        st.markdown('<div class="section-header">TRADE DETAILS</div>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("ENTRY", f"${decision['entry']:.2f}")
        with c2:
            st.metric("TAKE PROFIT", f"${decision['tp']:.2f}", f"+${tp_usd:.0f}")
        with c3:
            st.metric("STOP LOSS", f"${decision['sl']:.2f}", f"-${sl_usd:.0f}", delta_color="inverse")
        with c4:
            st.metric("PROBABILITY", f"{decision['probability']*100:.1f}%")
        with c5:
            st.metric("EXPECTED VALUE", f"${decision['ev']:.2f}",
                     delta="positive" if decision['ev'] > 0 else "negative")

    # MTF + Indicators
    st.markdown('<div class="section-header">MULTI-TIMEFRAME + INDICATORS</div>', unsafe_allow_html=True)

    col_mtf1, col_mtf2, col_mtf3, col_mtf4 = st.columns(4)

    def trend_emoji(t):
        if "UP" in t: return "📈"
        if "DOWN" in t: return "📉"
        return "➡️"

    with col_mtf1:
        st.metric("H4 TREND", f"{trend_emoji(tech['h4_trend'])} {tech['h4_trend']}")
    with col_mtf2:
        st.metric("H1 TREND", f"{trend_emoji(tech['h1_trend'])} {tech['h1_trend']}",
                 f"ADX {tech['h1_adx']:.0f}")
    with col_mtf3:
        st.metric("M15 MOMENTUM", tech['m15_momentum'])
    with col_mtf4:
        st.metric("M5 SIGNAL", tech['m5_signal'],
                 tech['m5_candle_pattern'] if tech['m5_candle_pattern'] != 'none' else None)

    # Indicator details
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    with col_i1:
        st.metric("PRICE",
                 f"${tech['current_price']:.2f}",
                 f"{tech['price_change_24h_pct']:+.2f}% 24h")
    with col_i2:
        st.metric("RSI H1/M5",
                 f"{tech['rsi_h1']:.0f} / {tech['rsi_m5']:.0f}")
    with col_i3:
        st.metric("MACD M5",
                 tech['macd_signal_m5'],
                 f"Hist {tech['macd_hist_m5']:.4f}")
    with col_i4:
        bb_label = tech['bb_position_m5'] + (" ⚡" if tech['bb_squeeze'] else "")
        st.metric("BB M5", bb_label,
                 "SQUEEZE" if tech['bb_squeeze'] else None)

    # Chart
    st.markdown('<div class="section-header">PRICE CHART · M5 (LAST 120 BARS)</div>', unsafe_allow_html=True)
    fig = make_chart(m5, cfg, decision)
    st.plotly_chart(fig, use_container_width=True)

    # Pivot levels
    st.markdown('<div class="section-header">KEY LEVELS · DAILY PIVOTS</div>', unsafe_allow_html=True)
    pc1, pc2, pc3, pc4, pc5 = st.columns(5)
    with pc1:
        st.metric("R2", f"${tech['r2']:.2f}" if tech['r2'] else "—")
    with pc2:
        st.metric("R1", f"${tech['r1']:.2f}" if tech['r1'] else "—")
    with pc3:
        st.metric("PIVOT", f"${tech['pivot_daily']:.2f}")
    with pc4:
        st.metric("S1", f"${tech['s1']:.2f}" if tech['s1'] else "—")
    with pc5:
        st.metric("S2", f"${tech['s2']:.2f}" if tech['s2'] else "—")

    # AI insights
    if use_ai:
        st.markdown('<div class="section-header">AI MARKET INTELLIGENCE</div>', unsafe_allow_html=True)
        col_ai1, col_ai2 = st.columns(2)
        with col_ai1:
            sentiment_color = cfg['color_primary'] if 'BULLISH' in ai.get('news_sentiment', '') else '#ff3b6b' if 'BEARISH' in ai.get('news_sentiment', '') else '#ffb84d'
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">SENTIMENT</div>
                <div style="font-size:18px; font-weight:700; color:{sentiment_color};">
                    {ai.get('news_sentiment', 'N/A')} ({ai.get('sentiment_score', 0):+d})
                </div>
                <div style="font-size:12px; color:#8b949e; margin-top:10px; line-height:1.6;">
                    {ai.get('sentiment_reason', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_ai2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">CONTEXT</div>
                <div style="font-size:12px; line-height:1.8; color:#e6edf3;">
                    📍 Positioning: <strong>{ai.get('positioning', 'N/A')}</strong><br>
                    🌍 Geopolitical: <strong>{ai.get('geopolitical_risk', 'N/A')}</strong><br>
                    💵 DXY: <strong>{ai.get('dxy_trend', 'N/A')}</strong><br>
                    📰 News 1h: <strong>{'⚠ HIGH RISK' if ai.get('has_high_impact_in_1h') else '✓ CLEAR'}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("⚠ FOR EDUCATIONAL USE · NOT INVESTMENT ADVICE · POWERED BY YAHOO FINANCE + CLAUDE AI")


if __name__ == "__main__":
    main()
