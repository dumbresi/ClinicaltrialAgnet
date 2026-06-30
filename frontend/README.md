# Clinical Trial Explorer — Frontend

Vite + React frontend for the Clinical Trial Visualization API.

## Setup

```bash
cd frontend
npm install
```

## Development

Start the backend first (from the repo root):

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then start the frontend dev server:

```bash
cd frontend
npm run dev
```

Open http://localhost:5173.

By default, API requests go to `/api`, which the Vite dev server proxies to `http://localhost:8000`. You do not need a `.env` file for local development.

## Production build

```bash
npm run build
npm run preview
```

Set `VITE_API_BASE_URL` to your deployed API base URL when not using the dev proxy:

```env
VITE_API_BASE_URL=https://your-api-host
```

## Features

- Natural language query input with example prompts
- Optional structured filters (drug, condition, phase, sponsor, country, year range)
- Renders all backend visualization types: line, bar, grouped/stacked bar, pie, scatter, table, map, network graph, and KPI
- Query metadata panel with execution plan and applied filters

See the [root README](../README.md) for full project setup, API docs, and architecture.
