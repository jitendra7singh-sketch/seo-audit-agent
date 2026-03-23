# 🔍 SEO Audit & Competitive Analysis Agent

A self-hosted AI-powered SEO audit platform that runs on **GitHub Actions** with a **GitHub Pages** frontend.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   GitHub Pages (UI)                  │
│   React SPA — Dashboard, Reports, Action Plans       │
└──────────────────┬──────────────────────────────────┘
                   │ reads JSON artifacts from
                   ▼
┌─────────────────────────────────────────────────────┐
│              GitHub Actions (Backend)                 │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────┐     │
│  │ Keyword  │  │Competitor│  │  Gap Analysis    │     │
│  │ Agent    │  │ Agent    │  │  Agent           │     │
│  └────┬─────┘  └────┬─────┘  └───────┬─────────┘     │
│       │              │                │               │
│  ┌────▼──────────────▼────────────────▼─────────┐    │
│  │            API Connectors Layer                │    │
│  │  GSC │ GA4 │ Google Ads │ SEMrush             │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Output → gh-pages branch as JSON data files         │
└─────────────────────────────────────────────────────┘
```

## How It Works

1. **Configure** — Set your API keys as GitHub Secrets
2. **Trigger** — Run the audit via GitHub Actions (manual or scheduled)
3. **Agents Execute** — Python agents call APIs, analyze data, generate reports
4. **Deploy** — Results are committed as JSON to `gh-pages` branch
5. **View** — React dashboard on GitHub Pages reads and displays the data

## Quick Start

### 1. Fork this repository

### 2. Set GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `GSC_SERVICE_ACCOUNT_JSON` | Google Search Console service account JSON |
| `GA4_PROPERTY_ID` | Google Analytics 4 property ID |
| `GA4_SERVICE_ACCOUNT_JSON` | GA4 service account JSON |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads API developer token |
| `GOOGLE_ADS_CLIENT_ID` | Google Ads OAuth client ID |
| `GOOGLE_ADS_CLIENT_SECRET` | Google Ads OAuth client secret |
| `GOOGLE_ADS_REFRESH_TOKEN` | Google Ads OAuth refresh token |
| `GOOGLE_ADS_CUSTOMER_ID` | Google Ads customer ID |
| `SEMRUSH_API_KEY` | SEMrush API key |

### 3. Configure your project

Edit `config/audit-config.json`:

```json
{
  "website_url": "https://yoursite.com",
  "business_name": "Your Business",
  "category": "Travel Ticket Booking",
  "target_market": "India",
  "keyword_count": 5000,
  "competitor_page_count": 2000,
  "min_referring_da": 30
}
```

### 4. Run the audit

- **Manual**: Go to Actions → "Run SEO Audit" → Run workflow
- **Scheduled**: Runs weekly on Monday at 6 AM UTC by default

### 5. View results

Visit `https://<your-username>.github.io/<repo-name>/`

## Project Structure

```
seo-audit-agent/
├── .github/workflows/
│   ├── run-audit.yml          # Main audit pipeline
│   ├── deploy-frontend.yml    # Build & deploy React to gh-pages
│   └── scheduled-audit.yml    # Cron-based weekly audit
├── backend/
│   ├── main.py                # Orchestrator — runs all agents
│   ├── agents/
│   │   ├── keyword_agent.py   # Keyword research & grouping
│   │   ├── competitor_agent.py# Competitor discovery & validation
│   │   ├── pages_agent.py     # Top pages analysis
│   │   ├── gap_agent.py       # Keyword & content gap analysis
│   │   ├── backlink_agent.py  # Backlink & referring domain gaps
│   │   ├── interlink_agent.py # Internal linking analysis
│   │   └── action_plan_agent.py # AI-generated action plan
│   ├── connectors/
│   │   ├── gsc_connector.py   # Google Search Console
│   │   ├── ga4_connector.py   # Google Analytics 4
│   │   ├── gads_connector.py  # Google Ads (keyword planner)
│   │   └── semrush_connector.py # SEMrush API
│   ├── models/
│   │   └── schemas.py         # Pydantic data models
│   └── utils/
│       ├── grouping.py        # Keyword clustering/grouping
│       └── scoring.py         # Opportunity scoring
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/             # Dashboard, Keywords, Gaps, etc.
│   │   ├── components/        # Reusable UI components
│   │   ├── hooks/             # Data loading hooks
│   │   └── utils/             # Helpers
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── config/
│   └── audit-config.json      # Your project configuration
├── scripts/
│   └── publish-data.sh        # Pushes JSON to gh-pages
├── requirements.txt
└── README.md
```

## GitHub Actions Workflows

### `run-audit.yml` — Full SEO Audit
Triggered manually or by schedule. Runs all agents in sequence, outputs JSON data, then deploys frontend.

### `deploy-frontend.yml` — Frontend Only
Builds the React app and deploys to GitHub Pages. Triggered on push to `main` or after audit completes.

## Extending

### Adding a new data source
1. Create a connector in `backend/connectors/`
2. Create an agent in `backend/agents/`
3. Register it in `backend/main.py`
4. Add a page/section in the frontend

### Custom keyword grouping
Edit `backend/utils/grouping.py` to change clustering logic.

## License

MIT
