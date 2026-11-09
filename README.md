# Validata — Authenticity Engine

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdeepeshyadav0425%2FValidata)

**Validata** is an AI and NLP-powered computational journalism platform designed to detect fake, misleading, sensationalist, or satirical news from any source (URLs, pasted article text, social media snippets, WhatsApp forwards, and claims) with explainable credibility scoring.

---

## 🌟 Key Features

- **Multi-Source Ingestion**:
  - **Direct Text**: Analyze raw headlines, full article bodies, viral WhatsApp forwards, or social media posts.
  - **Live URL Article Scraper**: Automatically extracts headline, body text, author, publisher, and date from any online news website.
  - **Pre-Loaded Realistic Test Corpus**: Test immediately with 1-click sample articles (Reuters wire, miracle cure hoaxes, The Onion satire, clickbait).

- **5-Layer Analytical Detection Engine**:
  1. **Source & Publisher Reputation**: Curated database of trusted global & regional newsrooms (Reuters, AP, BBC, The Hindu, etc.), known satire outlets (The Onion, Babylon Bee), suspicious TLDs (`.xyz`, `.top`, `.buzz`), and brand-spoofing detection (`bbc-news-today.com`).
  2. **Linguistic & Stylistic Analysis**: Detects sensationalism, emotional manipulation, ALL-CAPS screaming, excessive punctuation (`???`, `!!!`), clickbait phrasing, and headline-to-body divergence (bait-and-switch).
  3. **Evidentiary & Attribution Checker**: Identifies direct journalistic quotes, institutional attribution (WHO, courts, universities, ministries), and flags anonymous weasel words ("experts say", "secret sources claim").
  4. **Machine Learning NLP Classifier**: Calibrated TF-IDF n-gram text classification pipeline trained on genuine journalistic corpora vs fabricated disinformation.
  5. **Claim Extraction & 1-Click Verification**: Automatically extracts testable factual claims and generates direct 1-click search links to the **Google Fact Check Explorer** and international news wire feeds.

- **Explainable Verdicts & Metrics**:
  - 🟢 **GENUINE / HIGHLY CREDIBLE** (Score: 78% – 100%)
  - 🟡 **QUESTIONABLE / UNVERIFIED** (Score: 45% – 77%)
  - 🔴 **LIKELY FAKE / FABRICATED** (Score: 0% – 44%)
  - 🟣 **SATIRE / PARODY** (Identified satirical publication)
  - Interactive circular SVG credibility gauge.
  - 5-axis Radar / Spider chart visualizing each analytical pillar.
  - Itemized Red Flags (with warnings) and Credibility Highlights.

- **Audit History & Reporting**:
  - Persistent SQLite database recording every analysis.
  - Filter history by verdict, inspect archived reports, or delete entries.
  - One-click **Print / Save as PDF** report and **Export JSON** report.
  - Light and Dark theme support.

---

## 📁 Project Structure

```
Fake News Detector/
├── backend/
│   ├── app.py                   # REST API server & static file host (Flask)
│   ├── config.py                # Scoring weights, thresholds & domain databases
│   ├── analyzers/
│   │   ├── source_analyzer.py   # Domain reputation & spoofing detector
│   │   ├── style_analyzer.py    # Clickbait & sensationalism analyzer
│   │   ├── evidence_analyzer.py # Quotes, attribution & weasel words analyzer
│   │   └── claim_extractor.py   # Claim extraction & fact-check query generator
│   ├── models/
│   │   ├── train_model.py       # ML training script with TF-IDF pipeline
│   │   ├── classifier.py        # Model inference & explainable feature signals
│   │   └── fake_news_model.pkl  # Trained ML model artifact
│   ├── scraper/
│   │   └── url_scraper.py       # Web article parser (BeautifulSoup + requests)
│   └── database/
│       ├── db.py                # SQLite persistence layer
│       └── fakenews_history.db  # Database storage
├── frontend/
│   ├── index.html               # Single-page web dashboard
│   ├── style.css                # Glassmorphic responsive stylesheet
│   └── app.js                   # Client logic, Chart.js radar & API bindings
├── tests/
│   └── test_detector.py         # Automated unit & integration test suite
├── requirements.txt             # Python dependencies
├── run.bat                      # 1-Click Windows execution script
└── README.md                    # Documentation & user guide
```

---

## 🚀 Quick Start Guide

### Option 1: One-Click Launcher (Windows)
Double-click `run.bat` in the root folder.
This script checks dependencies, starts the backend server, and automatically opens `http://127.0.0.1:5000` in your web browser.

### Option 2: Command Line
1. **Ensure Python 3.12+ is installed**:
   ```bash
   python --version
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the application**:
   ```bash
   python -m backend.app
   ```
4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 🧪 Running Automated Tests

Run the comprehensive test suite verifying all 5 layers, satire recognition, domain spoofing, and API endpoints:
```bash
python -m unittest tests/test_detector.py
```

All 8 tests pass with `OK`:
- `test_genuine_reuters_article`: Confirms wire news is marked `GENUINE` (Score ≥ 78).
- `test_fake_miracle_cure_hoax`: Confirms medical disinformation is marked `FAKE` (Score < 45).
- `test_satire_article_detection`: Confirms satirical pieces are categorized as `SATIRE`.
- `test_domain_spoofing_detection`: Verifies imitation domains (e.g. `bbc-breakingnews-today.com`) are flagged.
- `test_clickbait_and_sensationalism_analyzer`: Verifies clickbait phrasing detection.
- `test_attribution_analyzer`: Verifies quote and institutional recognition.
- `test_claims_extraction`: Verifies fact-check links generation.
- `test_api_endpoints`: Verifies all REST endpoints (`/api/analyze/text`, `/api/sample-articles`, etc.).

---

## 📡 REST API Documentation

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `GET /` | `GET` | Serves the interactive web dashboard |
| `POST /api/analyze/text` | `POST` | Analyze article text (`headline`, `body`, `source_url`, `publisher`) |
| `POST /api/analyze/url` | `POST` | Scrape and analyze an online news link (`url`) |
| `GET /api/history` | `GET` | Retrieve audit history (`?limit=50&verdict=GENUINE`) |
| `GET /api/history/<id>` | `GET` | Retrieve full analysis report by ID |
| `DELETE /api/history/<id>` | `DELETE`| Remove a report from audit history |
| `GET /api/stats` | `GET` | Global aggregate statistics (Total, % Genuine, % Fake, % Satire) |
| `GET /api/sample-articles` | `GET` | Curated sample news articles for instant one-click testing |
