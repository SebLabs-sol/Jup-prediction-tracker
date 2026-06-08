"""
Jupiter Prediction Markets Dashboard
Top 20 Most Profitable Traders + Live Crypto Markets
Powered by Jupiter Prediction API (Beta)
"""

import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Jupiter Predict Tracker",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── API Config (hardcoded) ──────────────────────────────────────────────────────
API_KEY  = "jup_2b063a134ea3e77044bfb421822a9e82668db0a0bc0b75ba0fbb4bea8e2b57a2"
BASE_URL = "https://api.jup.ag/prediction/v1"
MICRO    = 1_000_000  # 1,000,000 units = $1.00

HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
}

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #080c14; color: #e2e8f0; }
.main .block-container { padding-top: 1.2rem; max-width: 1400px; }

.dash-header {
    background: linear-gradient(135deg, #0f1929 0%, #0d1f3c 50%, #091525 100%);
    border: 1px solid #1a3a6b; border-radius: 12px;
    padding: 1.4rem 2rem; margin-bottom: 1.2rem; position: relative; overflow: hidden;
}
.dash-header::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #00c2ff, #7b2fff, #00c2ff);
    background-size: 200% 100%; animation: shimmer 3s linear infinite;
}
@keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
.dash-title {
    font-family:'Syne',sans-serif; font-size:1.9rem; font-weight:800;
    background:linear-gradient(135deg,#00c2ff,#7b2fff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;
}
.dash-sub {
    font-family:'Space Mono',monospace; font-size:0.72rem; color:#4a7fb5;
    margin-top:0.3rem; letter-spacing:0.1em; text-transform:uppercase;
}
.section-title {
    font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:#00c2ff;
    border-bottom:1px solid #1a3a6b; padding-bottom:0.4rem;
    margin:1.1rem 0 0.7rem; letter-spacing:0.05em;
}
.refresh-info {
    font-family:'Space Mono',monospace; font-size:0.62rem; color:#4a7fb5; text-align:right;
}
.market-card {
    background:#0d1929; border:1px solid #1a3a6b; border-radius:10px;
    padding:0.9rem; margin-bottom:0.7rem; transition:border-color 0.2s;
}
.market-card:hover { border-color:#00c2ff44; }

div[data-testid="stMetric"] {
    background:#0d1929; border:1px solid #1a3a6b; border-radius:10px; padding:0.9rem;
}
div[data-testid="stMetricValue"] {
    font-family:'Syne',sans-serif !important; font-weight:800; color:#e2e8f0 !important;
}
div[data-testid="stMetricLabel"] {
    font-family:'Space Mono',monospace !important; font-size:0.62rem !important;
    color:#4a7fb5 !important; text-transform:uppercase; letter-spacing:0.05em;
}
.stSidebar { background:#060c18 !important; }
.stButton > button {
    background:linear-gradient(135deg,#00c2ff11,#7b2fff11);
    border:1px solid #1a3a6b; color:#00c2ff;
    font-family:'Space Mono',monospace; font-size:0.72rem;
    border-radius:6px; transition:all 0.2s;
}
.stButton > button:hover { border-color:#00c2ff; background:linear-gradient(135deg,#00c2ff22,#7b2fff22); }
.stDataFrame { border:1px solid #1a3a6b; border-radius:8px; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────────
def usd(micro) -> float:
    try:    return float(micro) / MICRO
    except: return 0.0

def fmt_usd(micro, decimals=2) -> str:
    v = usd(micro)
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:     return f"${v:,.0f}"
    return f"${v:,.{decimals}f}"

def shorten(w: str) -> str:
    if not w or len(w) < 10: return w or "—"
    return f"{w[:5]}…{w[-4:]}"

def win_rate(correct, total) -> float:
    try:
        c, t = int(correct), int(total)
        return round(c / t * 100, 1) if t else 0.0
    except: return 0.0

def time_left(close_ts) -> str:
    secs = int(close_ts) - int(time.time())
    if secs <= 0:    return "⏱ Closing"
    if secs > 3600:  return f"{secs//3600}h {(secs%3600)//60}m"
    if secs > 60:    return f"{secs//60}m {secs%60}s"
    return f"{secs}s"

def get_timeframe(ev: dict) -> str:
    sub   = (ev.get("subcategory") or "").lower()
    title = (ev.get("title") or "").lower()
    if "5"  in sub or "5m"  in sub: return "5min"
    if "15" in sub or "15m" in sub: return "15min"
    if any(k in sub   for k in ("daily","day","eod","close")): return "daily"
    if any(k in title for k in ("5 min","5min")):              return "5min"
    if any(k in title for k in ("15 min","15min")):            return "15min"
    if any(k in title for k in ("daily","eod","close","today")): return "daily"
    return "other"


# ─── API Calls ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_leaderboard(period: str = "all_time", metric: str = "pnl", limit: int = 20) -> dict:
    """GET /leaderboards  (plural — confirmed from docs)"""
    try:
        r = requests.get(
            f"{BASE_URL}/leaderboards",
            headers=HEADERS,
            params={"period": period, "metric": metric, "limit": limit},
            timeout=12,
        )
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        return {"ok": False, "status": 0, "body": str(e)}


@st.cache_data(ttl=20)
def fetch_events(category: str = "crypto", filter_: str = "live") -> dict:
    """GET /events"""
    try:
        r = requests.get(
            f"{BASE_URL}/events",
            headers=HEADERS,
            params={"category": category, "filter": filter_,
                    "includeMarkets": "true", "start": 0, "end": 50},
            timeout=12,
        )
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        return {"ok": False, "status": 0, "body": str(e)}


@st.cache_data(ttl=20)
def fetch_trades(limit: int = 30) -> dict:
    """GET /trades — global live trade feed"""
    try:
        r = requests.get(f"{BASE_URL}/trades", headers=HEADERS,
                         params={"limit": limit}, timeout=12)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        return {"ok": False, "status": 0, "body": str(e)}


@st.cache_data(ttl=20)
def fetch_profile(wallet: str) -> dict:
    """GET /profiles/{ownerPubkey}"""
    try:
        r = requests.get(f"{BASE_URL}/profiles/{wallet}",
                         headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        return {"ok": False, "status": 0, "body": str(e)}


@st.cache_data(ttl=20)
def fetch_pnl_history(wallet: str, interval: str = "1w", count: int = 12) -> dict:
    """GET /profiles/{ownerPubkey}/pnl-history"""
    try:
        r = requests.get(f"{BASE_URL}/profiles/{wallet}/pnl-history",
                         headers=HEADERS,
                         params={"interval": interval, "count": count},
                         timeout=12)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        return {"ok": False, "status": 0, "body": str(e)}


@st.cache_data(ttl=20)
def fetch_positions(wallet: str) -> dict:
    """GET /positions?ownerPubkey=..."""
    try:
        r = requests.get(f"{BASE_URL}/positions", headers=HEADERS,
                         params={"ownerPubkey": wallet}, timeout=12)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        return {"ok": False, "status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        return {"ok": False, "status": 0, "body": str(e)}


# ─── Demo fallbacks ──────────────────────────────────────────────────────────────
def demo_leaderboard(n=20):
    import random; random.seed(7)
    wallets = [
        "9kJFaB3xYqL2nRTmPdWe8vHcZ5sU1oAGbKVfN4DiXyCq","3mQpRw7NsJL9YhKbXtAeZc4FvGdU6iBWoCrPy2MnTgEk",
        "BxL4qK9pNmR2jHtZe7YfWsAc3DiVoGbUyCu5MrPnXwQJ","7vFtNq8kRmP3sHwZe2YbXcAu4DiVoGjLyCr5MrPnXwQK",
        "EmR5sN9kPmQ4tHwZe6YcXbAu3DiVoGjLyCr5MrPnXwQL","FkT6tP1mQnR5uHwZe8YdXcAv4EiWoHkMzDs6NsPqYxRM",
        "GlU7uQ2nRoS6vIxAf9ZeYeXbBw5FjXpInEt7OtQrZySN","HmV8vR3oSpT7wJyBg1AfZfYfYcCx6GkYqJoFu8PuRazTO",
        "InW9wS4pTqU8xKzCh2BgAfZgZdDy7HlZrKpGv9QvSbaUP","JoX1xT5qUrV9yLaDi3ChBgAhAeEz8ImAsLqHw1RwTcbVQ",
        "KpY2yU6rVsW1zMbEj4DiChBiBfFa9JnBtMrIx2SxUdcWR","LqZ3zV7sSuX2aNcFk5EjDiCjCgGb1KoCuNsJy3TyVedXS",
        "MrA4AU8tTvY3bOdGl6FkEjDkDhHc2LpDvOtKz4UzWfeYT","NsB5BV9uUwZ4cPeHm7GlFlElEiId3MqEwPuL15VAXgfZU",
        "OtC6CW1vVxA5dQfIn8HmGmFmFjJe4NrFxQvM26WBYhgAV","PuD7DX2wWyB6eRgJo9InHnGnGkKf5OsGzRwN37XCZihBW",
        "QvE8EY3xXzC7fShKp1JoIoHoHlLg6PtHASxO48YDajcCX","RwF9FZ4yYAD8gTiLq2KpJpIpImMh7QuIBTyP59ZEbkdDY",
        "SxG1GA5zZBE9hUjMr3LqKqJqJnNi8RvJCUzQ61AFcleCZ","TyH2HB6AAF1iVkNs4MrLrKrKoOj9SwKDVAR72BGdmfDA1",
    ]
    out = []
    for i, w in enumerate(wallets[:n]):
        pnl  = random.uniform(1800, 45000) if i < 10 else random.uniform(300, 1800)
        vol  = pnl * random.uniform(4, 14)
        corr = random.randint(12, 180)
        total = corr + random.randint(4, 80)
        out.append({
            "ownerPubkey": w,
            "realizedPnlUsd": str(int(pnl * MICRO)),
            "totalVolumeUsd": str(int(vol * MICRO)),
            "predictionsCount": str(total),
            "correctPredictions": str(corr),
            "wrongPredictions": str(total - corr),
            "winRatePct": str(round(corr / total * 100, 2)),
        })
    return out


def demo_events():
    now = int(time.time())
    return [
        {"id":"ev1","title":"BTC 5-Min Price","subtitle":"Will BTC be higher in 5 minutes?",
         "category":"crypto","subcategory":"5min","status":"open",
         "markets":[{"id":"m1","title":"BTC UP in 5 min","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":510000,"buyNoPriceUsd":490000,"volume":48200*MICRO}}],
         "totalVolumeUsd":48200*MICRO,"closeTime":now+220},
        {"id":"ev2","title":"SOL 5-Min Price","subtitle":"Will SOL be higher in 5 minutes?",
         "category":"crypto","subcategory":"5min","status":"open",
         "markets":[{"id":"m2","title":"SOL UP in 5 min","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":460000,"buyNoPriceUsd":540000,"volume":31700*MICRO}}],
         "totalVolumeUsd":31700*MICRO,"closeTime":now+170},
        {"id":"ev3","title":"ETH 5-Min Price","subtitle":"Will ETH be higher in 5 minutes?",
         "category":"crypto","subcategory":"5min","status":"open",
         "markets":[{"id":"m3","title":"ETH UP in 5 min","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":570000,"buyNoPriceUsd":430000,"volume":22900*MICRO}}],
         "totalVolumeUsd":22900*MICRO,"closeTime":now+300},
        {"id":"ev4","title":"BTC 15-Min Price","subtitle":"Will BTC be higher in 15 minutes?",
         "category":"crypto","subcategory":"15min","status":"open",
         "markets":[{"id":"m4","title":"BTC UP in 15 min","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":530000,"buyNoPriceUsd":470000,"volume":89400*MICRO}}],
         "totalVolumeUsd":89400*MICRO,"closeTime":now+780},
        {"id":"ev5","title":"SOL 15-Min Price","subtitle":"Will SOL be higher in 15 minutes?",
         "category":"crypto","subcategory":"15min","status":"open",
         "markets":[{"id":"m5","title":"SOL UP in 15 min","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":490000,"buyNoPriceUsd":510000,"volume":52100*MICRO}}],
         "totalVolumeUsd":52100*MICRO,"closeTime":now+660},
        {"id":"ev6","title":"ETH 15-Min Price","subtitle":"Will ETH be higher in 15 minutes?",
         "category":"crypto","subcategory":"15min","status":"open",
         "markets":[{"id":"m6","title":"ETH UP in 15 min","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":545000,"buyNoPriceUsd":455000,"volume":38800*MICRO}}],
         "totalVolumeUsd":38800*MICRO,"closeTime":now+710},
        {"id":"ev7","title":"BTC Daily Close","subtitle":"Will BTC close above $108,000 today?",
         "category":"crypto","subcategory":"daily","status":"open",
         "markets":[{"id":"m7","title":"BTC > $108K EOD","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":620000,"buyNoPriceUsd":380000,"volume":312000*MICRO}}],
         "totalVolumeUsd":312000*MICRO,"closeTime":now+36000},
        {"id":"ev8","title":"SOL Daily Close","subtitle":"Will SOL close above $175 today?",
         "category":"crypto","subcategory":"daily","status":"open",
         "markets":[{"id":"m8","title":"SOL > $175 EOD","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":430000,"buyNoPriceUsd":570000,"volume":187000*MICRO}}],
         "totalVolumeUsd":187000*MICRO,"closeTime":now+36200},
        {"id":"ev9","title":"JUP Daily Close","subtitle":"Will JUP close above $0.25 today?",
         "category":"crypto","subcategory":"daily","status":"open",
         "markets":[{"id":"m9","title":"JUP > $0.25 EOD","status":"open","result":None,
                     "pricing":{"buyYesPriceUsd":380000,"buyNoPriceUsd":620000,"volume":94000*MICRO}}],
         "totalVolumeUsd":94000*MICRO,"closeTime":now+36400},
    ]


