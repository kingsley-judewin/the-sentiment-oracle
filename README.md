# 🔮 The Tokenized Sentiment Oracle

> _"Markets move on narratives. We convert real‑time social discussion into a reliable, quantitative signal that decentralized systems can act upon."_

[![Solidity](https://img.shields.io/badge/Solidity-0.8.20-363636?logo=solidity)](contracts/SentimentOracle.sol)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](python-engine/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](dashboard/)
[![Polygon](https://img.shields.io/badge/Polygon-Amoy_Testnet-8247E5?logo=polygon)](https://amoy.polygonscan.com/address/0x0878645D0ee175Df0a5F61fa047A72d346b1D162)

---

## 📋 Table of Contents

- [The Problem](#the-problem)
- [Our Solution](#our-solution)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Core Pipeline](#core-pipeline)
- [Smart Contract](#smart-contract)
- [Technical Challenges & Solutions](#technical-challenges--solutions)
- [Live Demo](#live-demo)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deployment](#deployment)

---

## 🧩 The Problem

DeFi protocols and smart contracts are **blind to public sentiment**. Markets move on narratives, hype, and collective belief — yet on-chain logic has no way to access this information. Traders react to social signals manually, creating latency and inefficiency.

**What if smart contracts could listen to the crowd?**

---

## 💡 Our Solution

We built an **end-to-end Sentiment Oracle** — a fully autonomous pipeline that:

1. **Ingests** real-time social content from Reddit RSS feeds and a 1.6M-tweet Twitter dataset
2. **Cleans** noisy data (sarcasm, spam, manipulation, ALL-CAPS shouting)
3. **Analyzes** sentiment using a fine-tuned DistilBERT transformer model
4. **Computes** an engagement-weighted **Community Vibe Score** ([-100, +100])
5. **Smooths** the signal using Exponential Moving Average (EMA) to prevent viral spikes
6. **Pushes** the score on-chain to a Solidity smart contract on Polygon Amoy
7. **Triggers** Bullish/Bearish/Neutral signal events that other contracts can consume

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA INGESTION                          │
│  ┌──────────────┐    ┌──────────────────┐                   │
│  │  Reddit RSS  │    │  Sentiment140    │                   │
│  │  (Live)      │    │  (1.6M Tweets)   │                   │
│  └──────┬───────┘    └────────┬─────────┘                   │
│         └──────────┬──────────┘                              │
│              ┌─────▼─────┐                                   │
│              │  Source    │ ← Hybrid / RSS / Twitter mode     │
│              │  Router   │                                   │
│              └─────┬─────┘                                   │
│              ┌─────▼─────────┐                               │
│              │ Deduplicator  │ ← Rolling 500-hash window     │
│              └─────┬─────────┘                               │
├────────────────────┼────────────────────────────────────────┤
│                    │     NLP ENGINE                          │
│              ┌─────▼─────┐                                   │
│              │  Cleaner   │ ← URLs, HTML, emojis, spam       │
│              └─────┬─────┘                                   │
│              ┌─────▼──────────────┐                          │
│              │  DistilBERT Model  │ ← Sentiment inference    │
│              └─────┬──────────────┘                          │
├────────────────────┼────────────────────────────────────────┤
│                    │     SCORING                             │
│              ┌─────▼──────────────┐                          │
│              │  Vibe Score Engine │ ← Engagement-weighted    │
│              └─────┬──────────────┘                          │
│              ┌─────▼────────┐                                │
│              │  EMA Smoother│ ← α = 0.3                      │
│              └─────┬────────┘                                │
├────────────────────┼────────────────────────────────────────┤
│              ┌─────▼────┐     ┌──────────────┐              │
│              │ FastAPI   │     │   React      │              │
│              │ Backend   │────▶│   Dashboard  │              │
│              └─────┬─────┘     └──────────────┘              │
│              ┌─────▼──────────────┐                          │
│              │  Oracle Bridge     │ ← Safety filters          │
│              │  (Hardhat / JS)    │                           │
│              └─────┬──────────────┘                          │
│              ┌─────▼──────────────────┐                      │
│              │  SentimentOracle.sol   │ ← Polygon Amoy       │
│              │  (Smart Contract)      │                      │
│              └────────────────────────┘                      │
│                    │                                         │
│         ┌─────────┼─────────┐                                │
│         ▼         ▼         ▼                                │
│    Bullish    Neutral    Bearish                              │
│    Signal     Signal     Signal   ← On-chain events          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
sentiment-oracle/
│
├── python-engine/                  # 🐍 BACKEND — FastAPI + NLP Pipeline
│   ├── app/
│   │   ├── main.py                 # FastAPI server, /oracle & /sentiment endpoints
│   │   ├── config.py               # Centralized configuration
│   │   ├── ingestion/              # Multi-source data ingestion
│   │   │   ├── source_router.py    # Hybrid/RSS/Twitter mode selector
│   │   │   ├── reddit_rss.py       # Live Reddit RSS feed scraper
│   │   │   ├── twitter_dataset.py  # Sentiment140 dataset loader
│   │   │   ├── deduplicator.py     # Rolling cross-cycle deduplication
│   │   │   ├── stream_manager.py   # Rate limiting & caching
│   │   │   └── mock_stream.py      # Mock data for testing
│   │   ├── nlp/                    # NLP & Sentiment Analysis
│   │   │   ├── model.py            # DistilBERT model loader (singleton)
│   │   │   ├── sentiment.py        # Sentiment inference layer
│   │   │   └── cleaner.py          # Noise reduction (spam, sarcasm, URLs)
│   │   ├── scoring/                # Score Computation
│   │   │   ├── vibe_score.py       # Community Vibe Score algorithm
│   │   │   ├── smoothing.py        # EMA volatility dampening
│   │   │   └── aggregator.py       # Post aggregation & normalization
│   │   ├── monitoring/             # Health checks & metrics
│   │   ├── testing/                # Unit tests & stress tests
│   │   └── utils/                  # Logger & helpers
│   ├── requirements.txt            # Python dependencies
│   └── run.py                      # Server entry point
│
├── dashboard/                      # ⚛️ FRONTEND — React + Vite
│   ├── src/
│   │   ├── App.jsx                 # Main dashboard layout
│   │   ├── components/
│   │   │   ├── ScoreCard.jsx       # Community Vibe Score display
│   │   │   ├── PostsList.jsx       # Recent posts with sentiment tags
│   │   │   └── StatusBar.jsx       # Pipeline health & status
│   │   ├── hooks/
│   │   │   └── useSentiment.js     # Auto-refresh data hook (10s interval)
│   │   └── utils/
│   │       └── sentimentUtils.js   # Color mapping & score formatting
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── contracts/                      # ⛓️ SMART CONTRACT — Solidity
│   └── SentimentOracle.sol         # On-chain oracle (Polygon Amoy)
│
├── scripts/                        # 🔧 BLOCKCHAIN SCRIPTS — Hardhat
│   ├── deploy.js                   # Contract deployment
│   ├── oracle_bridge.js            # AI ↔ Blockchain automation bridge
│   ├── read_state.js               # Read on-chain state
│   └── update.js                   # Manual score update
│
├── hardhat.config.js               # Hardhat configuration (Polygon Amoy)
├── package.json                    # Node.js dependencies
├── .env                            # Private key (not committed)
├── start-backend.ps1               # One-click backend launcher
└── start-dashboard.ps1             # One-click dashboard launcher
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **NLP Model** | DistilBERT (HuggingFace) | Sentiment classification |
| **Backend** | FastAPI + Uvicorn | REST API & pipeline orchestration |
| **Frontend** | React 18 + Vite | Live sentiment dashboard |
| **Blockchain** | Solidity 0.8.20 + Hardhat | On-chain sentiment oracle |
| **Network** | Polygon Amoy Testnet | Low-cost, fast L2 chain |
| **Data Sources** | Reddit RSS, Sentiment140 | Real-time + historical social data |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **MetaMask** wallet with Amoy testnet MATIC ([Faucet](https://faucet.polygon.technology/))

### 1. Clone & Install

```bash
git clone https://github.com/your-repo/sentiment-oracle.git
cd sentiment-oracle
```

### 2. Backend Setup (Python Engine)

```bash
cd python-engine
pip install -r requirements.txt
cd ..
```

> **Note:** On first run, the DistilBERT model (~250MB) will auto-download from HuggingFace.

### 3. Frontend Setup (Dashboard)

```bash
cd dashboard
npm install
cd ..
```

### 4. Smart Contract Setup

```bash
npm install                    # Install Hardhat & dependencies
cp .env.example .env           # Add your wallet private key
```

### 5. Run Everything

**Terminal 1 — Backend:**
```bash
cd python-engine
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Dashboard:**
```bash
cd dashboard
npm run dev
```

**Terminal 3 — Oracle Bridge (optional):**
```bash
npx hardhat run scripts/oracle_bridge.js --network amoy
```

### 6. Open Dashboard

Visit **http://localhost:5173** — you'll see live sentiment scores updating every 10 seconds.

---

## ⚙️ Core Pipeline

### 1. Data Ingestion (`python-engine/app/ingestion/`)

| Source | Type | Subreddits / Dataset |
|--------|------|---------------------|
| Reddit RSS | Live | r/cryptocurrency, r/bitcoin, r/ethtrader, r/defi |
| Sentiment140 | Historical | 1.6M tweets (rolling sample of 50 per cycle) |

The **Source Router** supports four modes: `mock`, `rss`, `twitter`, `hybrid`  
The **Deduplicator** maintains a rolling window of 500 post hashes to prevent cross-cycle duplicates.

### 2. Noise Reduction (`python-engine/app/nlp/cleaner.py`)

| Filter | What It Catches |
|--------|----------------|
| URL stripping | Links and self-promotion |
| HTML removal | Encoded markup |
| Emoji removal | Non-textual noise |
| Excessive symbols | `$$$`, `!!!`, etc. |
| Character collapse | `sooooo` → `soo` |
| ALL-CAPS detection | Shouting / low-quality posts |
| Word count filter | Posts < 5 words |
| Spam phrase filter | "buy now", "free money", etc. |

### 3. Sentiment Analysis (`python-engine/app/nlp/`)

- **Model:** `distilbert-base-uncased-finetuned-sst-2-english`
- **Output per post:** `{ label: POSITIVE|NEGATIVE, confidence: 0.0-1.0, polarity: +1|-1 }`

### 4. Community Vibe Score (`python-engine/app/scoring/vibe_score.py`)

```
Per-post:   weight = engagement × confidence × 1.5
            signal = polarity × weight

Aggregate:  community_signal = mean(signals)

Normalize:  vibe_score = (signal / max_weight) × 100
            clamped to [-100, +100]
```

### 5. EMA Smoothing (`python-engine/app/scoring/smoothing.py`)

```
smoothed = α × raw + (1 - α) × previous    (α = 0.3)
```

Prevents single viral posts from causing extreme spikes.

---

## ⛓️ Smart Contract

### `SentimentOracle.sol` — Deployed on Polygon Amoy

**Contract Address:** [`0x0878645D0ee175Df0a5F61fa047A72d346b1D162`](https://amoy.polygonscan.com/address/0x0878645D0ee175Df0a5F61fa047A72d346b1D162)

#### Features

| Feature | Description |
|---------|------------|
| **updateSentiment(int256)** | Push vibe score on-chain (oracle-only) |
| **getSentiment()** | Read current score + timestamp |
| **getOracleState()** | Full state: score, timestamp, bullish/bearish flags |
| **BullishSignal** event | Emitted when score ≥ +60 |
| **BearishSignal** event | Emitted when score ≤ -60 |
| **NeutralSignal** event | Emitted when score is between thresholds |
| **Rate limiting** | Minimum 60s between updates |
| **Replay protection** | Rejects duplicate consecutive scores |
| **Configurable thresholds** | Adjustable bullish/bearish boundaries |

#### Oracle Bridge (`scripts/oracle_bridge.js`)

The autonomous bridge runs in a loop:
1. Fetches sentiment from the AI engine (`/oracle` endpoint)
2. Validates payload (safety filters, min sample size)
3. Checks on-chain state for duplicates
4. Pushes score via `updateSentiment()`
5. Logs the signal event (Bullish/Bearish/Neutral)

---

## 🧠 Technical Challenges & Solutions

### 1. Noise Reduction
> _Handle sarcasm, spam, and coordinated manipulation._

**Solution:** Multi-layer cleaning pipeline in `cleaner.py` — strips URLs, HTML, emojis, repeated characters, ALL-CAPS shouting, and known spam phrases. Posts under 5 words are dropped.

### 2. Sentiment Aggregation
> _Convert qualitative text into stable quantitative signals._

**Solution:** Engagement-weighted voting in `vibe_score.py` — each post's influence is proportional to `engagement × confidence × polarity`, then normalized to [-100, +100].

### 3. Oracle Design
> _Ensure transparency, reproducibility, and resistance to gaming._

**Solution:**
- **EMA smoothing** (α=0.3) prevents single-post spikes
- **Cross-cycle deduplication** (500-hash window) prevents replay attacks
- **Rate limiting** (60s on-chain) throttles manipulation
- **Replay protection** (contract rejects duplicate scores)
- **Configurable thresholds** for bullish/bearish signals

### 4. On-Chain Integration
> _Safely connect off-chain sentiment to on-chain logic._

**Solution:** Oracle bridge with 3-retry fetch, payload validation, sample size minimums, and on-chain state comparison before pushing.

---

## 🖥️ Live Demo

### Dashboard (http://localhost:5173)

| Component | What It Shows |
|-----------|--------------|
| **ScoreCard** | Community Vibe Score with color-coded sentiment |
| **StatusBar** | Pipeline health, source info, last update |
| **PostsList** | Recent analyzed posts with sentiment labels |

### On-Chain Transactions

View live transactions on Polygonscan:  
[`0x0878645D0ee175Df0a5F61fa047A72d346b1D162`](https://amoy.polygonscan.com/address/0x0878645D0ee175Df0a5F61fa047A72d346b1D162)

---

## 📡 API Reference

### `GET /oracle`
Full pipeline execution — returns structured score for on-chain push.

```json
{
  "raw_score": -64.02,
  "smoothed_score": -22.19,
  "post_count": 45,
  "positive_count": 7,
  "negative_count": 38,
  "last_updated_timestamp": "2026-02-14T05:55:05.315632+00:00"
}
```

### `GET /sentiment`
Dashboard-optimized endpoint — includes full post data.

```json
{
  "community_vibe_score": -22,
  "raw_score": -64.02,
  "sample_size": 45,
  "positive_ratio": 0.16,
  "status": "Pipeline healthy",
  "posts": [ ... ]
}
```

### `GET /health`
Health check endpoint.

### `GET /metrics`
Pipeline performance metrics.

---

## ⚙️ Configuration

All parameters are centralized in `python-engine/app/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `INGESTION_MODE` | `"hybrid"` | Data source mode (`mock`/`rss`/`twitter`/`hybrid`) |
| `MODEL_NAME` | `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace model |
| `EMA_ALPHA` | `0.3` | Smoothing factor (0=smooth, 1=reactive) |
| `ENGAGEMENT_WEIGHT_MULTIPLIER` | `1.5` | Engagement influence on scoring |
| `MIN_POST_WORD_COUNT` | `5` | Minimum words per post |
| `TWITTER_SAMPLE_SIZE` | `50` | Posts sampled per cycle |
| `DEDUP_WINDOW_SIZE` | `500` | Rolling dedup hash window |
| `RSS_FETCH_INTERVAL` | `30` | Seconds between RSS fetches |
| `SUBREDDITS` | `["cryptocurrency", "bitcoin", "ethtrader", "defi"]` | Reddit sources |

---

## 📊 Evidence: Social Sentiment as an Oracle

This project demonstrates that social sentiment **can reliably function as an oracle**:

1. ✅ **Quantitative signal** — Raw text is converted to a bounded [-100, +100] score
2. ✅ **Noise resistant** — Multi-layer cleaning + EMA smoothing dampens manipulation
3. ✅ **Transparent** — Every step is logged, reproducible, and auditable
4. ✅ **On-chain verifiable** — Score and signal events are permanently recorded on Polygon
5. ✅ **Actionable** — BullishSignal / BearishSignal events can trigger automated DeFi actions

---

## 🌐 Deployment

### Backend → Render (Free Tier)

1. Push your repo to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Configure:
   | Setting | Value |
   |---------|-------|
   | **Root Directory** | `python-engine` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | **Environment** | `FRONTEND_URL` = your Vercel URL (e.g. `https://sentiment-oracle.vercel.app`) |

5. Deploy — note the Render URL (e.g. `https://sentiment-oracle.onrender.com`)

### Frontend → Vercel (Free Tier)

1. Go to [vercel.com](https://vercel.com) → **Import Project**
2. Connect your GitHub repo
3. Configure:
   | Setting | Value |
   |---------|-------|
   | **Root Directory** | `dashboard` |
   | **Framework** | Vite |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |
   | **Environment Variable** | `VITE_API_URL` = your Render backend URL |

4. Deploy!

### Smart Contract → Already Live

**Contract:** [`0x0878645D0ee175Df0a5F61fa047A72d346b1D162`](https://amoy.polygonscan.com/address/0x0878645D0ee175Df0a5F61fa047A72d346b1D162)  
**Network:** Polygon Amoy Testnet

To redeploy:
```bash
npx hardhat run scripts/deploy.js --network amoy
```

### Oracle Bridge

Run from any machine with Node.js:
```bash
npx hardhat run scripts/oracle_bridge.js --network amoy
```

---

## 👥 Team

Built for the DeFi / NLP / Market Intelligence hackathon track.

---

## 📄 License

MIT License

