import { useState, type FormEvent } from 'react'
import type { QueryRequest } from '../types/api'

const EXAMPLE_QUERIES = [
  'How has the number of breast cancer trials changed over time?',
  'Compare Pembrolizumab and Nivolumab clinical trials by phase',
  'How many recruiting oncology trials are there by country?',
  'What is the distribution of trial phases for diabetes studies?',
]

interface QueryFormProps {
  loading: boolean
  onSubmit: (request: QueryRequest) => void
}

const emptyFilters = {
  drug_name: '',
  condition: '',
  trial_phase: '',
  sponsor: '',
  country: '',
  start_year: '',
  end_year: '',
}

export function QueryForm({ loading, onSubmit }: QueryFormProps) {
  const [query, setQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState(emptyFilters)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!query.trim() || loading) return

    const request: QueryRequest = { query: query.trim() }
    if (filters.drug_name.trim()) request.drug_name = filters.drug_name.trim()
    if (filters.condition.trim()) request.condition = filters.condition.trim()
    if (filters.trial_phase.trim()) request.trial_phase = filters.trial_phase.trim()
    if (filters.sponsor.trim()) request.sponsor = filters.sponsor.trim()
    if (filters.country.trim()) request.country = filters.country.trim()
    if (filters.start_year) request.start_year = Number(filters.start_year)
    if (filters.end_year) request.end_year = Number(filters.end_year)

    onSubmit(request)
  }

  function applyExample(example: string) {
    setQuery(example)
  }

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor="query">
        Ask a question about clinical trials
      </label>
      <textarea
        id="query"
        className="query-input"
        rows={3}
        placeholder="e.g. How has the number of breast cancer trials changed over time?"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        disabled={loading}
        required
        minLength={3}
        maxLength={2000}
      />

      <div className="example-queries">
        <span className="example-label">Try an example:</span>
        <div className="example-chips">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              type="button"
              className="chip"
              onClick={() => applyExample(example)}
              disabled={loading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        className="filters-toggle"
        onClick={() => setShowFilters((open) => !open)}
        aria-expanded={showFilters}
      >
        {showFilters ? 'Hide filters' : 'Show optional filters'}
      </button>

      {showFilters && (
        <div className="filters-grid">
          <div className="filter-field">
            <label htmlFor="drug_name">Drug / intervention</label>
            <input
              id="drug_name"
              type="text"
              value={filters.drug_name}
              onChange={(event) =>
                setFilters((current) => ({ ...current, drug_name: event.target.value }))
              }
              disabled={loading}
              placeholder="Pembrolizumab"
            />
          </div>
          <div className="filter-field">
            <label htmlFor="condition">Condition</label>
            <input
              id="condition"
              type="text"
              value={filters.condition}
              onChange={(event) =>
                setFilters((current) => ({ ...current, condition: event.target.value }))
              }
              disabled={loading}
              placeholder="Breast Cancer"
            />
          </div>
          <div className="filter-field">
            <label htmlFor="trial_phase">Trial phase</label>
            <input
              id="trial_phase"
              type="text"
              value={filters.trial_phase}
              onChange={(event) =>
                setFilters((current) => ({ ...current, trial_phase: event.target.value }))
              }
              disabled={loading}
              placeholder="Phase 2"
            />
          </div>
          <div className="filter-field">
            <label htmlFor="sponsor">Sponsor</label>
            <input
              id="sponsor"
              type="text"
              value={filters.sponsor}
              onChange={(event) =>
                setFilters((current) => ({ ...current, sponsor: event.target.value }))
              }
              disabled={loading}
            />
          </div>
          <div className="filter-field">
            <label htmlFor="country">Country</label>
            <input
              id="country"
              type="text"
              value={filters.country}
              onChange={(event) =>
                setFilters((current) => ({ ...current, country: event.target.value }))
              }
              disabled={loading}
              placeholder="United States"
            />
          </div>
          <div className="filter-field">
            <label htmlFor="start_year">Start year</label>
            <input
              id="start_year"
              type="number"
              min={1900}
              max={2100}
              value={filters.start_year}
              onChange={(event) =>
                setFilters((current) => ({ ...current, start_year: event.target.value }))
              }
              disabled={loading}
            />
          </div>
          <div className="filter-field">
            <label htmlFor="end_year">End year</label>
            <input
              id="end_year"
              type="number"
              min={1900}
              max={2100}
              value={filters.end_year}
              onChange={(event) =>
                setFilters((current) => ({ ...current, end_year: event.target.value }))
              }
              disabled={loading}
            />
          </div>
        </div>
      )}

      <button type="submit" className="submit-button" disabled={loading || !query.trim()}>
        {loading ? 'Analyzing trials…' : 'Generate visualization'}
      </button>
    </form>
  )
}