def parse_events(raw) -> list:
    """Normalise events from various API response shapes."""
    if isinstance(raw, list):
        evs = raw
    elif isinstance(raw, dict):
        evs = raw.get("data", raw.get("events", raw.get("items", [])))
    else:
        return []
    # Normalise nested pricing into each market
    out = []
    for ev in evs:
        markets = ev.get("markets", [])
        norm_markets = []
        for m in markets:
            pricing = m.get("pricing", {})
            nm = dict(m)
            nm.setdefault("buyYesPriceUsd", pricing.get("buyYesPriceUsd", 500000))
            nm.setdefault("buyNoPriceUsd",  pricing.get("buyNoPriceUsd",  500000))
            nm.setdefault("volumeUsd",       pricing.get("volume", m.get("volumeUsd", 0)))
            norm_markets.append(nm)
        ne = dict(ev)
        ne["markets"] = norm_markets
        out.append(ne)
    return out


def parse_leaderboard(raw) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("data", raw.get("traders", raw.get("users", [])))
    return []


# ─── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:0.6rem 0 0.4rem;'>
        <div style='font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;
             background:linear-gradient(135deg,#00c2ff,#7b2fff);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            🔮 JUP PREDICT
        </div>
        <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#4a7fb5;
             text-transform:uppercase;letter-spacing:0.1em;margin-top:0.2rem;'>
            Tracker Dashboard · Live
        </div>
    </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("**⚙️ Leaderboard**")
    lb_period = st.selectbox("Period",
        ["all_time","monthly","weekly"],
        format_func=lambda x: {"all_time":"All Time","monthly":"Monthly","weekly":"Weekly"}[x])
    lb_metric = st.selectbox("Rank By",
        ["pnl","volume","win_rate"],
        format_func=lambda x: {"pnl":"PnL","volume":"Volume","win_rate":"Win Rate"}[x])
    top_n = st.slider("Top N", 5, 20, 20)

    st.divider()
    st.markdown("**📈 Markets**")
    mkt_filter = st.multiselect("Timeframes",
        ["5min","15min","daily","other"],
        default=["5min","15min","daily"])
    ev_filter_mode = st.selectbox("Show",
        ["live","trending","new"],
        format_func=lambda x: x.title())

    st.divider()
    auto_refresh = st.toggle("Auto Refresh (30s)", value=False)
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear(); st.rerun()

    st.divider()
    st.markdown("**🔭 Wallet Tracker**")
    tracked_wallet = st.text_input("Paste wallet address",
        placeholder="Solana pubkey…", label_visibility="collapsed")

    st.divider()
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:0.58rem;color:#2a4f7a;text-align:center;'>
        <a href='https://developers.jup.ag/docs/prediction' target='_blank'
           style='color:#00c2ff;text-decoration:none;'>API Docs ↗</a>
        &nbsp;·&nbsp;
        <a href='https://jup.ag/prediction' target='_blank'
           style='color:#00c2ff;text-decoration:none;'>Trade ↗</a>
    </div>""", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(0.1); st.rerun()

# ─── Header ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='dash-header'>
    <div class='dash-title'>🔮 Jupiter Prediction Markets Tracker</div>
    <div class='dash-sub'>
        Top 20 Most Profitable Traders · Live Crypto Markets · 5-Min · 15-Min · Daily · Solana
    </div>
</div>""", unsafe_allow_html=True)

