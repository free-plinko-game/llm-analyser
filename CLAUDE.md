# Citation Intelligence Tool

## Project Overview

A Flask application that analyses which websites get cited by ChatGPT for different query intents, specifically focused on Australian gambling affiliate market research.

## Purpose

Help identify patterns in LLM citations to inform content strategy for better visibility in AI-generated responses.

## Tech Stack

- **Backend**: Flask + SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Job Queue**: APScheduler for running citation collection jobs
- **API**: OpenAI API (ChatGPT with web browsing)
- **Analysis**: pandas for pattern analysis

## Project Structure

```
citation-intel/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Configuration management
│   ├── cli.py                # CLI commands
│   ├── models/
│   │   ├── __init__.py
│   │   ├── query.py          # Query model (the searches we run)
│   │   ├── citation.py       # Citation model (extracted URLs)
│   │   └── job_run.py        # Job execution tracking
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chatgpt_runner.py # Runs queries against ChatGPT API
│   │   ├── citation_parser.py # Extracts URLs from responses
│   │   └── domain_analyser.py # Analyses citation patterns
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── queries.py        # CRUD for query bank
│   │   ├── jobs.py           # Trigger and monitor jobs
│   │   └── analysis.py       # View analysis results
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── queries.html
│       └── analysis.html
├── migrations/               # Database migrations
├── tests/
├── .env.example
├── requirements.txt
├── run.py                    # Entry point
└── CLAUDE.md                 # This file
```

## Data Models

### Query
Stores the search queries we want to analyse.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| query_text | String | The actual search query |
| intent_type | Enum | INFORMATIONAL, NAVIGATIONAL, TRANSACTIONAL, COMMERCIAL |
| category | String | Business category (e.g., "sports betting", "casino", "poker") |
| is_active | Boolean | Whether to include in job runs |
| created_at | DateTime | When added |

### Citation
Stores each citation extracted from ChatGPT responses.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| job_run_id | Integer | FK to JobRun |
| query_id | Integer | FK to Query |
| url | String | Full cited URL |
| domain | String | Extracted domain (e.g., "betfair.com.au") |
| page_type | String | Optional classification (homepage, article, product, etc.) |
| position | Integer | Order in which it appeared in response |
| snippet | Text | Context around the citation |
| created_at | DateTime | When captured |

### JobRun
Tracks each execution of the citation collection job.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| started_at | DateTime | Job start time |
| completed_at | DateTime | Job end time |
| status | Enum | PENDING, RUNNING, COMPLETED, FAILED |
| queries_processed | Integer | Count of queries run |
| citations_found | Integer | Count of citations extracted |
| error_log | Text | Any errors encountered |

## Key Workflows

### 1. Adding Queries
- User adds queries via web UI or bulk CSV upload
- Each query tagged with intent type and business category
- Queries stored in database for repeated analysis

### 2. Running Collection Jobs
- Manual trigger or scheduled (daily/weekly)
- For each active query:
  1. Send to ChatGPT API with web search enabled
  2. Parse response for cited URLs
  3. Extract domain and metadata
  4. Store in citations table
- Track job progress and handle rate limits

### 3. Analysing Results
- Aggregate citations by domain, intent type, category
- Identify top-cited domains per intent
- Track citation frequency over time
- Export reports

## Environment Variables

```
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///citations.db
SECRET_KEY=your-secret-key
FLASK_ENV=development
```

## Commands

```bash
# Setup
pip install -r requirements.txt
flask db upgrade

# Run development server
flask run

# Run a collection job manually
flask collect-citations

# Seed demo queries
flask seed-demo-queries

# Export analysis
flask export-analysis --format csv
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /queries | List all queries |
| POST | /queries | Add new query |
| POST | /queries/bulk | Bulk upload CSV |
| DELETE | /queries/<id> | Remove query |
| POST | /jobs/run | Trigger collection job |
| GET | /jobs | List job history |
| GET | /jobs/<id> | Job details |
| GET | /analysis | View analysis dashboard |
| GET | /analysis/domains | Top domains report |
| GET | /analysis/export | Download CSV |

## Development Notes

- Start with SQLite, migrate to PostgreSQL when deploying
- Use OpenAI's responses API with web_search tool for citations
- Implement rate limiting to avoid API throttling
- Cache domain metadata to reduce repeated lookups
- Consider storing full ChatGPT responses for later re-analysis

## Australian Gambling Context

Target query categories:
- Sports betting (AFL, NRL, cricket, racing)
- Online casinos
- Poker sites
- Betting odds comparisons
- Responsible gambling info
- State-specific regulations (each state has different rules)

Example queries by intent:
- **Informational**: "how do betting odds work australia"
- **Navigational**: "sportsbet login"
- **Transactional**: "sign up bonus bet365 australia"
- **Commercial**: "best betting app australia 2025 review"

## Running Tests

```bash
pytest tests/ -v
```
