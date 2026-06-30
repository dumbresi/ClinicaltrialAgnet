# Clinical Trial Explorer

Full-stack application that converts natural language clinical trial questions into interactive visualizations backed by [ClinicalTrials.gov](https://clinicaltrials.gov/data-api/api) data.

- **Web UI** (`frontend/`) — React app for querying and rendering charts, tables, maps, and more
- **API** (`app/`) — FastAPI service that plans queries, fetches trial data, aggregates results, and returns structured visualization specs

The API does not answer medical questions. It returns JSON that the frontend (or any client) can render unambiguously.

## Features

### Query & planning

- **Dynamic query planning** — OpenAI produces an execution plan (intent, entities, filters, metric, group_by, visualization), not raw API parameters
- **Multi-request search** — comparison queries (e.g. Drug A vs Drug B) issue separate ClinicalTrials.gov requests per entity
- **Full pagination** — fetches all pages until `nextPageToken` is absent (optional safety cap via env)
- **Comparison & multi-entity support** — drugs, conditions, sponsors, countries, phases, and more as separate series

### Data processing

- **Registry-based aggregation** — reusable operations (`group_by`, `proportion`, `top_n`, `network_edges`, histograms, etc.) with unique NCT-ID counting
- **Registry-based visualization** — one builder class per chart type with automatic encoding

### Web UI

- Natural language query input with example prompts
- Optional structured filters (drug, condition, phase, sponsor, country, year range)
- Renders all backend visualization types: line, bar, grouped/stacked bar, pie, scatter, table, map, network graph, and KPI
- Query metadata panel with execution plan and applied filters

### Operations

- Structured logging, typed errors, and dependency injection
- CORS configured for local frontend development

## Requirements

- Python 3.12+
- Node.js 18+ (for the frontend)
- OpenAI API key
- Internet access for ClinicalTrials.gov (and OpenAI at runtime)

## Setup

### Backend

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
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
CLINICAL_TRIALS_PAGE_SIZE=100
CLINICAL_TRIALS_MAX_PAGES=50     # omit or leave unset for unlimited pagination
```

### Frontend

```bash
cd frontend
npm install
```

For local development, the Vite dev server proxies `/api` to the backend — no frontend `.env` is required. For production builds, set the API URL:

```env
VITE_API_BASE_URL=https://your-api-host
```

## Running locally

Start the backend from the repo root:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal, start the frontend:

```bash
cd frontend
npm run dev
```

| Service | URL |
|---|---|
| Web app | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

### Production build (frontend)

```bash
cd frontend
npm run build
npm run preview
```

See [frontend/README.md](frontend/README.md) for frontend-specific details.

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

Explicit filter fields override LLM output when provided.

#### Example requests

Trend over time:

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

Comparison query (issues one ClinicalTrials.gov request per entity, then merges results as separate chart series):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare recruiting Phase 3 Pembrolizumab trials in the United States and Canada by status"
  }'
```

Network graph (co-occurrence edges between interventions and sponsors, counted by unique NCT ID):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show the relationship between interventions and sponsors in breast cancer trials"
  }'
```

#### Example response (time series)

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
    "query_plan": {
      "intent": "trend",
      "entities": [],
      "filters": { "condition": "Breast Cancer" },
      "metric": "trial_count",
      "group_by": "year",
      "visualization": "line_chart",
      "comparison": false
    },
    "filters": {
      "condition": "Breast Cancer",
      "group_by": "year",
      "metric": "trial_count"
    },
    "api_calls": 1,
    "studies_processed": 18342,
    "records_after_filter": 160,
    "aggregation": "trial_count_by_year",
    "generated_at": "2026-06-29T12:00:00+00:00",
    "source": "ClinicalTrials.gov",
    "notes": []
  }
}
```

#### Example response (comparison / grouped bar)

Comparison queries run **one API request per entity** (e.g. United States vs Canada), tag each study with its series label, then aggregate into a grouped chart. The `series` encoding tells the frontend which field distinguishes the compared arms.