col_ts, col_ref = st.columns([6, 1])
with col_ts:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f"<div class='refresh-info'>Last updated: {now_str}</div>", unsafe_allow_html=True)

# ─── Load data ───────────────────────────────────────────────────────────────────
with st.spinner("Fetching live data from Jupiter API…"):
    lb_resp = fetch_leaderboard(lb_period, lb_metric, top_n)
    ev_resp = fetch_events("crypto", ev_filter_mode)
    tr_resp = fetch_trades(40)

# Parse leaderboard
if lb_resp["ok"]:
    lb_raw = parse_leaderboard(lb_resp["data"])
    lb_source = "live"
else:
    lb_raw = demo_leaderboard(top_n)
    lb_source = "demo"
    st.warning(f"⚠️ Leaderboard API returned HTTP {lb_resp.get('status','?')} "
               f"— showing demo data. ({lb_resp.get('body','')[:120]})")

# Parse events
if ev_resp["ok"]:
    events = parse_events(ev_resp["data"])
    ev_source = "live"
    if not events:  # API ok but empty — fallback
        events = demo_events(); ev_source = "demo"
else:
    events = demo_events(); ev_source = "demo"
    st.warning(f"⚠️ Events API returned HTTP {ev_resp.get('status','?')} — showing demo data.")

