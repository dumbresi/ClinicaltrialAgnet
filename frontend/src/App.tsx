import { useEffect, useState } from 'react'
import { checkHealth, QueryApiError, submitQuery } from './api/client'
import { ErrorAlert } from './components/ErrorAlert'
import { MetaPanel } from './components/MetaPanel'
import { QueryForm } from './components/QueryForm'
import { VisualizationRenderer } from './components/VisualizationRenderer'
import type { QueryRequest, VisualizationResponse } from './types/api'
import './App.css'

function App() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<{ message: string; status?: number } | null>(null)
  const [result, setResult] = useState<VisualizationResponse | null>(null)
  const [apiOnline, setApiOnline] = useState<boolean | null>(null)

  useEffect(() => {
    checkHealth().then(setApiOnline)
  }, [])

  async function handleSubmit(request: QueryRequest) {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await submitQuery(request)
      setResult(response)
    } catch (err) {
      if (err instanceof QueryApiError) {
        setError({ message: err.message, status: err.status })
      } else {
        setError({
          message: 'Unable to reach the API. Make sure the backend is running on port 8000.',
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="brand">
            <div className="brand-icon" aria-hidden="true">
              CT
            </div>
            <div>
              <h1>Clinical Trial Explorer</h1>
              <p>Natural language insights from ClinicalTrials.gov</p>
            </div>
          </div>
          <div className={`status-pill ${apiOnline ? 'online' : 'offline'}`}>
            <span className="status-dot" />
            {apiOnline === null ? 'Checking API…' : apiOnline ? 'API connected' : 'API offline'}
          </div>
        </div>
      </header>

      <main className="app-main">
        <section className="query-section">
          <QueryForm loading={loading} onSubmit={handleSubmit} />
        </section>

        {loading && (
          <div className="loading-state" aria-live="polite">
            <div className="spinner" />
            <p>Planning query, fetching trials, and building visualization…</p>
            <p className="loading-hint">This may take a moment for broad searches.</p>
          </div>
        )}

        {error && <ErrorAlert message={error.message} status={error.status} />}

        {result && !loading && (
          <section className="results-section">
            <VisualizationRenderer spec={result.visualization} />
            <MetaPanel meta={result.meta} />
          </section>
        )}

        {!result && !loading && !error && (
          <section className="empty-state">
            <h2>Ask anything about clinical trials</h2>
            <p>
              Describe trends, comparisons, distributions, or geographic breakdowns. The backend
              plans your query, fetches data from ClinicalTrials.gov, and returns a chart-ready
              specification.
            </p>
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Data from{' '}
          <a href="https://clinicaltrials.gov" target="_blank" rel="noreferrer">
            ClinicalTrials.gov
          </a>
          . For research purposes only — not medical advice.
        </p>
      </footer>
    </div>
  )
}

export default App
