import type { ApiError, QueryRequest, VisualizationResponse } from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class QueryApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'QueryApiError'
    this.status = status
  }
}

function formatErrorDetail(detail: ApiError['detail']): string {
  if (typeof detail === 'string') {
    return detail
  }
  return detail.map((item) => item.msg).join('; ')
}

export async function submitQuery(request: QueryRequest): Promise<VisualizationResponse> {
  const body: Record<string, unknown> = { query: request.query.trim() }

  if (request.drug_name?.trim()) body.drug_name = request.drug_name.trim()
  if (request.condition?.trim()) body.condition = request.condition.trim()
  if (request.trial_phase?.trim()) body.trial_phase = request.trial_phase.trim()
  if (request.sponsor?.trim()) body.sponsor = request.sponsor.trim()
  if (request.country?.trim()) body.country = request.country.trim()
  if (request.start_year != null) body.start_year = request.start_year
  if (request.end_year != null) body.end_year = request.end_year

  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const payload = (await response.json()) as ApiError
      if (payload.detail) {
        message = formatErrorDetail(payload.detail)
      }
    } catch {
      // keep default message
    }
    throw new QueryApiError(message, response.status)
  }

  return response.json() as Promise<VisualizationResponse>
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`)
    return response.ok
  } catch {
    return false
  }
}