# Parse trades
trades_live = []
if tr_resp["ok"]:
    td = tr_resp["data"]
    trades_live = td.get("data", td) if isinstance(td, dict) else td

# ─── TABS ────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Top 20 Traders", "📈 Live Markets", "🔭 Wallet Tracker", "📊 Analytics"
])


# ══════════════════════════════════════════════════════════
# TAB 1 — LEADERBOARD
# ══════════════════════════════════════════════════════════
with tab1:
    badge = "🟢 LIVE" if lb_source == "live" else "🟡 DEMO"
    st.markdown(f"<div class='section-title'>🏆 TOP {top_n} TRADERS — {badge}</div>",
                unsafe_allow_html=True)

    rows = []
    for i, t in enumerate(lb_raw[:top_n]):
        wallet   = t.get("ownerPubkey", t.get("wallet", t.get("pubkey", f"Trader-{i+1}")))
        pnl_usd  = usd(t.get("realizedPnlUsd", t.get("totalPnlUsd", 0)))
        vol_usd  = usd(t.get("totalVolumeUsd", t.get("volumeUsd", 0)))
        wr_field = t.get("winRatePct", t.get("winRate", None))
        if wr_field is not None:
            wr = float(wr_field)
        else:
            wr = win_rate(t.get("correctPredictions", 0), t.get("predictionsCount", 1))
        total_trades = int(t.get("predictionsCount", t.get("totalTrades", t.get("tradeCount", 0))))
        correct      = int(t.get("correctPredictions", 0))

        rank_icon = ["🥇","🥈","🥉"] [i] if i < 3 else f"#{i+1}"
        rows.append({
            "Rank":     rank_icon,
            "Wallet":   shorten(wallet),
            "_wallet":  wallet,
            "PnL":      pnl_usd,
            "Volume":   vol_usd,
            "Win Rate": wr,
            "Trades":   total_trades,
            "Correct":  correct,
        })

    df = pd.DataFrame(rows)

    # Summary metrics
    m1,m2,m3,m4 = st.columns(4)
    with m1: st.metric("Combined PnL", f"${df['PnL'].sum():,.0f}")
    with m2: st.metric("Avg Win Rate", f"{df['Win Rate'].mean():.1f}%")
    with m3: st.metric("Top Trader PnL", f"${df['PnL'].max():,.0f}")
    with m4: st.metric("Total Volume", f"${df['Volume'].sum():,.0f}")

    st.markdown("---")

    disp = df[["Rank","Wallet","PnL","Volume","Win Rate","Trades","Correct"]].copy()
    disp["PnL"]      = disp["PnL"].apply(lambda x: f"${x:,.2f}")
    disp["Volume"]   = disp["Volume"].apply(lambda x: f"${x:,.0f}")
    disp["Win Rate"] = disp["Win Rate"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(disp, use_container_width=True, height=560, hide_index=True,
        column_config={
            "Rank":     st.column_config.TextColumn("Rank",  width=65),
            "Wallet":   st.column_config.TextColumn("Wallet",width=130),
            "PnL":      st.column_config.TextColumn("PnL",   width=110),
            "Volume":   st.column_config.TextColumn("Volume",width=110),
            "Win Rate": st.column_config.TextColumn("Win%",  width=80),
            "Trades":   st.column_config.NumberColumn("Trades", width=80),
            "Correct":  st.column_config.NumberColumn("✓",      width=70),
        })

    # Charts
    st.markdown("<div class='section-title'>📊 PnL Distribution</div>", unsafe_allow_html=True)
    fig_bar = px.bar(df.head(20), x="Wallet", y="PnL",
        color="PnL", color_continuous_scale=[[0,"#7b2fff"],[0.5,"#00c2ff"],[1,"#00e676"]],
        template="plotly_dark")
    fig_bar.update_layout(paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
        font=dict(family="Space Mono",color="#4a7fb5"), coloraxis_showscale=False,
        margin=dict(l=10,r=10,t=10,b=60), height=280,
        xaxis=dict(tickangle=-30,gridcolor="#1a3a6b"),
        yaxis=dict(gridcolor="#1a3a6b",title="PnL (USD)"))
    st.plotly_chart(fig_bar, use_container_width=True)

    ca, cb = st.columns(2)
    with ca:
        fig_sc = px.scatter(df, x="Win Rate", y="PnL", size="Trades",
            color="PnL", hover_name="Wallet",
            color_continuous_scale=[[0,"#7b2fff"],[1,"#00e676"]],
            template="plotly_dark", title="Win Rate vs PnL")
        fig_sc.update_layout(paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
            font=dict(family="Space Mono",color="#4a7fb5"),coloraxis_showscale=False,
            margin=dict(l=10,r=10,t=40,b=10), height=270,
            xaxis=dict(gridcolor="#1a3a6b"), yaxis=dict(gridcolor="#1a3a6b"))
        st.plotly_chart(fig_sc, use_container_width=True)
    with cb:
        fig_vol = px.bar(df.head(10), x="Wallet", y="Volume", color="Win Rate",
            color_continuous_scale=[[0,"#7b2fff"],[1,"#00e676"]],
            template="plotly_dark", title="Top 10 Volume (color = win%)")
        fig_vol.update_layout(paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
            font=dict(family="Space Mono",color="#4a7fb5"),coloraxis_showscale=False,
            margin=dict(l=10,r=10,t=40,b=60), height=270,
            xaxis=dict(tickangle=-30,gridcolor="#1a3a6b"),
            yaxis=dict(gridcolor="#1a3a6b"))
        st.plotly_chart(fig_vol, use_container_width=True)

    # Live trade feed from API
    if trades_live:
        st.markdown("<div class='section-title'>⚡ LIVE TRADE FEED</div>", unsafe_allow_html=True)
        feed_rows = []
        for t in trades_live[:20]:
            ts = t.get("timestamp", 0)
            dt_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S") if ts else "—"
            feed_rows.append({
                "Time":    dt_str,
                "Trader":  shorten(t.get("ownerPubkey","")),
                "Action":  (t.get("action","") + " " + t.get("side","")).upper(),
                "Market":  (t.get("marketTitle") or t.get("eventTitle") or "—")[:40],
                "Amount":  fmt_usd(t.get("amountUsd",0)),
                "Price":   fmt_usd(t.get("priceUsd",0)),
            })
        df_feed = pd.DataFrame(feed_rows)
        st.dataframe(df_feed, use_container_width=True, height=320, hide_index=True)


# ══════════════════════════════════════════════════════════
# TAB 2 — LIVE MARKETS
# ══════════════════════════════════════════════════════════
with tab2:
    badge2 = "🟢 LIVE" if ev_source == "live" else "🟡 DEMO"
    st.markdown(f"<div class='section-title'>📈 CRYPTO PREDICTION MARKETS — {badge2}</div>",
                unsafe_allow_html=True)

    now_ts = int(time.time())
    tf_labels = {
        "5min":  "⚡ 5-Minute Markets",
        "15min": "🕐 15-Minute Markets",
        "daily": "📅 Daily Markets",
        "other": "🌐 Other Crypto Markets",
    }
    groups = {"5min":[],"15min":[],"daily":[],"other":[]}
    for ev in events:
        tf = get_timeframe(ev)
        groups.setdefault(tf, []).append(ev)

    for tf in ["5min","15min","daily","other"]:
        if tf not in mkt_filter: continue
        evs = groups.get(tf, [])
        if not evs: continue

        st.markdown(f"<div class='section-title'>{tf_labels[tf]}</div>", unsafe_allow_html=True)
        cols = st.columns(min(len(evs), 3))
        for i, ev in enumerate(evs):
            mkt     = (ev.get("markets") or [{}])[0]
            pricing = mkt.get("pricing", mkt)  # handle nested or flat
            yes_p   = float(pricing.get("buyYesPriceUsd", mkt.get("buyYesPriceUsd", 500000))) / MICRO
            no_p    = float(pricing.get("buyNoPriceUsd",  mkt.get("buyNoPriceUsd",  500000))) / MICRO
            vol     = float(ev.get("totalVolumeUsd", pricing.get("volume", 0))) / MICRO
            oi      = float(mkt.get("openInterestUsd", pricing.get("openInterest", 0))) / MICRO
            liq     = float(mkt.get("liquidityUsd", 0)) / MICRO
            tl      = time_left(ev.get("closeTime", 0))
            dir_str = "🟢 YES FAVORED" if yes_p > 0.5 else "🔴 NO FAVORED"
            dir_col = "#00e676" if yes_p > 0.5 else "#ff5252"

            with cols[i % 3]:
                st.markdown(f"""
                <div class='market-card'>
                    <div style='font-family:Syne,sans-serif;font-weight:700;font-size:0.9rem;
                         color:#e2e8f0;margin-bottom:0.15rem;'>{ev.get('title','—')}</div>
                    <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#4a7fb5;
                         margin-bottom:0.6rem;'>{ev.get('subtitle','')[:60]}</div>
                    <div style='display:flex;justify-content:space-between;margin-bottom:0.55rem;'>
                        <div style='text-align:center;flex:1;'>
                            <div style='font-family:Space Mono,monospace;font-size:0.55rem;color:#4a7fb5;'>YES</div>
                            <div style='font-family:Syne,sans-serif;font-weight:800;font-size:1.1rem;color:#00c2ff;'>{yes_p*100:.0f}¢</div>
                        </div>
                        <div style='text-align:center;flex:1;'>
                            <div style='font-family:Space Mono,monospace;font-size:0.55rem;color:#4a7fb5;'>NO</div>
                            <div style='font-family:Syne,sans-serif;font-weight:800;font-size:1.1rem;color:#b388ff;'>{no_p*100:.0f}¢</div>
                        </div>
                        <div style='text-align:center;flex:1;'>
                            <div style='font-family:Space Mono,monospace;font-size:0.55rem;color:#4a7fb5;'>CLOSES</div>
                            <div style='font-family:Space Mono,monospace;font-size:0.68rem;color:#e2e8f0;'>{tl}</div>
                        </div>
                    </div>
                    <div style='background:#060c18;border-radius:5px;padding:0.4rem 0.6rem;
                         display:flex;justify-content:space-between;margin-bottom:0.45rem;'>
                        <div><div style='font-family:Space Mono,monospace;font-size:0.5rem;color:#4a7fb5;'>VOLUME</div>
                             <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#e2e8f0;'>${vol:,.0f}</div></div>
                        <div><div style='font-family:Space Mono,monospace;font-size:0.5rem;color:#4a7fb5;'>OI</div>
                             <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#e2e8f0;'>${oi:,.0f}</div></div>
                        <div><div style='font-family:Space Mono,monospace;font-size:0.5rem;color:#4a7fb5;'>LIQ</div>
                             <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#e2e8f0;'>${liq:,.0f}</div></div>
                    </div>
                    <div style='font-family:Space Mono,monospace;font-size:0.65rem;
                         color:{dir_col};text-align:center;font-weight:700;'>{dir_str}</div>
                </div>""", unsafe_allow_html=True)

    # Summary table
    st.markdown("<div class='section-title'>📋 All Markets Summary</div>", unsafe_allow_html=True)
    ev_rows = []
    for ev in events:
        tf  = get_timeframe(ev)
        mkt = (ev.get("markets") or [{}])[0]
        pricing = mkt.get("pricing", mkt)
        yes_p = float(pricing.get("buyYesPriceUsd", mkt.get("buyYesPriceUsd", 500000))) / MICRO
        vol   = float(ev.get("totalVolumeUsd", pricing.get("volume", 0))) / MICRO
        close_ts = ev.get("closeTime", 0)
        secs = int(close_ts) - now_ts if close_ts else 0
        tl2  = f"{secs//60}m" if secs > 60 else ("Closing" if secs >= 0 else "Closed")
        ev_rows.append({
            "TF":      tf, "Market": ev.get("title","—")[:40],
            "YES":     f"{yes_p*100:.0f}¢", "NO": f"{(1-yes_p)*100:.0f}¢",
            "Volume":  f"${vol:,.0f}",
            "Closes":  tl2,
            "Signal":  "✅ YES" if yes_p > 0.5 else "❌ NO",
        })
    st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, height=320, hide_index=True)


