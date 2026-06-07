# 🔮 Jupiter Prediction Markets Tracker

A live dashboard tracking the **Top 20 Most Profitable Traders** on Jupiter's Prediction Markets (Solana), with real-time crypto UP/DOWN markets across 5-min, 15-min, and daily timeframes.

![Dashboard Preview](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)
![Solana](https://img.shields.io/badge/Solana-Jupiter%20API-9945FF?logo=solana)

## ✨ Features

- 🏆 **Top 20 Leaderboard** — ranked by total PnL, with win rate, volume, trade count
- 📈 **Live Crypto Markets** — BTC/SOL/ETH UP or DOWN across 5-min, 15-min, and daily timeframes
- 🔭 **Wallet Tracker** — drill into any trader's open positions and PnL
- 📊 **Analytics** — sentiment charts, volume by timeframe, win rate distributions
- 🟡 **Demo Mode** — works out-of-the-box without an API key (realistic sample data)
- 🟢 **Live Mode** — connects to Jupiter Prediction API with your free API key

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/jup-predict-dashboard.git
cd jup-predict-dashboard
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run locally

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔑 Getting a Jupiter API Key (Free)

1. Go to **[portal.jup.ag](https://portal.jup.ag)**
2. Connect your wallet or sign up
3. Generate a free API key
4. Paste it in the dashboard sidebar

> **Note:** The Jupiter Prediction API is currently in **beta**. Some endpoints (e.g., leaderboard) may evolve. The dashboard gracefully falls back to demo data if an endpoint isn't available yet.

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. **Fork this repo** to your GitHub account

2. Go to **[share.streamlit.io](https://share.streamlit.io)**

3. Click **"New app"** → connect your GitHub

4. Set:
   - **Repository:** `your-username/jup-predict-dashboard`
   - **Branch:** `main`
   - **Main file:** `app.py`

5. Click **Deploy** — done! 🎉

### Optional: Add your API key as a secret

In Streamlit Cloud, go to **Settings → Secrets** and add:

```toml
JUP_API_KEY = "your_api_key_here"
```

Then in `app.py`, update the sidebar to read:
```python
import os
api_key = st.sidebar.text_input(...) or st.secrets.get("JUP_API_KEY", "")
```

---

## 📡 API Endpoints Used

| Endpoint | Purpose |
|---|---|
| `GET /prediction/v1/leaderboard` | Top traders by PnL |
| `GET /prediction/v1/events?category=crypto` | Live crypto markets |
| `GET /prediction/v1/positions?ownerPubkey=...` | Wallet positions |
| `GET /prediction/v1/profiles/{wallet}` | Trader profile |

Full docs: [developers.jup.ag/docs/prediction](https://developers.jup.ag/docs/prediction)

---

## 📊 Market Timeframes Tracked

| Timeframe | Description | Example |
|---|---|---|
| ⚡ **5-Minute** | Ultra short-term crypto direction | "Will BTC be higher in 5 min?" |
| 🕐 **15-Minute** | Short-term crypto direction | "Will SOL be higher in 15 min?" |
| 📅 **Daily** | End-of-day price targets | "Will BTC close above $108K?" |

---

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io)** — Python web app framework
- **[Plotly](https://plotly.com)** — Interactive charts
- **[Pandas](https://pandas.pydata.org)** — Data manipulation
- **[Jupiter Prediction API](https://developers.jup.ag/docs/prediction)** — On-chain data

---

## ⚠️ Disclaimer

This dashboard is for informational purposes only. Not financial advice. Prediction markets involve risk of total loss. Jupiter Prediction API is in beta and subject to changes.

---

## 📄 License

MIT — free to use, modify, and deploy.
