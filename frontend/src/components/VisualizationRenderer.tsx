import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { VisualizationSpec } from '../types/api'

const CHART_COLORS = [
  '#0d9488',
  '#2563eb',
  '#7c3aed',
  '#db2777',
  '#ea580c',
  '#ca8a04',
  '#059669',
  '#4f46e5',
]

function channelLabel(
  channel: { field: string; label?: string | null } | null | undefined,
  fallback: string,
): string {
  return channel?.label ?? channel?.field ?? fallback
}

function asNumber(value: unknown): number {
  if (typeof value === 'number') return value
  if (typeof value === 'string' && value.trim() !== '') return Number(value)
  return 0
}

function asString(value: unknown): string {
  if (value == null) return ''
  return String(value)
}

function pivotGroupedData(
  data: Record<string, unknown>[],
  xField: string,
  seriesField: string,
  yField: string,
): { rows: Record<string, string | number>[]; seriesKeys: string[] } {
  const seriesSet = new Set<string>()
  const rowMap = new Map<string, Record<string, string | number>>()

  for (const row of data) {
    const xValue = asString(row[xField])
    const seriesValue = asString(row[seriesField])
    const yValue = asNumber(row[yField])
    seriesSet.add(seriesValue)

    const existing = rowMap.get(xValue) ?? { [xField]: xValue }
    existing[seriesValue] = yValue
    rowMap.set(xValue, existing)
  }

  return {
    rows: Array.from(rowMap.values()),
    seriesKeys: Array.from(seriesSet),
  }
}

function DataTable({ data }: { data: Record<string, unknown>[] }) {
  if (data.length === 0) {
    return <p className="empty-chart">No data to display.</p>
  }

  const columns = Object.keys(data[0])

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>{asString(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function KpiDisplay({
  data,
  valueField,
  label,
}: {
  data: Record<string, unknown>[]
  valueField: string
  label: string
}) {
  const value = data.length > 0 ? asNumber(data[0][valueField]) : 0

  return (
    <div className="kpi-display">
      <span className="kpi-value">{value.toLocaleString()}</span>
      <span className="kpi-label">{label}</span>
    </div>
  )
}

function NetworkGraph({ data, valueField }: { data: Record<string, unknown>[]; valueField: string }) {
  if (data.length === 0) {
    return <p className="empty-chart">No network edges to display.</p>
  }

  const maxWeight = Math.max(...data.map((row) => asNumber(row[valueField])), 1)

  return (
    <div className="network-list">
      {data.map((row, index) => {
        const source = asString(row.source)
        const target = asString(row.target)
        const weight = asNumber(row[valueField])
        const width = Math.max(4, (weight / maxWeight) * 100)

        return (
          <div key={`${source}-${target}-${index}`} className="network-edge">
            <div className="network-nodes">
              <span className="network-node">{source}</span>
              <span className="network-arrow">→</span>
              <span className="network-node">{target}</span>
            </div>
            <div className="network-bar-track">
              <div className="network-bar-fill" style={{ width: `${width}%` }} />
            </div>
            <span className="network-weight">{weight.toLocaleString()}</span>
          </div>
        )
      })}
    </div>
  )
}

export function VisualizationRenderer({ spec }: { spec: VisualizationSpec }) {
  const { type, title, encoding, data } = spec

  if (!data.length) {
    return (
      <div className="chart-card">
        <h2>{title}</h2>
        <p className="empty-chart">No data returned for this query.</p>
      </div>
    )
  }

  const xField = encoding.x?.field ?? 'x'
  const yField = encoding.y?.field ?? encoding.value?.field ?? 'y'
  const seriesField = encoding.series?.field
  const valueField = encoding.value?.field ?? yField
  const labelField = encoding.label?.field ?? encoding.geo?.field ?? xField

  const xLabel = channelLabel(encoding.x, 'Category')
  const yLabel = channelLabel(encoding.y ?? encoding.value, 'Value')

  const chartBody = (() => {
    switch (type) {
      case 'line_chart':
        return (
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={data} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey={xField}
                label={{ value: xLabel, position: 'insideBottom', offset: -4 }}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Line
                type="monotone"
                dataKey={yField}
                stroke={CHART_COLORS[0]}
                strokeWidth={2.5}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )

      case 'bar_chart':
      case 'map':
        return (
          <ResponsiveContainer width="100%" height={380}>
            <BarChart
              data={data}
              layout={type === 'map' ? 'vertical' : 'horizontal'}
              margin={{ top: 8, right: 24, left: type === 'map' ? 80 : 8, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              {type === 'map' ? (
                <>
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey={labelField}
                    width={120}
                    tick={{ fontSize: 12 }}
                  />
                </>
              ) : (
                <>
                  <XAxis
                    dataKey={xField}
                    label={{ value: xLabel, position: 'insideBottom', offset: -4 }}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
                    tick={{ fontSize: 12 }}
                  />
                </>
              )}
              <Tooltip />
              <Bar dataKey={yField} fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )

      case 'grouped_bar_chart': {
        if (!seriesField) {
          return <DataTable data={data} />
        }
        const { rows, seriesKeys } = pivotGroupedData(data, xField, seriesField, yField)
        return (
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={rows} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey={xField}
                label={{ value: xLabel, position: 'insideBottom', offset: -4 }}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Legend />
              {seriesKeys.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )
      }

      case 'stacked_bar_chart': {
        if (!seriesField) {
          return <DataTable data={data} />
        }
        const { rows, seriesKeys } = pivotGroupedData(data, xField, seriesField, yField)
        return (
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={rows} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey={xField}
                label={{ value: xLabel, position: 'insideBottom', offset: -4 }}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Legend />
              {seriesKeys.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  stackId="stack"
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )
      }

      case 'pie_chart': {
        const pieLabel = encoding.label?.field ?? xField
        return (
          <ResponsiveContainer width="100%" height={380}>
            <PieChart>
              <Pie
                data={data}
                dataKey={valueField}
                nameKey={pieLabel}
                cx="50%"
                cy="50%"
                outerRadius={130}
                label={({ name, percent }) =>
                  `${asString(name)} (${((percent ?? 0) * 100).toFixed(0)}%)`
                }
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )
      }

      case 'scatter_plot':
        return (
          <ResponsiveContainer width="100%" height={380}>
            <ScatterChart margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                type="number"
                dataKey={xField}
                name={xLabel}
                label={{ value: xLabel, position: 'insideBottom', offset: -4 }}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                type="number"
                dataKey={yField}
                name={yLabel}
                label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
                tick={{ fontSize: 12 }}
              />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={data} fill={CHART_COLORS[0]} />
            </ScatterChart>
          </ResponsiveContainer>
        )

      case 'table':
        return <DataTable data={data} />

      case 'kpi':
        return (
          <KpiDisplay
            data={data}
            valueField={valueField}
            label={channelLabel(encoding.value, 'Total')}
          />
        )

      case 'network_graph':
        return <NetworkGraph data={data} valueField={valueField} />

      default:
        return <DataTable data={data} />
    }
  })()

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h2>{title}</h2>
        <span className="chart-type-badge">{type.replace(/_/g, ' ')}</span>
      </div>
      <div className="chart-body">{chartBody}</div>
    </div>
  )
}