# ══════════════════════════════════════════════════════════
# TAB 3 — WALLET TRACKER
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-title'>🔭 WALLET TRACKER</div>", unsafe_allow_html=True)

    # Quick-click top 5
    if lb_raw:
        st.markdown("**Quick-load a top trader:**")
        qcols = st.columns(5)
        for i, t in enumerate(lb_raw[:5]):
            w = t.get("ownerPubkey", t.get("wallet",""))
            ri = ["🥇","🥈","🥉","#4","#5"][i]
            with qcols[i]:
                if st.button(f"{ri} {shorten(w)}", key=f"qw{i}"):
                    st.session_state["tw"] = w

    active_wallet = st.session_state.get("tw", tracked_wallet or "")

    if active_wallet:
        st.markdown(f"""
        <div style='background:#0d1929;border:1px solid #1a3a6b;border-radius:7px;
             padding:0.5rem 0.9rem;margin:0.7rem 0;font-family:Space Mono,monospace;
             font-size:0.68rem;color:#4a7fb5;'>
            Tracking: <span style='color:#00c2ff;'>{active_wallet}</span>
        </div>""", unsafe_allow_html=True)

        # Profile
        prof_r = fetch_profile(active_wallet)
        pos_r  = fetch_positions(active_wallet)
        pnlh_r = fetch_pnl_history(active_wallet, "1w", 12)

        if prof_r["ok"]:
            p = prof_r["data"]
            p1,p2,p3,p4 = st.columns(4)
            with p1: st.metric("Realized PnL",   fmt_usd(p.get("realizedPnlUsd",0)))
            with p2: st.metric("Total Volume",    fmt_usd(p.get("totalVolumeUsd",0)))
            with p3:
                corr  = int(p.get("correctPredictions",0))
                total = int(p.get("predictionsCount",1))
                st.metric("Win Rate", f"{win_rate(corr,total):.1f}%")
            with p4: st.metric("Predictions",     p.get("predictionsCount","—"))
        else:
            st.info(f"Profile unavailable (HTTP {prof_r.get('status','?')})")

        # PnL history chart
        if pnlh_r["ok"]:
            hist = pnlh_r["data"].get("history", [])
            if hist:
                hdf = pd.DataFrame(hist)
                hdf["pnl_usd"] = hdf["realizedPnlUsd"].apply(lambda x: float(x)/MICRO)
                hdf["dt"] = pd.to_datetime(hdf["timestamp"], unit="s", utc=True)
                fig_pnl = px.line(hdf, x="dt", y="pnl_usd",
                    labels={"dt":"Date","pnl_usd":"Realized PnL ($)"},
                    title="PnL History (weekly)", template="plotly_dark",
                    color_discrete_sequence=["#00c2ff"])
                fig_pnl.update_layout(
                    paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                    font=dict(family="Space Mono",color="#4a7fb5"),
                    margin=dict(l=10,r=10,t=40,b=10), height=260,
                    xaxis=dict(gridcolor="#1a3a6b"), yaxis=dict(gridcolor="#1a3a6b"))
                fig_pnl.add_hline(y=0, line_dash="dot", line_color="#ff5252", opacity=0.4)
                st.plotly_chart(fig_pnl, use_container_width=True)

        # Positions
        if pos_r["ok"]:
            pdata = pos_r["data"]
            positions = pdata.get("data", pdata) if isinstance(pdata, dict) else pdata
            if positions:
                st.markdown("**Open Positions**")
                pos_rows = []
                for p in positions:
                    cost = float(p.get("totalCostUsd",0)) / MICRO
                    val  = float(p.get("valueUsd",0))     / MICRO
                    pnl  = val - cost
                    pct  = (pnl/cost*100) if cost else 0
                    pos_rows.append({
                        "Market": str(p.get("marketId","—"))[:35],
                        "Side":   str(p.get("side","—")).upper(),
                        "Contracts": p.get("contracts","—"),
                        "Cost":   f"${cost:.2f}",
                        "Value":  f"${val:.2f}",
                        "PnL":    f"${pnl:+.2f}",
                        "PnL%":   f"{pct:+.1f}%",
                    })
                st.dataframe(pd.DataFrame(pos_rows), use_container_width=True,
                             height=280, hide_index=True)
            else:
                st.info("No open positions for this wallet.")
        else:
            st.info(f"Positions unavailable (HTTP {pos_r.get('status','?')})")
    else:
        st.info("Paste a wallet in the sidebar or click a quick-load button above.")


