export type VisualizationType =
  | 'line_chart'
  | 'bar_chart'
  | 'grouped_bar_chart'
  | 'stacked_bar_chart'
  | 'pie_chart'
  | 'scatter_plot'
  | 'table'
  | 'map'
  | 'network_graph'
  | 'kpi'

export interface EncodingChannel {
  field: string
  label?: string | null
  type?: 'quantitative' | 'ordinal' | 'nominal' | 'temporal' | null
}

export interface VisualizationEncoding {
  x?: EncodingChannel | null
  y?: EncodingChannel | null
  series?: EncodingChannel | null
  source?: EncodingChannel | null
  target?: EncodingChannel | null
  value?: EncodingChannel | null
  label?: EncodingChannel | null
  geo?: EncodingChannel | null
}

export interface VisualizationSpec {
  type: VisualizationType
  title: string
  encoding: VisualizationEncoding
  data: Record<string, unknown>[]
}

export interface MetaData {
  query_plan: Record<string, unknown>
  filters: Record<string, unknown>
  api_calls: number
  studies_processed: number
  records_after_filter: number
  aggregation: string
  generated_at: string
  source: string
  notes: string[]
}

export interface VisualizationResponse {
  visualization: VisualizationSpec
  meta: MetaData
}

export interface QueryRequest {
  query: string
  drug_name?: string
  condition?: string
  trial_phase?: string
  sponsor?: string
  country?: string
  start_year?: number
  end_year?: number
}

export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[]
}
