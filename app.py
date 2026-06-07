"""
Jupiter Prediction Markets Dashboard
Top 20 Profitable Traders + Live Crypto Markets
Author: Generated with Claude
"""

import streamlit as st
import requests
import pandas as pd
import time
import json
from datetime import datetime, timezone
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Jupiter Predict Tracker",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Dark neon theme */
.stApp {
    background: #080c14;
    color: #e2e8f0;
}

.main .block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}

/* Header */
.dash-header {
    background: linear-gradient(135deg, #0f1929 0%, #0d1f3c 50%, #091525 100%);
    border: 1px solid #1a3a6b;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.dash-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00c2ff, #7b2fff, #00c2ff);
    animation: shimmer 3s linear infinite;
    background-size: 200% 100%;
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
.dash-title {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00c2ff, #7b2fff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.2;
}
.dash-sub {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #4a7fb5;
    margin-top: 0.3rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Metric cards */
.metric-card {
    background: #0d1929;
    border: 1px solid #1a3a6b;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #00c2ff; }
.metric-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #4a7fb5;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: #e2e8f0;
}
.metric-delta {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    margin-top: 0.2rem;
}
.pos { color: #00e676; }
.neg { color: #ff5252; }

/* Leaderboard table */
.lb-rank {
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    color: #4a7fb5;
}
.lb-rank-1 { color: #ffd700; }
.lb-rank-2 { color: #c0c0c0; }
.lb-rank-3 { color: #cd7f32; }

/* Status badge */
.badge {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-live { background: rgba(0,230,118,0.15); color: #00e676; border: 1px solid #00e676; }
.badge-closed { background: rgba(255,82,82,0.15); color: #ff5252; border: 1px solid #ff5252; }
.badge-yes { background: rgba(0,194,255,0.15); color: #00c2ff; border: 1px solid #00c2ff; }
.badge-no { background: rgba(123,47,255,0.15); color: #b388ff; border: 1px solid #b388ff; }

/* Sidebar */
.stSidebar { background: #060c18 !important; }
.stSidebar .block-container { padding: 1rem; }

/* Section headers */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #00c2ff;
    border-bottom: 1px solid #1a3a6b;
    padding-bottom: 0.5rem;
    margin: 1.2rem 0 0.8rem;
    letter-spacing: 0.05em;
}

/* Wallet badge */
.wallet-badge {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: #4a7fb5;
    background: #0a1628;
    border: 1px solid #1a3a6b;
    border-radius: 4px;
    padding: 0.15rem 0.4rem;
}

/* Alerts */
.stAlert { border-radius: 8px; }

/* Refresh indicator */
.refresh-info {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #4a7fb5;
    text-align: right;
}

/* Streamlit overrides */
div[data-testid="stMetric"] {
    background: #0d1929;
    border: 1px solid #1a3a6b;
    border-radius: 10px;
    padding: 1rem;
}
div[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    color: #e2e8f0 !important;
}
div[data-testid="stMetricDelta"] { font-family: 'Space Mono', monospace; font-size: 0.75rem; }
div[data-testid="stMetricLabel"] {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem !important;
    color: #4a7fb5 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.stDataFrame { border: 1px solid #1a3a6b; border-radius: 8px; }
.stButton > button {
    background: linear-gradient(135deg, #00c2ff22, #7b2fff22);
    border: 1px solid #1a3a6b;
    color: #00c2ff;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    border-radius: 6px;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color: #00c2ff;
    background: linear-gradient(135deg, #00c2ff33, #7b2fff33);
}
</style>
""", unsafe_allow_html=True)


# ─── Constants ──────────────────────────────────────────────────────────────────
BASE_URL = "https://api.jup.ag/prediction/v1"
MICRO_USD = 1_000_000  # API returns micro-USD


# ─── API Helpers ────────────────────────────────────────────────────────────────
def get_headers(api_key: str) -> dict:
    return {"x-api-key": api_key, "Accept": "application/json"}


@st.cache_data(ttl=30)
def fetch_leaderboard(api_key: str, period: str = "all_time", limit: int = 20) -> dict:
    """Fetch top traders leaderboard."""
    try:
        # Jupiter leaderboard endpoint (beta)
        url = f"{BASE_URL}/leaderboard"
        params = {"period": period, "limit": limit}
        r = requests.get(url, headers=get_headers(api_key), params=params, timeout=10)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        # Fallback: try profiles/leaderboard path
        url2 = f"{BASE_URL}/profiles/leaderboard"
        r2 = requests.get(url2, headers=get_headers(api_key), params=params, timeout=10)
        if r2.status_code == 200:
            return {"ok": True, "data": r2.json()}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@st.cache_data(ttl=15)
def fetch_events(api_key: str, category: str = "crypto", status: str = "open") -> dict:
    """Fetch prediction market events."""
    try:
        url = f"{BASE_URL}/events"
        params = {"category": category, "status": status, "limit": 50}
        r = requests.get(url, headers=get_headers(api_key), params=params, timeout=10)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@st.cache_data(ttl=15)
def fetch_trader_positions(api_key: str, wallet: str) -> dict:
    """Fetch positions for a wallet address."""
    try:
        url = f"{BASE_URL}/positions"
        params = {"ownerPubkey": wallet}
        r = requests.get(url, headers=get_headers(api_key), params=params, timeout=10)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@st.cache_data(ttl=15)
def fetch_trader_profile(api_key: str, wallet: str) -> dict:
    """Fetch profile/stats for a wallet."""
    try:
        url = f"{BASE_URL}/profiles/{wallet}"
        r = requests.get(url, headers=get_headers(api_key), timeout=10)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def fmt_usd(micro_usd) -> str:
    """Convert micro-USD to formatted dollar string."""
    try:
        val = float(micro_usd) / MICRO_USD
        if abs(val) >= 1000:
            return f"${val:,.0f}"
        return f"${val:.2f}"
    except Exception:
        return "—"


def fmt_pct(val) -> str:
    try:
        return f"{float(val):.1f}%"
    except Exception:
        return "—"


def shorten_wallet(wallet: str) -> str:
    if not wallet or len(wallet) < 8:
        return wallet
    return f"{wallet[:5]}…{wallet[-4:]}"


def parse_pnl(pos: dict) -> float:
    """Extract PnL in USD from position dict."""
    try:
        return float(pos.get("pnlUsd", pos.get("unrealizedPnlUsd", 0))) / MICRO_USD
    except Exception:
        return 0.0


def parse_value(pos: dict) -> float:
    try:
        return float(pos.get("valueUsd", 0)) / MICRO_USD
    except Exception:
        return 0.0


# ─── DEMO DATA (used when no API key / endpoints return errors) ──────────────
def get_demo_leaderboard() -> list[dict]:
    """Return realistic-looking demo leaderboard data."""
    import random
    random.seed(42)
    wallets = [
        "9kJFaB3xYqL2nRTmPdWe8vHcZ5sU1oAGbKVfN4DiXyCq",
        "3mQpRw7NsJL9YhKbXtAeZc4FvGdU6iBWoCrPy2MnTgEk",
        "BxL4qK9pNmR2jHtZe7YfWsAc3DiVoGbUyCu5MrPnXwQJ",
        "7vFtNq8kRmP3sHwZe2YbXcAu4DiVoGjLyCr5MrPnXwQK",
        "EmR5sN9kPmQ4tHwZe6YcXbAu3DiVoGjLyCr5MrPnXwQL",
        "FkT6tP1mQnR5uHwZe8YdXcAv4EiWoHkMzDs6NsPqYxRM",
        "GlU7uQ2nRoS6vIxAf9ZeYeXbBw5FjXpInEt7OtQrZySN",
        "HmV8vR3oSpT7wJyBg1AfZfYfYcCx6GkYqJoFu8PuRazTO",
        "InW9wS4pTqU8xKzCh2BgAfZgZdDy7HlZrKpGv9QvSbaUP",
        "JoX1xT5qUrV9yLaDi3ChBgAhAeEz8ImAsLqHw1RwTcbVQ",
        "KpY2yU6rVsW1zMbEj4DiChBiBfFa9JnBtMrIx2SxUdcWR",
        "LqZ3zV7sSuX2aNcFk5EjDiCjCgGb1KoCuNsJy3TyVedXS",
        "MrA4AU8tTvY3bOdGl6FkEjDkDhHc2LpDvOtKz4UzWfeYT",
        "NsB5BV9uUwZ4cPeHm7GlFlElEiId3MqEwPuL15VAXgfZU",
        "OtC6CW1vVxA5dQfIn8HmGmFmFjJe4NrFxQvM26WBYhgAV",
        "PuD7DX2wWyB6eRgJo9InHnGnGkKf5OsGzRwN37XCZihBW",
        "QvE8EY3xXzC7fShKp1JoIoHoHlLg6PtHASxO48YDajcCX",
        "RwF9FZ4yYAD8gTiLq2KpJpIpImMh7QuIBTyP59ZEbkdDY",
        "SxG1GA5zZBE9hUjMr3LqKqJqJnNi8RvJCUzQ61AFcleCZ",
        "TyH2HB6AAF1iVkNs4MrLrKrKoOj9SwKDVAR72BGdmfDA1",
    ]
    data = []
    for i, wallet in enumerate(wallets):
        pnl = random.uniform(1800, 45000) if i < 10 else random.uniform(500, 1800)
        vol = pnl * random.uniform(3, 12)
        win_rate = random.uniform(52, 78) if i < 5 else random.uniform(44, 65)
        trades = random.randint(20, 350)
        data.append({
            "rank": i + 1,
            "wallet": wallet,
            "displayName": f"Trader_{wallet[:6]}",
            "totalPnlUsd": pnl * MICRO_USD,
            "totalVolumeUsd": vol * MICRO_USD,
            "winRate": win_rate,
            "totalTrades": trades,
            "openPositions": random.randint(1, 12),
        })
    return data


def get_demo_events() -> list[dict]:
    """Return realistic crypto prediction market events."""
    now = int(time.time())
    return [
        {
            "id": "ev_btc_5m_001",
            "title": "BTC 5-Min Price",
            "subtitle": "Will BTC be higher in 5 minutes?",
            "category": "crypto",
            "subcategory": "5min",
            "status": "open",
            "markets": [{
                "id": "mkt_btc_5m_yes",
                "title": "BTC UP in 5 min",
                "status": "open",
                "result": None,
                "yesBuyPrice": 510000,
                "noBuyPrice": 490000,
                "volumeUsd": 48200 * MICRO_USD,
                "openInterestUsd": 12400 * MICRO_USD,
                "liquidityUsd": 8900 * MICRO_USD,
            }],
            "totalVolumeUsd": 48200 * MICRO_USD,
            "closeTime": now + 240,
        },
        {
            "id": "ev_sol_5m_002",
            "title": "SOL 5-Min Price",
            "subtitle": "Will SOL be higher in 5 minutes?",
            "category": "crypto",
            "subcategory": "5min",
            "status": "open",
            "markets": [{
                "id": "mkt_sol_5m_yes",
                "title": "SOL UP in 5 min",
                "status": "open",
                "result": None,
                "yesBuyPrice": 480000,
                "noBuyPrice": 520000,
                "volumeUsd": 31700 * MICRO_USD,
                "openInterestUsd": 9200 * MICRO_USD,
                "liquidityUsd": 5600 * MICRO_USD,
            }],
            "totalVolumeUsd": 31700 * MICRO_USD,
            "closeTime": now + 180,
        },
        {
            "id": "ev_eth_5m_003",
            "title": "ETH 5-Min Price",
            "subtitle": "Will ETH be higher in 5 minutes?",
            "category": "crypto",
            "subcategory": "5min",
            "status": "open",
            "markets": [{
                "id": "mkt_eth_5m_yes",
                "title": "ETH UP in 5 min",
                "status": "open",
                "result": None,
                "yesBuyPrice": 560000,
                "noBuyPrice": 440000,
                "volumeUsd": 22900 * MICRO_USD,
                "openInterestUsd": 6700 * MICRO_USD,
                "liquidityUsd": 4200 * MICRO_USD,
            }],
            "totalVolumeUsd": 22900 * MICRO_USD,
            "closeTime": now + 310,
        },
        {
            "id": "ev_btc_15m_004",
            "title": "BTC 15-Min Price",
            "subtitle": "Will BTC be higher in 15 minutes?",
            "category": "crypto",
            "subcategory": "15min",
            "status": "open",
            "markets": [{
                "id": "mkt_btc_15m_yes",
                "title": "BTC UP in 15 min",
                "status": "open",
                "result": None,
                "yesBuyPrice": 530000,
                "noBuyPrice": 470000,
                "volumeUsd": 89400 * MICRO_USD,
                "openInterestUsd": 28700 * MICRO_USD,
                "liquidityUsd": 19300 * MICRO_USD,
            }],
            "totalVolumeUsd": 89400 * MICRO_USD,
            "closeTime": now + 780,
        },
        {
            "id": "ev_sol_15m_005",
            "title": "SOL 15-Min Price",
            "subtitle": "Will SOL be higher in 15 minutes?",
            "category": "crypto",
            "subcategory": "15min",
            "status": "open",
            "markets": [{
                "id": "mkt_sol_15m_yes",
                "title": "SOL UP in 15 min",
                "status": "open",
                "result": None,
                "yesBuyPrice": 490000,
                "noBuyPrice": 510000,
                "volumeUsd": 52100 * MICRO_USD,
                "openInterestUsd": 17200 * MICRO_USD,
                "liquidityUsd": 11400 * MICRO_USD,
            }],
            "totalVolumeUsd": 52100 * MICRO_USD,
            "closeTime": now + 650,
        },
        {
            "id": "ev_eth_15m_006",
            "title": "ETH 15-Min Price",
            "subtitle": "Will ETH be higher in 15 minutes?",
            "category": "crypto",
            "subcategory": "15min",
            "status": "open",
            "markets": [{
                "id": "mkt_eth_15m_yes",
                "title": "ETH UP in 15 min",
                "status": "open",
                "result": None,
                "yesBuyPrice": 545000,
                "noBuyPrice": 455000,
                "volumeUsd": 38800 * MICRO_USD,
                "openInterestUsd": 13500 * MICRO_USD,
                "liquidityUsd": 8900 * MICRO_USD,
            }],
            "totalVolumeUsd": 38800 * MICRO_USD,
            "closeTime": now + 720,
        },
        {
            "id": "ev_btc_daily_007",
            "title": "BTC Daily Close",
            "subtitle": "Will BTC close above $108,000 today?",
            "category": "crypto",
            "subcategory": "daily",
            "status": "open",
            "markets": [{
                "id": "mkt_btc_daily_yes",
                "title": "BTC > $108K EOD",
                "status": "open",
                "result": None,
                "yesBuyPrice": 620000,
                "noBuyPrice": 380000,
                "volumeUsd": 312000 * MICRO_USD,
                "openInterestUsd": 98000 * MICRO_USD,
                "liquidityUsd": 67000 * MICRO_USD,
            }],
            "totalVolumeUsd": 312000 * MICRO_USD,
            "closeTime": now + 36000,
        },
        {
            "id": "ev_sol_daily_008",
            "title": "SOL Daily Close",
            "subtitle": "Will SOL close above $175 today?",
            "category": "crypto",
            "subcategory": "daily",
            "status": "open",
            "markets": [{
                "id": "mkt_sol_daily_yes",
                "title": "SOL > $175 EOD",
                "status": "open",
                "result": None,
                "yesBuyPrice": 430000,
                "noBuyPrice": 570000,
                "volumeUsd": 187000 * MICRO_USD,
                "openInterestUsd": 56000 * MICRO_USD,
                "liquidityUsd": 38000 * MICRO_USD,
            }],
            "totalVolumeUsd": 187000 * MICRO_USD,
            "closeTime": now + 36200,
        },
        {
            "id": "ev_jup_daily_009",
            "title": "JUP Daily Close",
            "subtitle": "Will JUP close above $0.25 today?",
            "category": "crypto",
            "subcategory": "daily",
            "status": "open",
            "markets": [{
                "id": "mkt_jup_daily_yes",
                "title": "JUP > $0.25 EOD",
                "status": "open",
                "result": None,
                "yesBuyPrice": 380000,
                "noBuyPrice": 620000,
                "volumeUsd": 94000 * MICRO_USD,
                "openInterestUsd": 31000 * MICRO_USD,
                "liquidityUsd": 21000 * MICRO_USD,
            }],
            "totalVolumeUsd": 94000 * MICRO_USD,
            "closeTime": now + 36400,
        },
    ]


# ─── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:0.8rem 0;'>
        <div style='font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;
             background:linear-gradient(135deg,#00c2ff,#7b2fff);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            🔮 JUP PREDICT
        </div>
        <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a7fb5;
             text-transform:uppercase;letter-spacing:0.1em;margin-top:0.2rem;'>
            Tracker Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # API Key input
    st.markdown("**🔑 Jupiter API Key**")
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="Get free key at portal.jup.ag",
        label_visibility="collapsed",
        help="Get your free API key at https://portal.jup.ag — required for live data"
    )

    demo_mode = not bool(api_key)
    if demo_mode:
        st.info("🟡 **Demo Mode** — showing simulated data.\nEnter your API key from [portal.jup.ag](https://portal.jup.ag) for live data.")
    else:
        st.success("🟢 **Live Mode** — connected to Jupiter API")

    st.divider()

    st.markdown("**⚙️ Settings**")
    leaderboard_period = st.selectbox(
        "Leaderboard Period",
        ["all_time", "30d", "7d", "24h"],
        format_func=lambda x: {"all_time": "All Time", "30d": "30 Days", "7d": "7 Days", "24h": "24 Hours"}[x]
    )

    top_n = st.slider("Top N Traders", 5, 20, 20)

    auto_refresh = st.toggle("Auto Refresh (30s)", value=False)

    market_filter = st.multiselect(
        "Market Timeframes",
        ["5min", "15min", "daily", "other"],
        default=["5min", "15min", "daily"]
    )

    st.divider()

    # Wallet tracker
    st.markdown("**🔭 Wallet Tracker**")
    tracked_wallet = st.text_input(
        "Track Wallet",
        placeholder="Solana public key…",
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#2a4f7a;text-align:center;'>
        Data via Jupiter Prediction API<br>
        <a href='https://developers.jup.ag/docs/prediction' target='_blank' 
           style='color:#00c2ff;text-decoration:none;'>API Docs ↗</a>
        &nbsp;|&nbsp;
        <a href='https://portal.jup.ag' target='_blank'
           style='color:#00c2ff;text-decoration:none;'>Get API Key ↗</a>
    </div>
    """, unsafe_allow_html=True)


# ─── Auto Refresh ────────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(0.1)
    st.rerun()


# ─── Header ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='dash-header'>
    <div class='dash-title'>🔮 Jupiter Prediction Markets Tracker</div>
    <div class='dash-sub'>Top 20 Most Profitable Traders · Live Crypto Markets · Solana On-Chain</div>
</div>
""", unsafe_allow_html=True)

# Last updated
col_ts, col_refresh = st.columns([5, 1])
with col_ts:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f"<div class='refresh-info'>Last updated: {now_str} {'· Demo Mode' if demo_mode else '· Live'}</div>", unsafe_allow_html=True)
with col_refresh:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()


# ─── Load Data ───────────────────────────────────────────────────────────────────
with st.spinner("Loading market data…"):
    if demo_mode:
        raw_lb = get_demo_leaderboard()
        raw_events = get_demo_events()
        lb_error = None
        ev_error = None
    else:
        lb_resp = fetch_leaderboard(api_key, leaderboard_period, top_n)
        ev_resp = fetch_events(api_key, "crypto", "open")

        if lb_resp["ok"]:
            raw_data = lb_resp["data"]
            # Handle various response shapes
            if isinstance(raw_data, list):
                raw_lb = raw_data
            elif isinstance(raw_data, dict):
                raw_lb = raw_data.get("data", raw_data.get("traders", raw_data.get("users", [])))
            else:
                raw_lb = []
            lb_error = None if raw_lb else "No leaderboard data returned — API may be evolving."
        else:
            raw_lb = get_demo_leaderboard()  # fallback to demo
            lb_error = lb_resp["error"]

        if ev_resp["ok"]:
            raw_ev_data = ev_resp["data"]
            if isinstance(raw_ev_data, list):
                raw_events = raw_ev_data
            elif isinstance(raw_ev_data, dict):
                raw_events = raw_ev_data.get("data", raw_ev_data.get("events", []))
            else:
                raw_events = []
            ev_error = None
        else:
            raw_events = get_demo_events()  # fallback to demo
            ev_error = ev_resp["error"]


# ─── API Error Notices ───────────────────────────────────────────────────────────
if not demo_mode:
    if lb_error:
        st.warning(f"⚠️ Leaderboard API: {lb_error} — showing demo data as fallback.")
    if ev_error:
        st.warning(f"⚠️ Events API: {ev_error} — showing demo data as fallback.")


# ─── TAB LAYOUT ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Top 20 Traders",
    "📈 Live Markets",
    "🔭 Wallet Tracker",
    "📊 Analytics"
])


# ════════════════════════════════════════════════════════════════════
# TAB 1: LEADERBOARD
# ════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-title'>🏆 TOP 20 MOST PROFITABLE TRADERS</div>", unsafe_allow_html=True)

    if not raw_lb:
        st.error("No leaderboard data available.")
    else:
        # Build DataFrame
        rows = []
        for i, t in enumerate(raw_lb[:top_n]):
            rank = t.get("rank", i + 1)
            wallet = t.get("wallet", t.get("ownerPubkey", t.get("pubkey", "Unknown")))
            pnl_micro = t.get("totalPnlUsd", t.get("pnlUsd", 0))
            vol_micro = t.get("totalVolumeUsd", t.get("volumeUsd", 0))
            win_rate = t.get("winRate", t.get("winRatePct", 0))
            trades = t.get("totalTrades", t.get("tradeCount", 0))
            open_pos = t.get("openPositions", t.get("openPositionCount", "—"))

            pnl_usd = float(pnl_micro) / MICRO_USD if pnl_micro else 0
            vol_usd = float(vol_micro) / MICRO_USD if vol_micro else 0

            rows.append({
                "Rank": rank,
                "Wallet": shorten_wallet(wallet),
                "Full Wallet": wallet,
                "Total PnL": pnl_usd,
                "Volume": vol_usd,
                "Win Rate": float(win_rate) if win_rate else 0,
                "Trades": int(trades) if trades else 0,
                "Open Positions": open_pos,
            })

        df_lb = pd.DataFrame(rows)

        # Summary metrics
        total_pnl = df_lb["Total PnL"].sum()
        avg_win = df_lb["Win Rate"].mean()
        top_pnl = df_lb["Total PnL"].max()
        total_vol = df_lb["Volume"].sum()

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Combined PnL (Top 20)", f"${total_pnl:,.0f}")
        with m2:
            st.metric("Avg Win Rate", f"{avg_win:.1f}%")
        with m3:
            st.metric("#1 Trader PnL", f"${top_pnl:,.0f}")
        with m4:
            st.metric("Total Volume", f"${total_vol:,.0f}")

        st.markdown("---")

        # Styled leaderboard table
        display_df = df_lb[["Rank", "Wallet", "Total PnL", "Volume", "Win Rate", "Trades", "Open Positions"]].copy()
        display_df["Total PnL"] = display_df["Total PnL"].apply(lambda x: f"${x:,.2f}")
        display_df["Volume"] = display_df["Volume"].apply(lambda x: f"${x:,.0f}")
        display_df["Win Rate"] = display_df["Win Rate"].apply(lambda x: f"{x:.1f}%")

        # Color-code by rank
        def rank_icon(r):
            if r == 1: return "🥇"
            if r == 2: return "🥈"
            if r == 3: return "🥉"
            return f"#{r}"

        display_df["Rank"] = display_df["Rank"].apply(rank_icon)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=560,
            column_config={
                "Rank": st.column_config.TextColumn("Rank", width=60),
                "Wallet": st.column_config.TextColumn("Wallet", width=120),
                "Total PnL": st.column_config.TextColumn("Total PnL", width=110),
                "Volume": st.column_config.TextColumn("Volume", width=110),
                "Win Rate": st.column_config.TextColumn("Win Rate", width=90),
                "Trades": st.column_config.NumberColumn("Trades", width=80),
                "Open Positions": st.column_config.TextColumn("Open", width=70),
            },
            hide_index=True,
        )

        # Bar chart: PnL by rank
        st.markdown("<div class='section-title'>📊 PnL Distribution</div>", unsafe_allow_html=True)
        fig_bar = px.bar(
            df_lb.head(20),
            x="Wallet",
            y="Total PnL",
            color="Total PnL",
            color_continuous_scale=[[0, "#7b2fff"], [0.5, "#00c2ff"], [1, "#00e676"]],
            labels={"Total PnL": "PnL (USD)", "Wallet": ""},
            template="plotly_dark",
        )
        fig_bar.update_layout(
            paper_bgcolor="#080c14",
            plot_bgcolor="#0d1929",
            font=dict(family="Space Mono, monospace", color="#4a7fb5"),
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=20, b=60),
            height=300,
            xaxis=dict(tickangle=-30, gridcolor="#1a3a6b"),
            yaxis=dict(gridcolor="#1a3a6b"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Win Rate vs PnL scatter
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            fig_scatter = px.scatter(
                df_lb,
                x="Win Rate",
                y="Total PnL",
                size="Trades",
                color="Total PnL",
                hover_name="Wallet",
                color_continuous_scale=[[0, "#7b2fff"], [1, "#00e676"]],
                labels={"Win Rate": "Win Rate (%)", "Total PnL": "PnL (USD)"},
                template="plotly_dark",
                title="Win Rate vs PnL (bubble = trade count)"
            )
            fig_scatter.update_layout(
                paper_bgcolor="#080c14",
                plot_bgcolor="#0d1929",
                font=dict(family="Space Mono, monospace", color="#4a7fb5"),
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=40, b=10),
                height=280,
                xaxis=dict(gridcolor="#1a3a6b"),
                yaxis=dict(gridcolor="#1a3a6b"),
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col_s2:
            fig_vol = px.bar(
                df_lb.head(10),
                x="Wallet",
                y="Volume",
                color="Win Rate",
                color_continuous_scale=[[0, "#7b2fff"], [1, "#00e676"]],
                labels={"Volume": "Volume (USD)", "Wallet": ""},
                template="plotly_dark",
                title="Top 10 by Volume (colored = win rate)"
            )
            fig_vol.update_layout(
                paper_bgcolor="#080c14",
                plot_bgcolor="#0d1929",
                font=dict(family="Space Mono, monospace", color="#4a7fb5"),
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=40, b=60),
                height=280,
                xaxis=dict(tickangle=-30, gridcolor="#1a3a6b"),
                yaxis=dict(gridcolor="#1a3a6b"),
            )
            st.plotly_chart(fig_vol, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# TAB 2: LIVE MARKETS
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-title'>📈 LIVE CRYPTO PREDICTION MARKETS</div>", unsafe_allow_html=True)

    if not raw_events:
        st.error("No live market events available.")
    else:
        now_ts = int(time.time())

        # Filter by selected timeframes
        def get_timeframe(ev):
            sub = ev.get("subcategory", "").lower()
            title = ev.get("title", "").lower()
            if "5" in sub or "5min" in sub or "5 min" in title:
                return "5min"
            if "15" in sub or "15min" in sub or "15 min" in title:
                return "15min"
            if "daily" in sub or "daily" in title or "eod" in title or "close" in title:
                return "daily"
            return "other"

        events_with_tf = [(ev, get_timeframe(ev)) for ev in raw_events]

        # Group by timeframe
        groups = {"5min": [], "15min": [], "daily": [], "other": []}
        for ev, tf in events_with_tf:
            if tf in groups:
                groups[tf].append(ev)

        tf_labels = {
            "5min": "⚡ 5-Minute Markets",
            "15min": "🕐 15-Minute Markets",
            "daily": "📅 Daily Markets",
            "other": "🌐 Other Crypto Markets"
        }

        for tf in ["5min", "15min", "daily", "other"]:
            if tf not in market_filter:
                continue
            evs = groups[tf]
            if not evs:
                continue

            st.markdown(f"<div class='section-title'>{tf_labels[tf]}</div>", unsafe_allow_html=True)

            cols = st.columns(min(len(evs), 3))
            for i, ev in enumerate(evs):
                col = cols[i % 3]
                with col:
                    markets = ev.get("markets", [])
                    mkt = markets[0] if markets else {}
                    yes_price = float(mkt.get("yesBuyPrice", 500000)) / MICRO_USD
                    no_price = float(mkt.get("noBuyPrice", 500000)) / MICRO_USD
                    volume = float(ev.get("totalVolumeUsd", 0)) / MICRO_USD
                    oi = float(mkt.get("openInterestUsd", 0)) / MICRO_USD
                    liq = float(mkt.get("liquidityUsd", 0)) / MICRO_USD

                    close_ts = ev.get("closeTime", 0)
                    if close_ts:
                        secs_left = close_ts - now_ts
                        if secs_left > 3600:
                            time_left = f"{secs_left // 3600}h {(secs_left % 3600) // 60}m"
                        elif secs_left > 60:
                            time_left = f"{secs_left // 60}m {secs_left % 60}s"
                        else:
                            time_left = f"{max(0, secs_left)}s"
                    else:
                        time_left = "—"

                    # Direction signal
                    yes_pct = yes_price * 100
                    direction = "🟢 YES FAVORED" if yes_pct > 50 else "🔴 NO FAVORED"
                    direction_color = "#00e676" if yes_pct > 50 else "#ff5252"

                    st.markdown(f"""
                    <div style='background:#0d1929;border:1px solid #1a3a6b;border-radius:10px;
                         padding:1rem;margin-bottom:0.8rem;'>
                        <div style='font-family:Syne,sans-serif;font-weight:700;font-size:0.95rem;
                             color:#e2e8f0;margin-bottom:0.2rem;'>{ev.get('title','—')}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#4a7fb5;
                             margin-bottom:0.7rem;'>{ev.get('subtitle','')}</div>
                        <div style='display:flex;justify-content:space-between;margin-bottom:0.6rem;'>
                            <div style='text-align:center;flex:1;'>
                                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a7fb5;'>YES</div>
                                <div style='font-family:Syne,sans-serif;font-weight:800;font-size:1.2rem;color:#00c2ff;'>{yes_pct:.0f}¢</div>
                            </div>
                            <div style='text-align:center;flex:1;'>
                                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a7fb5;'>NO</div>
                                <div style='font-family:Syne,sans-serif;font-weight:800;font-size:1.2rem;color:#b388ff;'>{no_price*100:.0f}¢</div>
                            </div>
                            <div style='text-align:center;flex:1;'>
                                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a7fb5;'>CLOSES</div>
                                <div style='font-family:Space Mono,monospace;font-size:0.75rem;color:#e2e8f0;'>{time_left}</div>
                            </div>
                        </div>
                        <div style='background:#060c18;border-radius:6px;padding:0.5rem;
                             display:flex;justify-content:space-between;margin-bottom:0.5rem;'>
                            <div>
                                <div style='font-family:Space Mono,monospace;font-size:0.55rem;color:#4a7fb5;'>VOL</div>
                                <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#e2e8f0;'>${volume:,.0f}</div>
                            </div>
                            <div>
                                <div style='font-family:Space Mono,monospace;font-size:0.55rem;color:#4a7fb5;'>OI</div>
                                <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#e2e8f0;'>${oi:,.0f}</div>
                            </div>
                            <div>
                                <div style='font-family:Space Mono,monospace;font-size:0.55rem;color:#4a7fb5;'>LIQ</div>
                                <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#e2e8f0;'>${liq:,.0f}</div>
                            </div>
                        </div>
                        <div style='font-family:Space Mono,monospace;font-size:0.65rem;
                             color:{direction_color};text-align:center;'>{direction}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Summary table
        st.markdown("<div class='section-title'>📋 All Crypto Markets Summary</div>", unsafe_allow_html=True)
        ev_rows = []
        for ev, tf in events_with_tf:
            mkt = ev.get("markets", [{}])[0]
            yes_p = float(mkt.get("yesBuyPrice", 500000)) / MICRO_USD
            vol = float(ev.get("totalVolumeUsd", 0)) / MICRO_USD
            oi = float(mkt.get("openInterestUsd", 0)) / MICRO_USD
            close_ts = ev.get("closeTime", 0)
            secs = close_ts - now_ts if close_ts else 0
            if secs > 3600:
                tl = f"{secs // 3600}h {(secs % 3600) // 60}m"
            elif secs > 0:
                tl = f"{secs // 60}m"
            else:
                tl = "Closing"
            ev_rows.append({
                "Timeframe": tf,
                "Market": ev.get("title", "—"),
                "YES Price": f"{yes_p * 100:.0f}¢",
                "NO Price": f"{(1 - yes_p) * 100:.0f}¢",
                "Volume": f"${vol:,.0f}",
                "Open Interest": f"${oi:,.0f}",
                "Closes In": tl,
                "Signal": "YES" if yes_p > 0.5 else "NO",
            })

        df_ev = pd.DataFrame(ev_rows)
        st.dataframe(
            df_ev,
            use_container_width=True,
            height=350,
            column_config={
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "Timeframe": st.column_config.TextColumn("TF", width=70),
            },
            hide_index=True,
        )


# ════════════════════════════════════════════════════════════════════
# TAB 3: WALLET TRACKER
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-title'>🔭 WALLET POSITION TRACKER</div>", unsafe_allow_html=True)

    # Quick-click top traders
    if raw_lb:
        st.markdown("**Quick load a top trader:**")
        quick_cols = st.columns(5)
        for i, t in enumerate(raw_lb[:5]):
            w = t.get("wallet", t.get("ownerPubkey", t.get("pubkey", "")))
            with quick_cols[i]:
                rank_icon_str = ["🥇", "🥈", "🥉", "#4", "#5"][i]
                if st.button(f"{rank_icon_str} {shorten_wallet(w)}", key=f"qw_{i}"):
                    st.session_state["tracked_wallet"] = w

    wallet_to_track = st.session_state.get("tracked_wallet", tracked_wallet)

    if wallet_to_track:
        st.markdown(f"""
        <div style='background:#0d1929;border:1px solid #1a3a6b;border-radius:8px;
             padding:0.6rem 1rem;margin:0.8rem 0;font-family:Space Mono,monospace;font-size:0.75rem;color:#4a7fb5;'>
            Tracking: <span style='color:#00c2ff;'>{wallet_to_track}</span>
        </div>
        """, unsafe_allow_html=True)

        if demo_mode:
            # Demo positions
            import random
            random.seed(hash(wallet_to_track) % 1000)
            demo_positions = []
            market_names = [
                "BTC UP in 5 min", "SOL UP in 15 min", "ETH UP in 15 min",
                "BTC > $108K EOD", "SOL > $175 EOD", "JUP > $0.25 EOD"
            ]
            for j in range(random.randint(2, 6)):
                cost = random.uniform(100, 5000) * MICRO_USD
                pnl = random.uniform(-200, 1500) * MICRO_USD
                val = cost + pnl
                demo_positions.append({
                    "market": random.choice(market_names),
                    "side": random.choice(["YES", "NO"]),
                    "contracts": random.randint(10, 500),
                    "totalCostUsd": cost,
                    "valueUsd": val,
                    "pnlUsd": pnl,
                    "status": "active",
                })
            positions = demo_positions
            pos_error = None
        else:
            pos_resp = fetch_trader_positions(api_key, wallet_to_track)
            if pos_resp["ok"]:
                raw_pos = pos_resp["data"]
                positions = raw_pos.get("data", raw_pos) if isinstance(raw_pos, dict) else raw_pos
                pos_error = None
            else:
                positions = []
                pos_error = pos_resp["error"]
                st.error(f"Could not fetch positions: {pos_error}")

        if positions:
            total_val = sum(float(p.get("valueUsd", 0)) / MICRO_USD for p in positions)
            total_cost = sum(float(p.get("totalCostUsd", 0)) / MICRO_USD for p in positions)
            total_pnl = total_val - total_cost
            pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0

            pw1, pw2, pw3, pw4 = st.columns(4)
            with pw1:
                st.metric("Positions", len(positions))
            with pw2:
                st.metric("Portfolio Value", f"${total_val:,.2f}")
            with pw3:
                st.metric("Total Cost", f"${total_cost:,.2f}")
            with pw4:
                pnl_str = f"${total_pnl:+,.2f}"
                st.metric("Unrealized PnL", pnl_str, f"{pnl_pct:+.1f}%")

            st.markdown("---")
            st.markdown("**Open Positions**")
            pos_rows = []
            for p in positions:
                market_name = p.get("market", p.get("marketTitle", p.get("marketId", "—")))
                side = p.get("side", "—")
                contracts = p.get("contracts", "—")
                cost = float(p.get("totalCostUsd", 0)) / MICRO_USD
                val = float(p.get("valueUsd", 0)) / MICRO_USD
                pnl = val - cost
                pnl_pct_pos = (pnl / cost * 100) if cost else 0

                pos_rows.append({
                    "Market": market_name if isinstance(market_name, str) else str(market_name)[:40],
                    "Side": str(side).upper(),
                    "Contracts": contracts,
                    "Cost": f"${cost:.2f}",
                    "Value": f"${val:.2f}",
                    "PnL": f"${pnl:+.2f}",
                    "PnL %": f"{pnl_pct_pos:+.1f}%",
                    "Status": p.get("status", "active").title(),
                })

            df_pos = pd.DataFrame(pos_rows)
            st.dataframe(df_pos, use_container_width=True, hide_index=True, height=300)

            # PnL donut
            if len(pos_rows) > 1:
                pnl_vals = [float(p.get("valueUsd", 0)) / MICRO_USD for p in positions]
                labels_p = [str(p.get("market", p.get("marketId", f"Pos {i}")))[:25] for i, p in enumerate(positions)]
                fig_donut = go.Figure(data=[go.Pie(
                    labels=labels_p,
                    values=pnl_vals,
                    hole=0.55,
                    marker=dict(colors=px.colors.sequential.Plasma),
                )])
                fig_donut.update_layout(
                    paper_bgcolor="#080c14",
                    font=dict(family="Space Mono, monospace", color="#4a7fb5"),
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=280,
                    showlegend=True,
                    legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
                    title=dict(text="Portfolio Allocation", font=dict(color="#4a7fb5", size=12)),
                )
                st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No open positions found for this wallet.")
    else:
        st.info("Enter a Solana wallet address in the sidebar, or click a quick-load button above.")


# ════════════════════════════════════════════════════════════════════
# TAB 4: ANALYTICS
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-title'>📊 MARKET ANALYTICS</div>", unsafe_allow_html=True)

    if raw_events:
        # Volume by timeframe
        vol_by_tf = {"5min": 0, "15min": 0, "daily": 0, "other": 0}
        oi_by_tf = {"5min": 0, "15min": 0, "daily": 0, "other": 0}
        for ev, tf in [(e, get_timeframe(e)) for e in raw_events]:
            vol_by_tf[tf] += float(ev.get("totalVolumeUsd", 0)) / MICRO_USD
            mkt = ev.get("markets", [{}])[0]
            oi_by_tf[tf] += float(mkt.get("openInterestUsd", 0)) / MICRO_USD

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            fig_tf_vol = px.bar(
                x=list(vol_by_tf.keys()),
                y=list(vol_by_tf.values()),
                color=list(vol_by_tf.values()),
                color_continuous_scale=[[0, "#7b2fff"], [1, "#00c2ff"]],
                labels={"x": "Timeframe", "y": "Volume (USD)"},
                title="Volume by Timeframe",
                template="plotly_dark",
            )
            fig_tf_vol.update_layout(
                paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono, monospace", color="#4a7fb5"),
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=40, b=10),
                height=280,
                xaxis=dict(gridcolor="#1a3a6b"),
                yaxis=dict(gridcolor="#1a3a6b"),
            )
            st.plotly_chart(fig_tf_vol, use_container_width=True)

        with col_a2:
            fig_tf_oi = px.bar(
                x=list(oi_by_tf.keys()),
                y=list(oi_by_tf.values()),
                color=list(oi_by_tf.values()),
                color_continuous_scale=[[0, "#b388ff"], [1, "#00e676"]],
                labels={"x": "Timeframe", "y": "Open Interest (USD)"},
                title="Open Interest by Timeframe",
                template="plotly_dark",
            )
            fig_tf_oi.update_layout(
                paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono, monospace", color="#4a7fb5"),
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=40, b=10),
                height=280,
                xaxis=dict(gridcolor="#1a3a6b"),
                yaxis=dict(gridcolor="#1a3a6b"),
            )
            st.plotly_chart(fig_tf_oi, use_container_width=True)

        # Sentiment gauge from YES prices
        st.markdown("<div class='section-title'>🧠 Market Sentiment (YES Price Probabilities)</div>", unsafe_allow_html=True)
        sent_rows = []
        for ev in raw_events:
            mkt = ev.get("markets", [{}])[0]
            yes_p = float(mkt.get("yesBuyPrice", 500000)) / MICRO_USD
            sent_rows.append({
                "Market": ev.get("title", "—")[:35],
                "YES %": yes_p * 100,
                "NO %": (1 - yes_p) * 100,
            })
        df_sent = pd.DataFrame(sent_rows)

        fig_sent = go.Figure()
        fig_sent.add_trace(go.Bar(
            name="YES",
            x=df_sent["Market"],
            y=df_sent["YES %"],
            marker_color="#00c2ff",
            opacity=0.85,
        ))
        fig_sent.add_trace(go.Bar(
            name="NO",
            x=df_sent["Market"],
            y=df_sent["NO %"],
            marker_color="#b388ff",
            opacity=0.85,
        ))
        fig_sent.update_layout(
            barmode="stack",
            paper_bgcolor="#080c14",
            plot_bgcolor="#0d1929",
            font=dict(family="Space Mono, monospace", color="#4a7fb5"),
            margin=dict(l=10, r=10, t=20, b=80),
            height=320,
            xaxis=dict(tickangle=-30, gridcolor="#1a3a6b"),
            yaxis=dict(gridcolor="#1a3a6b", title="Probability %"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0")),
        )
        fig_sent.add_hline(y=50, line_dash="dot", line_color="#4a7fb5", opacity=0.5)
        st.plotly_chart(fig_sent, use_container_width=True)

    # Leaderboard analytics
    if raw_lb:
        st.markdown("<div class='section-title'>🏆 Leaderboard Analytics</div>", unsafe_allow_html=True)
        df_lb2 = pd.DataFrame([{
            "rank": i + 1,
            "wallet": shorten_wallet(t.get("wallet", t.get("ownerPubkey", t.get("pubkey", f"Trader {i+1}")))),
            "pnl": float(t.get("totalPnlUsd", t.get("pnlUsd", 0))) / MICRO_USD,
            "winRate": float(t.get("winRate", t.get("winRatePct", 50))),
            "trades": int(t.get("totalTrades", t.get("tradeCount", 0))),
        } for i, t in enumerate(raw_lb[:top_n])])

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            fig_hist = px.histogram(
                df_lb2,
                x="winRate",
                nbins=10,
                color_discrete_sequence=["#00c2ff"],
                labels={"winRate": "Win Rate (%)"},
                title="Win Rate Distribution",
                template="plotly_dark",
            )
            fig_hist.update_layout(
                paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono, monospace", color="#4a7fb5"),
                margin=dict(l=10, r=10, t=40, b=10),
                height=260,
                xaxis=dict(gridcolor="#1a3a6b"),
                yaxis=dict(gridcolor="#1a3a6b"),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_b2:
            fig_trades = px.scatter(
                df_lb2,
                x="trades",
                y="pnl",
                color="winRate",
                size="pnl",
                size_max=40,
                hover_name="wallet",
                color_continuous_scale=[[0, "#7b2fff"], [1, "#00e676"]],
                labels={"trades": "Total Trades", "pnl": "PnL (USD)", "winRate": "Win %"},
                title="Trades vs PnL",
                template="plotly_dark",
            )
            fig_trades.update_layout(
                paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono, monospace", color="#4a7fb5"),
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=40, b=10),
                height=260,
                xaxis=dict(gridcolor="#1a3a6b"),
                yaxis=dict(gridcolor="#1a3a6b"),
            )
            st.plotly_chart(fig_trades, use_container_width=True)


# ─── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.65rem;color:#2a4f7a;padding:0.5rem;'>
    Jupiter Predict Tracker · Data via <a href='https://developers.jup.ag/docs/prediction' 
    target='_blank' style='color:#00c2ff;text-decoration:none;'>Jupiter Prediction API (Beta)</a> · 
    Not financial advice · 
    <a href='https://portal.jup.ag' target='_blank' style='color:#00c2ff;text-decoration:none;'>Get API Key</a>
</div>
""", unsafe_allow_html=True)