# ══════════════════════════════════════════════════════════
# TAB 4 — ANALYTICS
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-title'>📊 MARKET ANALYTICS</div>", unsafe_allow_html=True)

    if events:
        # Volume by timeframe
        vol_tf = {"5min":0,"15min":0,"daily":0,"other":0}
        for ev in events:
            tf  = get_timeframe(ev)
            mkt = (ev.get("markets") or [{}])[0]
            pricing = mkt.get("pricing", mkt)
            vol_tf[tf] += float(ev.get("totalVolumeUsd", pricing.get("volume",0))) / MICRO

        ca2, cb2 = st.columns(2)
        with ca2:
            fig_tvol = px.bar(
                x=list(vol_tf.keys()), y=list(vol_tf.values()),
                color=list(vol_tf.values()),
                color_continuous_scale=[[0,"#7b2fff"],[1,"#00c2ff"]],
                labels={"x":"Timeframe","y":"Volume (USD)"},
                title="Volume by Timeframe", template="plotly_dark")
            fig_tvol.update_layout(paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono",color="#4a7fb5"),coloraxis_showscale=False,
                margin=dict(l=10,r=10,t=40,b=10), height=270,
                xaxis=dict(gridcolor="#1a3a6b"), yaxis=dict(gridcolor="#1a3a6b"))
            st.plotly_chart(fig_tvol, use_container_width=True)

        with cb2:
            # Sentiment (YES vs NO probabilities)
            sent = []
            for ev in events:
                mkt = (ev.get("markets") or [{}])[0]
                pricing = mkt.get("pricing", mkt)
                yp = float(pricing.get("buyYesPriceUsd", mkt.get("buyYesPriceUsd",500000))) / MICRO
                sent.append({"Market": ev.get("title","")[:25], "YES%": yp*100, "NO%": (1-yp)*100})
            df_sent = pd.DataFrame(sent)
            fig_sent = go.Figure()
            fig_sent.add_trace(go.Bar(name="YES", x=df_sent["Market"], y=df_sent["YES%"],
                marker_color="#00c2ff", opacity=0.85))
            fig_sent.add_trace(go.Bar(name="NO",  x=df_sent["Market"], y=df_sent["NO%"],
                marker_color="#b388ff", opacity=0.85))
            fig_sent.update_layout(barmode="stack", paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono",color="#4a7fb5"),
                margin=dict(l=10,r=10,t=40,b=70), height=270,
                xaxis=dict(tickangle=-30,gridcolor="#1a3a6b"),
                yaxis=dict(gridcolor="#1a3a6b",title="Probability %"),
                legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#e2e8f0")),
                title="Market Sentiment (YES vs NO %)")
            fig_sent.add_hline(y=50, line_dash="dot", line_color="#4a7fb5", opacity=0.4)
            st.plotly_chart(fig_sent, use_container_width=True)

    if lb_raw:
        st.markdown("<div class='section-title'>🏆 Leaderboard Analytics</div>", unsafe_allow_html=True)
        df_lb2 = pd.DataFrame([{
            "wallet": shorten(t.get("ownerPubkey", t.get("wallet",""))),
            "pnl":    usd(t.get("realizedPnlUsd", t.get("totalPnlUsd",0))),
            "wr":     float(t.get("winRatePct", t.get("winRate",
                            win_rate(t.get("correctPredictions",0), t.get("predictionsCount",1))))),
            "trades": int(t.get("predictionsCount", t.get("totalTrades",0))),
        } for t in lb_raw[:top_n]])

        cc2, cd2 = st.columns(2)
        with cc2:
            fig_hist = px.histogram(df_lb2, x="wr", nbins=10,
                color_discrete_sequence=["#00c2ff"],
                labels={"wr":"Win Rate (%)"},
                title="Win Rate Distribution", template="plotly_dark")
            fig_hist.update_layout(paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono",color="#4a7fb5"),
                margin=dict(l=10,r=10,t=40,b=10), height=260,
                xaxis=dict(gridcolor="#1a3a6b"), yaxis=dict(gridcolor="#1a3a6b"))
            st.plotly_chart(fig_hist, use_container_width=True)
        with cd2:
            fig_tr = px.scatter(df_lb2, x="trades", y="pnl", color="wr",
                size="pnl", size_max=40, hover_name="wallet",
                color_continuous_scale=[[0,"#7b2fff"],[1,"#00e676"]],
                labels={"trades":"Trades","pnl":"PnL ($)","wr":"Win %"},
                title="Trades vs PnL (color = win%)", template="plotly_dark")
            fig_tr.update_layout(paper_bgcolor="#080c14", plot_bgcolor="#0d1929",
                font=dict(family="Space Mono",color="#4a7fb5"),coloraxis_showscale=False,
                margin=dict(l=10,r=10,t=40,b=10), height=260,
                xaxis=dict(gridcolor="#1a3a6b"), yaxis=dict(gridcolor="#1a3a6b"))
            st.plotly_chart(fig_tr, use_container_width=True)

# ─── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center;font-family:Space Mono,monospace;font-size:0.6rem;color:#2a4f7a;padding:0.4rem;'>
    Jupiter Predict Tracker · 
    <a href='https://developers.jup.ag/docs/prediction' target='_blank' style='color:#00c2ff;text-decoration:none;'>
    API Docs (Beta)</a> · Not financial advice
</div>""", unsafe_allow_html=True)
