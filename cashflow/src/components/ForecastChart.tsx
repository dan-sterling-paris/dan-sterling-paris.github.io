import { format } from 'date-fns'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts'
import type { WeekForecast } from '../lib/types'

interface ForecastChartProps {
  forecast: WeekForecast[]
}

interface ChartDatum {
  label: string
  end: number
  balance: number
  in: number
  out: number
}

function formatCurrency(value: number): string {
  return `£${value.toLocaleString('en-GB', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const data = payload[0].payload as ChartDatum
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm">
      <p className="text-white font-medium mb-1">{label}</p>
      <p className="text-gray-300">Balance: {formatCurrency(data.end)}</p>
      <p className="text-green-400">In: {formatCurrency(data.in)}</p>
      <p className="text-red-400">Out: {formatCurrency(data.out)}</p>
    </div>
  )
}

export default function ForecastChart({ forecast }: ForecastChartProps) {
  const chartData: ChartDatum[] = forecast.map((week) => ({
    label: format(week.weekStart, 'dd MMM'),
    end: week.end,
    balance: week.balance,
    in: week.in,
    out: week.out,
  }))

  const minValue = Math.min(...chartData.map((d) => d.end))
  const maxValue = Math.max(...chartData.map((d) => d.end))
  const padding = Math.abs(maxValue - minValue) * 0.1 || 500
  const yMin = Math.floor((minValue - padding) / 100) * 100
  const yMax = Math.ceil((maxValue + padding) / 100) * 100

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h3 className="text-gray-400 text-sm mb-3">12-week forecast</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="label"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: '#374151' }}
            interval={1}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: '#374151' }}
            tickFormatter={(v: number) => `£${(v / 1000).toFixed(0)}k`}
            width={50}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="4 4" />
          <Line
            type="monotone"
            dataKey="end"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            activeDot={{ r: 5, fill: '#60a5fa' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
