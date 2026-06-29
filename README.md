# Clinical Trial Visualization API

Backend service that converts natural language clinical trial questions into structured visualization specifications backed by [ClinicalTrials.gov](https://clinicaltrials.gov/data-api/api) data.

The API does **not** render charts or answer medical questions. It returns JSON that a frontend can use to render visualizations unambiguously.

## Features

- Natural language → structured search intent (OpenAI GPT, temperature 0)
- ClinicalTrials.gov v2 search with pagination and filters
- Aggregation by year, phase, sponsor, country, status, or intervention
- Visualization spec generation (`line_chart`, `bar_chart`, `pie_chart`, `map`)
- Structured logging, typed errors, and dependency injection

## Requirements

- Python 3.12+
- OpenAI API key
- Internet access for ClinicalTrials.gov (and OpenAI at runtime)

## Setup

```bash
git clone <repository-url>
cd ClinicaltrialAgnet

python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key
```

Optional settings:

```env
CLINICAL_TRIALS_BASE_URL=https://clinicaltrials.gov/api/v2
TIMEOUT_SECONDS=30
OPENAI_MODEL=gpt-4o
LOG_LEVEL=INFO
CLINICAL_TRIALS_PAGE_SIZE=100
CLINICAL_TRIALS_MAX_PAGES=50
```

## Running locally

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## API

### `POST /query`

Convert a natural language question into a visualization specification.

#### Request schema

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | Natural language clinical trial question (3–2000 chars) |
| `drug_name` | string | No | Drug or intervention filter |
| `condition` | string | No | Disease or condition filter |
| `trial_phase` | string | No | Phase filter (e.g. `"Phase 2"`) |
| `sponsor` | string | No | Sponsor or organization filter |
| `country` | string | No | Country or location filter |
| `start_year` | integer | No | Inclusive lower bound on study start year |
| `end_year` | integer | No | Inclusive upper bound on study start year |

#### Example request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How has the number of breast cancer trials changed over time?"
  }'
```

With explicit filters:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How has the number of trials for this drug changed over time?",
    "drug_name": "Pembrolizumab"
  }'
```

#### Example response

```json
{
  "visualization": {
    "type": "line_chart",
    "title": "Breast Cancer Trials Over Time",
    "encoding": {
      "x": { "field": "year", "label": "Year", "type": "temporal" },
      "y": { "field": "trial_count", "label": "Trial Count", "type": "quantitative" }
    },
    "data": [
      { "year": 2018, "trial_count": 42 },
      { "year": 2019, "trial_count": 51 },
      { "year": 2020, "trial_count": 67 }
    ]
  },
  "meta": {
    "filters": {
      "condition": "Breast Cancer",
      "group_by": "year",
      "metric": "trial_count"
    },
    "record_count": 160,
    "source": "ClinicalTrials.gov",
    "notes": []
  }
}
```

Bar chart example:

```json
{
  "visualization": {
    "type": "bar_chart",
    "title": "Trials for Pembrolizumab by Phase",
    "encoding": {
      "x": { "field": "phase", "type": "nominal" },
      "y": { "field": "trial_count", "type": "quantitative" }
    },
    "data": [
      { "phase": "Phase 1", "trial_count": 32 },
      { "phase": "Phase 2", "trial_count": 78 }
    ]
  },
  "meta": {
    "filters": { "drug": "Pembrolizumab", "group_by": "phase", "metric": "trial_count" },
    "record_count": 110,
    "source": "ClinicalTrials.gov",
    "notes": []
  }
}
```

#### Error responses

| Status | Meaning |
|---|---|
| `422` | Invalid request body |
| `404` | No matching studies found |
| `400` | Cannot build visualization from results |
| `502` | OpenAI or ClinicalTrials.gov upstream error |
| `504` | Upstream timeout |
| `500` | Unexpected application error |

## Architecture

```
User Prompt
     │
     ▼
LLM Intent Parser          (OpenAI Responses API)
     │
     ▼
Structured Search Intent
     │
     ▼
ClinicalTrials.gov Client  (async httpx, paginated)
     │
     ▼
Raw Study Data
     │
     ▼
Aggregation Layer          (count / proportion by dimension)
     │
     ▼
Visualization Selector     (line, bar, pie, map)
     │
     ▼
Visualization JSON
```

## Project layout

```
app/
  main.py                  FastAPI entry point
  api/routes.py            HTTP routes
  api/deps.py              Dependency injection
  core/                    Config, logging, exceptions
  models/                  Pydantic request/response models
  services/                Business logic
  clients/                 OpenAI + ClinicalTrials.gov clients
  prompts/                 LLM prompt templates
tests/                     Unit and integration tests
```

## Testing

Run unit tests (mocked, no external calls):

```bash
pytest -m "not integration"
```

Run live ClinicalTrials.gov integration tests:

```bash
pytest -m integration
```

Run the full suite:

```bash
pytest
```

## Data source

Study data is retrieved from the [ClinicalTrials.gov Data API v2](https://clinicaltrials.gov/data-api/api). The LLM is used only to extract structured search intent — it does not provide medical advice or interpret trial results.

## License

See repository license file.
