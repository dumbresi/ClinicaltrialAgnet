import type { MetaData } from '../types/api'

interface MetaPanelProps {
  meta: MetaData
}

export function MetaPanel({ meta }: MetaPanelProps) {
  const generatedAt = meta.generated_at
    ? new Date(meta.generated_at).toLocaleString()
    : '—'

  return (
    <aside className="meta-panel">
      <h3>Query details</h3>

      <dl className="meta-stats">
        <div>
          <dt>Studies processed</dt>
          <dd>{meta.studies_processed.toLocaleString()}</dd>
        </div>
        <div>
          <dt>Records after filter</dt>
          <dd>{meta.records_after_filter.toLocaleString()}</dd>
        </div>
        <div>
          <dt>API calls</dt>
          <dd>{meta.api_calls}</dd>
        </div>
        <div>
          <dt>Aggregation</dt>
          <dd>{meta.aggregation || '—'}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>{meta.source}</dd>
        </div>
        <div>
          <dt>Generated</dt>
          <dd>{generatedAt}</dd>
        </div>
      </dl>

      {meta.notes.length > 0 && (
        <div className="meta-notes">
          <h4>Notes</h4>
          <ul>
            {meta.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      <details className="meta-details">
        <summary>Execution plan</summary>
        <pre>{JSON.stringify(meta.query_plan, null, 2)}</pre>
      </details>

      <details className="meta-details">
        <summary>Applied filters</summary>
        <pre>{JSON.stringify(meta.filters, null, 2)}</pre>
      </details>
    </aside>
  )
}