```json
{
  "visualization": {
    "type": "grouped_bar_chart",
    "title": "Pembrolizumab Trials by Status: United States vs Canada",
    "encoding": {
      "x": { "field": "status", "label": "Status", "type": "nominal" },
      "y": { "field": "trial_count", "label": "Trial Count", "type": "quantitative" },
      "series": { "field": "country", "label": "Country", "type": "nominal" }
    },
    "data": [
      { "country": "United States", "status": "Recruiting", "trial_count": 48 },
      { "country": "Canada", "status": "Recruiting", "trial_count": 12 },
      { "country": "United States", "status": "Completed", "trial_count": 31 },
      { "country": "Canada", "status": "Completed", "trial_count": 9 }
    ]
  },
  "meta": {
    "query_plan": {
      "intent": "comparison",
      "entities": [
        { "type": "country", "value": "United States" },
        { "type": "country", "value": "Canada" }
      ],
      "filters": {
        "drug": "Pembrolizumab",
        "phase": "Phase 3",
        "status": "RECRUITING"
      },
      "metric": "trial_count",
      "group_by": "status",
      "visualization": "grouped_bar_chart",
      "comparison": true
    },
    "filters": {
      "drug": "Pembrolizumab",
      "phase": "Phase 3",
      "status": "RECRUITING",
      "group_by": "status",
      "metric": "trial_count",
      "comparison": true
    },
    "api_calls": 2,
    "studies_processed": 186,
    "records_after_filter": 100,
    "aggregation": "trial_count_by_country_by_status",
    "generated_at": "2026-06-29T12:00:00+00:00",
    "source": "ClinicalTrials.gov",
    "notes": []
  }
}
```

#### Example response (network graph)

Relationship queries build **co-occurrence edges** between two dimensions (e.g. intervention ↔ sponsor). Each edge weight is the number of unique trials where both values appear. The frontend renders nodes and weighted links from `source`, `target`, and `trial_count`.

```json
{
  "visualization": {
    "type": "network_graph",
    "title": "Intervention–Sponsor Relationships in Breast Cancer Trials",
    "encoding": {
      "source": { "field": "source", "label": "Intervention", "type": "nominal" },
      "target": { "field": "target", "label": "Sponsor", "type": "nominal" },
      "value": { "field": "trial_count", "label": "Trial Count", "type": "quantitative" }
    },
    "data": [
      {
        "source": "Pembrolizumab",
        "target": "Merck Sharp & Dohme LLC",
        "trial_count": 42
      },
      {
        "source": "Trastuzumab",
        "target": "Genentech, Inc.",
        "trial_count": 37
      },
      {
        "source": "Pembrolizumab",
        "target": "National Cancer Institute (NCI)",
        "trial_count": 18
      }
    ]
  },
  "meta": {
    "query_plan": {
      "intent": "relationship",
      "entities": [],
      "filters": { "condition": "Breast Cancer" },
      "metric": "trial_count",
      "group_by": null,
      "visualization": "network_graph",
      "comparison": false,
      "network_source": "intervention",
      "network_target": "sponsor"
    },
    "filters": {
      "condition": "Breast Cancer",
      "metric": "trial_count"
    },
    "api_calls": 1,
    "studies_processed": 8240,
    "records_after_filter": 8240,
    "aggregation": "trial_count",
    "generated_at": "2026-06-29T12:00:00+00:00",
    "source": "ClinicalTrials.gov",
    "notes": []
  }
}
```

#### Supported visualization types

| Type | Typical use |
|---|---|
| `line_chart` | Trends over time (`group_by: year`) |
| `bar_chart` | Single-series category counts |
| `grouped_bar_chart` | Comparisons across categories |
| `stacked_bar_chart` | Part-to-whole comparisons across series |
| `pie_chart` | Proportions / distributions |
| `scatter_plot` | Numeric relationships (e.g. enrollment) |
| `table` | Detailed tabular output |
| `map` | Geographic breakdown by country |
| `network_graph` | Entity relationships (drug–sponsor, etc.) |
| `kpi` | Single total count |

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

