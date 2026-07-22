<p align="center">
  <h1 align="center">🎯 Opportunity Scout Agent</h1>
  <p align="center">
    <strong>An autonomous intelligence engine that continuously discovers grants, fellowships, internships, and career opportunities — and delivers them straight to your WhatsApp.</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" alt="Version" />
    <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-18.2-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
    <img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite" />
    <img src="https://img.shields.io/badge/Railway-ready-0B0D0E?style=flat-square&logo=railway&logoColor=white" alt="Railway" />
    <img src="https://img.shields.io/github/license/CalKK/scout_agent?style=flat-square" alt="License" />
  </p>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Deployment (Railway)](#deployment-railway)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Opportunity Scout Agent** is a full-stack autonomous scouting system designed to monitor RSS feeds and web pages for opportunities matching your interest areas. It ingests content from configurable sources, filters it against your keywords using a case-insensitive substring matching algorithm, stores deduplicated results in a local SQLite database, and notifies you via WhatsApp using the CallMeBot API.

The system consists of three core components:

| Component | Technology | Purpose |
|:--|:--|:--|
| **Scouting Engine** | Python, BeautifulSoup, feedparser | RSS & HTML ingestion, keyword matching, deduplication |
| **REST API** | FastAPI, Uvicorn | Exposes scouted data to the dashboard and external clients |
| **Dashboard** | React 18, Vite | Real-time search, filtering, and visualization of opportunities |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    config.json                          │
│          (keywords, sources, WhatsApp creds)            │
└────────────────────────┬────────────────────────────────┘
                         │
           ┌─────────────▼──────────────┐
           │    scout_agent.py          │
           │  ┌──────────────────────┐  │
           │  │  RSS Feed Ingestion  │  │  feedparser
           │  │  HTML Web Scraping   │  │  BeautifulSoup
           │  │  Keyword Matching    │  │  Substring algo
           │  │  Deduplication       │  │  SQLite UNIQUE
           │  └──────────┬───────────┘  │
           └─────────────┼──────────────┘
                         │
              ┌──────────▼──────────┐
              │   scout_data.db     │
              │  (SQLite Database)  │
              └──────────┬──────────┘
                         │
           ┌─────────────▼──────────────┐
           │         api.py             │
           │  ┌──────────────────────┐  │
           │  │  FastAPI REST API    │  │  /api/opportunities
           │  │  Background Scheduler│  │  6-hour auto cycle
           │  │  Static File Server  │  │  Serves React build
           │  └──────────┬───────────┘  │
           └─────────────┼──────────────┘
                    ┌────┴────┐
                    │         │
          ┌─────────▼──┐  ┌──▼──────────┐
          │  React UI  │  │  WhatsApp   │
          │ Dashboard  │  │ CallMeBot   │
          └────────────┘  └─────────────┘
```

---

## Features

- **🔄 Multi-Source Ingestion** — Parses RSS/Atom feeds and scrapes HTML pages concurrently
- **🔍 Smart Keyword Matching** — Case-insensitive substring algorithm with multi-keyword support
- **🛡️ Automatic Deduplication** — SQLite `UNIQUE(url)` constraint prevents duplicate entries
- **📱 WhatsApp Notifications** — Daily digest delivered via CallMeBot with automatic message chunking (3,000 char limit)
- **📊 Interactive Dashboard** — React-based UI with real-time search, source filtering, and keyword filtering
- **⏰ Background Scheduling** — Embedded asyncio loop runs scouting cycles every 6 hours
- **🚀 Railway-Ready** — Single-service deployment with frontend and backend served from the same process
- **📝 Run Logging** — Every scouting cycle logs timestamp, sources checked, items found, and errors

---

## Prerequisites

| Requirement | Minimum Version |
|:--|:--|
| Python | 3.10+ |
| Node.js | 18+ (for frontend development) |
| npm | 9+ |
| Git | 2.x |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/CalKK/scout_agent.git
cd scout_agent
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `beautifulsoup4` — HTML parsing and text extraction
- `feedparser` — RSS/Atom feed parsing
- `requests` — HTTP client for WhatsApp API dispatch
- `fastapi` — REST API framework
- `uvicorn` — ASGI server

### 3. Install Frontend Dependencies (Optional — for local dashboard development)

```bash
cd frontend
npm install
cd ..
```

---

## Configuration

All runtime configuration is managed through a single `config.json` file in the project root.

### Configuration Schema

```json
{
  "keywords": [
    "grant",
    "call for applications",
    "internship",
    "scholarships",
    "positions",
    "fellowship"
  ],
  "sources": {
    "rss_feeds": [
      "https://example.com/feed.xml"
    ],
    "scrape_sites": [
      "https://example.com/opportunities/"
    ]
  },
  "whatsapp": {
    "phone_number": "+254XXXXXXXXX",
    "api_key": "YOUR_CALLMEBOT_API_KEY"
  }
}
```

### Configuration Reference

| Field | Type | Description |
|:--|:--|:--|
| `keywords` | `string[]` | List of search terms. Matching is case-insensitive substring. |
| `sources.rss_feeds` | `string[]` | URLs of RSS/Atom feeds to parse. |
| `sources.scrape_sites` | `string[]` | URLs of HTML pages to scrape for `<h1>`, `<h2>`, `<h3>`, and `<p>` elements. |
| `whatsapp.phone_number` | `string` | Your WhatsApp number in international format (e.g., `+254...`). |
| `whatsapp.api_key` | `string` | Your CallMeBot API key. [Get one here](https://www.callmebot.com/blog/free-api-whatsapp-messages/). |

### Setting Up CallMeBot WhatsApp Notifications

1. Save the contact **+34 644 71 84 88** in your phone as "CallMeBot".
2. Send the message `I allow callmebot to send me messages` to this contact via WhatsApp.
3. You will receive your API key in the response.
4. Enter your phone number and API key in `config.json`.

---

## Usage

### Run a Scouting Cycle

Scrapes all configured RSS feeds and websites, filters results against your keywords, and stores new opportunities in the SQLite database:

```bash
python scout_agent.py
```

**Expected output:**
```
[2026-07-22 20:51:16.945743] Starting scout cycle...
Cycle complete. Scraped/updated opportunities into scout_data.db.
```

### Send WhatsApp Daily Summary

Compiles all opportunities discovered in the last 24 hours and dispatches them to your WhatsApp:

```bash
python scout_agent.py --summary
```

### Start the API Server (Local Development)

```bash
python -m uvicorn api:app --reload --port 8001
```

The API will be available at `http://localhost:8001`. Interactive docs at `http://localhost:8001/docs`.

### Start the Frontend Dashboard (Local Development)

In a separate terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

### Piecemeal Stress Testing

**Test RSS ingestion individually:**
```bash
python -c "from scout_agent import ingest_rss, load_config; import sqlite3; conn = sqlite3.connect('scout_data.db'); config = load_config(); count = ingest_rss(config['sources']['rss_feeds'][0], config['keywords'], conn); print(f'Found {count} new items')"
```

**Test HTML scraper individually:**
```bash
python -c "from scout_agent import ingest_html, load_config; import sqlite3; conn = sqlite3.connect('scout_data.db'); config = load_config(); count = ingest_html(config['sources']['scrape_sites'][0], config['keywords'], conn); print(f'Found {count} new items')"
```

**Test keyword matching logic:**
```bash
python -c "from scout_agent import match_keywords, load_config; config = load_config(); print(match_keywords('Apply for our 2026 undergraduate scholarships and fellowship program!', config['keywords']))"
```

**Test deduplication (should return `True` then `False`):**
```bash
python -c "from scout_agent import save_opportunity; import sqlite3; conn = sqlite3.connect('scout_data.db'); r1 = save_opportunity(conn, 'Test', 'https://test.com/dedup-check', 'Snippet', 'src', ['grant']); r2 = save_opportunity(conn, 'Test', 'https://test.com/dedup-check', 'Snippet', 'src', ['grant']); print(f'First: {r1}, Duplicate: {r2}')"
```

**Inspect database statistics:**
```bash
python -c "import sqlite3; conn = sqlite3.connect('scout_data.db'); print('Total:', conn.execute('SELECT COUNT(*) FROM opportunities').fetchone()[0]); print('Logs:', conn.execute('SELECT * FROM run_logs ORDER BY id DESC LIMIT 3').fetchall())"
```

---

## API Documentation

The FastAPI server exposes the following REST endpoints. Full interactive documentation is available at `/docs` (Swagger UI) when the server is running.

### `GET /api/filters`

Returns the distinct sources and keywords currently stored in the database, used to populate frontend dropdown menus.

**Response:**
```json
{
  "sources": [
    "https://opportunitiesforeveryone.net/category/jobs/",
    "https://opportunitiesforeveryone.net/category/scholarships/"
  ],
  "keywords": [
    "call for applications",
    "fellowship",
    "grant",
    "internship",
    "scholarships"
  ]
}
```

---

### `GET /api/opportunities`

Returns a list of scouted opportunities with optional filtering.

**Query Parameters:**

| Parameter | Type | Default | Description |
|:--|:--|:--|:--|
| `search` | `string` | `null` | Free-text search across `title` and `snippet` fields. |
| `source` | `string` | `null` | Exact match filter on the `source` URL. |
| `keyword` | `string` | `null` | Substring match filter on `matched_keywords`. |
| `limit` | `integer` | `100` | Maximum number of results (max: 500). |

**Example Requests:**

```bash
# Fetch all opportunities
curl http://localhost:8001/api/opportunities

# Search for "Africa"
curl "http://localhost:8001/api/opportunities?search=Africa"

# Filter by keyword
curl "http://localhost:8001/api/opportunities?keyword=fellowship"

# Combine filters with limit
curl "http://localhost:8001/api/opportunities?search=UNESCO&keyword=internship&limit=10"
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Applications are now open for the IISD Geneva Internship Program...",
    "url": "https://opportunitiesforeveryone.net/...",
    "snippet": "Closing Date: 31 July 2026...",
    "source": "https://opportunitiesforeveryone.net/category/internships/",
    "matched_keywords": "internship",
    "date_discovered": "2026-07-22"
  }
]
```

---

## Deployment (Railway)

This project is configured for one-click deployment on [Railway](https://railway.app). The backend serves both the API and the React frontend from a single service.

### How It Works on Railway

1. **Build Phase**: Railway runs `cd frontend && npm install && npm run build` to compile the React dashboard into `frontend/dist/`.
2. **Start Phase**: Uvicorn launches the FastAPI app, which serves both `/api/*` endpoints and the static React build at `/`.
3. **Background Agent**: An embedded asyncio loop automatically runs a scouting cycle + WhatsApp summary every **6 hours** while the server is live.
4. **Auto-Restart**: Configured with `ON_FAILURE` restart policy (up to 10 retries).

### Deployment Steps

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy to Railway"
   git push
   ```

2. **Create Railway Service:**
   - Go to [railway.app](https://railway.app) → **+ New Project** → **Deploy from GitHub Repo**
   - Select your `scout_agent` repository

3. **Generate a Public Domain:**
   - Click on your service → **Settings** → **Networking** → **Generate Domain**
   - You'll receive a URL like `https://scout-agent-production.up.railway.app`

4. **Access Your Dashboard:**
   - `https://your-domain.up.railway.app/` — React Dashboard
   - `https://your-domain.up.railway.app/api/opportunities` — REST API
   - `https://your-domain.up.railway.app/docs` — Swagger API Docs

### Railway Configuration Files

| File | Purpose |
|:--|:--|
| `railway.json` | Build command, start command, and restart policy |
| `Procfile` | Fallback process declaration for Heroku-compatible platforms |
| `requirements.txt` | Python dependency manifest (auto-detected by Nixpacks) |

---

## Project Structure

```
opportunity-scout-agent/
│
├── scout_agent.py          # Core scouting engine (ingestion, matching, notifications)
├── api.py                  # FastAPI server + background scheduler + static file serving
├── config.json             # Runtime configuration (keywords, sources, WhatsApp credentials)
├── requirements.txt        # Python dependencies
├── scout_data.db           # SQLite database (auto-generated on first run)
│
├── Procfile                # Process declaration for Railway / Heroku
├── railway.json            # Railway-specific build and deploy configuration
│
├── frontend/               # React dashboard application
│   ├── src/
│   │   ├── App.jsx         # Main dashboard component (search, filters, results grid)
│   │   └── App.css         # Dashboard styles
│   ├── index.html          # HTML entry point
│   ├── package.json        # Node.js dependencies and scripts
│   ├── vite.config.js      # Vite bundler configuration
│   └── dist/               # Production build output (generated by `npm run build`)
│
└── README.md               # This file
```

### Database Schema

**`opportunities`** — Stores discovered opportunities

| Column | Type | Constraint | Description |
|:--|:--|:--|:--|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique row identifier |
| `title` | `TEXT` | — | Opportunity title (truncated to 100 chars for scraped items) |
| `url` | `TEXT` | `UNIQUE` | Source URL (enforces deduplication) |
| `snippet` | `TEXT` | — | Description excerpt (max 500 chars) |
| `source` | `TEXT` | — | Origin feed or page URL |
| `matched_keywords` | `TEXT` | — | Comma-separated list of matched keywords |
| `date_discovered` | `DATE` | — | Date the opportunity was first ingested |

**`run_logs`** — Tracks each scouting cycle execution

| Column | Type | Description |
|:--|:--|:--|
| `id` | `INTEGER` | Unique log identifier |
| `timestamp` | `DATETIME` | Exact time the cycle ran |
| `sources_checked` | `INTEGER` | Number of feeds + pages checked |
| `items_found` | `INTEGER` | Number of *new* (non-duplicate) items saved |
| `errors` | `TEXT` | JSON-stringified list of error messages |

---

## Troubleshooting

### Common Issues

<details>
<summary><strong>⚠️ Port already in use — <code>[WinError 10013]</code></strong></summary>

Port `8000` is commonly reserved by Windows services or Hyper-V. Use an alternate port:

```bash
python -m uvicorn api:app --reload --port 8001
```
</details>

<details>
<summary><strong>⚠️ <code>uvicorn</code> is not recognized as a command</strong></summary>

Python package executables may not be on your system PATH. Use the module invocation instead:

```bash
python -m uvicorn api:app --reload --port 8001
```
</details>

<details>
<summary><strong>⚠️ PowerShell <code>&</code> (ampersand) errors in inline Python commands</strong></summary>

PowerShell reserves `&` as an operator. Avoid constructing URLs with `&` in PowerShell strings. Instead, pass parameters as a Python dictionary:

```powershell
python -c "import requests; r = requests.get('https://api.example.com', params={'key': 'val', 'key2': 'val2'}); print(r.text)"
```
</details>

<details>
<summary><strong>⚠️ Scouting cycle returns 0 items</strong></summary>

This is expected behavior when all matching items have already been ingested. The `UNIQUE(url)` constraint prevents duplicates — `save_opportunity()` returns `False` for existing URLs, so `found_count` only increments for **new** items. To verify, clear the database and re-run:

```bash
python -c "import sqlite3; conn = sqlite3.connect('scout_data.db'); conn.execute('DELETE FROM opportunities'); conn.commit(); print('Cleared')"
python scout_agent.py
```
</details>

<details>
<summary><strong>⚠️ <code>Expected comma</code> JSON error in <code>config.json</code></strong></summary>

Standard JSON does not allow trailing commas. Ensure the last item in every array or object does **not** end with a comma:

```json
// ❌ Invalid
["item1", "item2",]

// ✅ Valid
["item1", "item2"]
```
</details>

<details>
<summary><strong>⚠️ WhatsApp messages not arriving</strong></summary>

1. Confirm you have completed the [CallMeBot setup](#setting-up-callmebot-whatsapp-notifications).
2. Test connectivity directly:
   ```bash
   python -c "import requests, json; cfg = json.load(open('config.json'))['whatsapp']; r = requests.get('https://api.callmebot.com/whatsapp.php', params={'phone': cfg['phone_number'], 'text': 'Test', 'apikey': cfg['api_key']}); print(r.status_code, r.text)"
   ```
3. CallMeBot has rate limits — wait 30 seconds between consecutive sends.
</details>

---

## Contributing

Contributions are welcome! Here's how to get started:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make** your changes and test locally
4. **Commit** with clear, descriptive messages:
   ```bash
   git commit -m "Add: support for Telegram notifications"
   ```
5. **Push** to your fork and open a **Pull Request**

### Coding Guidelines

- **Python**: Follow PEP 8 conventions. Use docstrings for all public functions.
- **JavaScript/React**: Use functional components with hooks. No class components.
- **Commits**: Use imperative mood (e.g., "Add feature" not "Added feature").
- **Configuration**: All user-facing settings belong in `config.json`, not hardcoded.

### Ideas for Contribution

- [ ] Add Telegram notification support
- [ ] Implement email digest delivery
- [ ] Add pagination to the API and dashboard
- [ ] Create a Docker deployment option
- [ ] Add unit tests with pytest
- [ ] Support additional scraping selectors beyond `h1`–`h3` and `p`

---

## License

This project is open source and available under the [MIT License](LICENSE).

---