The pipeline is fully generic — no hardcoded query-type branches. The LLM describes *what* to analyze; downstream services decide *how*.

```
User Prompt (web UI or API client)
     │
     ▼
Query Planner              (OpenAI structured output → ExecutionPlan)
     │
     ▼
Query Builder              (1..N ClinicalTrials.gov request specs)
     │
     ▼
ClinicalTrials.gov Client  (async httpx, full pagination)
     │
     ▼
Tagged Study Records       (series labels for comparisons)
     │
     ▼
Aggregation Engine         (registry of reusable operations)
     │
     ▼
Visualization Engine       (registry of chart builders)
     │
     ▼
Visualization JSON + meta  → rendered in React (Recharts)
```

### Execution plan

The LLM produces an `ExecutionPlan`, not API parameters:

```json
{
  "intent": "comparison",
  "entities": [
    { "type": "drug", "value": "Pembrolizumab" },
    { "type": "drug", "value": "Nivolumab" }
  ],
  "filters": {
    "status": "RECRUITING",
    "country": "United States"
  },
  "metric": "trial_count",
  "group_by": "phase",
  "visualization": "grouped_bar_chart",
  "comparison": true
}
```

Supported entity/filter dimensions include drugs, conditions, sponsors, countries, phases, statuses, intervention types, study types, enrollment bounds, and date ranges.

### Aggregation

Operations are registered in `app/aggregation/registry.py` and composed automatically from the execution plan:

- `count`, `group_by`, `sum`, `average`, `median`, `unique`
- `top_n`, `sort`, `proportion`
- `date_histogram`, `phase_histogram`, `country_histogram`, `status_histogram`, `sponsor_histogram`
- `network_edges`

Studies are counted by unique NCT ID per bucket. Country and intervention grouping deduplicates values within each study so facility locations do not inflate counts.

### Extending the system

| Add | Where |
|---|---|
| New chart type | `app/visualization/builders/` + register in `app/visualization/registry.py`; add renderer in `frontend/src/components/VisualizationRenderer.tsx` |
| New aggregation | `app/aggregation/operations/` + register in `app/aggregation/registry.py` |
| New filter dimension | `PlanFilters` in `app/models/execution_plan.py` + `app/services/query_builder.py` + planner prompt |

## Project layout

```
app/                            FastAPI backend
  main.py                       Application entry point
  api/                          Routes and dependency injection
  core/                         Config, logging, exceptions
  models/
    execution_plan.py           ExecutionPlan, PlanEntity, PlanFilters
    request.py                  UserQuery
    response.py                 VisualizationResponse, MetaData
    clinical_trials.py          StudyRecord, MultiSearchResult
  services/
    query_planner_service.py    LLM → ExecutionPlan
    query_builder.py            ExecutionPlan → API request specs
    query_service.py            Pipeline orchestration
    clinical_trials_service.py  Multi-request fetch + tagging
    aggregation_service.py      Thin wrapper over AggregationEngine
    visualization_service.py    Thin wrapper over VisualizationEngine
  aggregation/
    engine.py                   Pipeline derivation and execution
    registry.py                 Operation registry
    operations/                   Individual aggregation strategies
  visualization/
    engine.py                   Chart type resolution and spec building
    registry.py                 Builder registry
    builders/                   One class per chart type
  clients/                      OpenAI + ClinicalTrials.gov HTTP clients
  prompts/
    query_planner.txt           LLM query planner instructions

frontend/                       Vite + React web UI
  src/
    api/client.ts               API client (/api proxy in dev)
    components/
      QueryForm.tsx             Query input and filters
      VisualizationRenderer.tsx Chart/table/map rendering (Recharts)
      MetaPanel.tsx             Execution plan and metadata
      ErrorAlert.tsx            Error display
    types/api.ts                Shared TypeScript types

tests/                          Unit and integration tests
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

## Backend development notes

### What was built

The backend is a FastAPI service that turns natural language questions into structured visualization specs. A user sends a query; OpenAI produces an **execution plan** describing analytical intent — what to count, group by, and chart. Downstream code, not the LLM, decides how to search ClinicalTrials.gov, aggregate studies, and build the chart spec. That separation keeps the pipeline generic: new chart types and aggregations are added by registering new operations, not by branching on query text.

Development moved in three stages. First, a working end-to-end path: API route, ClinicalTrials.gov client with full pagination, OpenAI integration, and basic aggregation and visualization. Second, a refactor into the current planner/executor model with registry-based engines so comparison queries, network graphs, and KPIs all share the same pipeline. Third, hardening: validating plans before any API call, normalizing network-graph labels, and tightening how comparison queries map entities to separate API requests.

### Tools used

Python 3.12, FastAPI, Pydantic v2, and httpx form the core. OpenAI (`gpt-4o-mini`) generates structured execution plans from `app/prompts/query_planner.txt`. Study data comes from the [ClinicalTrials.gov Data API v2](https://clinicaltrials.gov/data-api/api). Tests use pytest and pytest-asyncio. Cursor was used as the IDE and for AI-assisted coding during implementation.

### How correctness was validated

Correctness was checked at every layer. Unit tests (70+, fully mocked) exercise the query builder, plan validator, aggregation operations, visualization builders, HTTP clients, models, and API routes — runnable with `pytest -m "not integration"`. A smaller set of integration tests hits the live ClinicalTrials.gov API to verify pagination, search parameters, and response parsing. Pipeline tests run the full orchestration path with the LLM and external API mocked. Manual checks through Swagger UI and the `curl` examples in this README confirmed comparison and multi-entity queries against real result counts.

Tests specifically guard against: comparison queries issuing one API request per entity (not repeating every entity on each request), rejection of off-topic questions, warnings when a location looks like a region rather than a country, and inflation of counts from duplicate NCT IDs or unnormalized graph node labels.

### Deliberate design vs generated and adapted

**Deliberate design choices** shaped the architecture:

- The **execution plan** is the contract between the LLM and the rest of the system. It captures intent, entities, filters, metric, group_by, and visualization — never raw API parameters.
- **QueryBuilder** translates plans into ClinicalTrials.gov v2 query syntax, including `AREA[...]` advanced filters for phase, enrollment, and date ranges.
- **Registry-based engines** derive aggregation pipelines and chart specs at runtime from the plan, using pluggable operations (`group_by`, `proportion`, `top_n`, `network_edges`, etc.) and one builder per chart type.
- **Multi-request comparisons** issue a separate paginated search per compared entity, tag results with series labels, and merge them for grouped or stacked charts.
- **PlanValidator** rejects plans with no actionable search criteria and warns on ambiguous inputs (e.g. "Europe" instead of a specific country).

**Generated and adapted** pieces were bootstrapped quickly and refined through testing:

- The initial FastAPI layout, dependency injection, config, and logging were scaffolded with AI assistance, then reorganized when the monolithic services were split into the registry pattern.
- The query planner prompt was drafted with AI help and tightened over several iterations as edge cases surfaced (off-topic queries, comparison entity placement, region-like locations).
- The ClinicalTrials.gov client was adapted from API documentation; field extraction and pagination were adjusted after integration tests exposed real response shapes.
- Individual aggregation operations and chart builders follow a shared template pattern, with per-type customization where needed (network edge deduplication, map encoding for countries).

## Data source

Study data is retrieved from the [ClinicalTrials.gov Data API v2](https://clinicaltrials.gov/data-api/api). The LLM is used only to produce structured execution plans — it does not provide medical advice or interpret trial results.

