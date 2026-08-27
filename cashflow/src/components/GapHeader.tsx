import { useMemo } from 'react'
import { format } from 'date-fns'
import { calculateForecast } from '../lib/forecast'
import type { Account, CashflowItem, Loan } from '../lib/types'

interface GapHeaderProps {
  accounts: Account[]
  items: CashflowItem[]
  loans: Loan[]
}

function formatCurrency(value: number): string {
  return `£${Math.abs(value).toLocaleString('en-GB', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export default function GapHeader({ accounts, items, loans }: GapHeaderProps) {
  const forecast = useMemo(
    () => calculateForecast(accounts, items, loans),
    [accounts, items, loans]
  )

  const lowest = useMemo(() => {
    if (forecast.length === 0) return null
    return forecast.reduce((min, w) => (w.end < min.end ? w : min))
  }, [forecast])

  const totalBalance = accounts.reduce((sum, a) => sum + a.balance, 0)

  if (!lowest) return null

  const isNegative = lowest.end < 0

  return (
    <div
      className={`sticky top-0 z-20 px-4 py-2 flex items-center justify-between text-sm ${
        isNegative
          ? 'bg-red-950/95 border-b border-red-800'
          : 'bg-green-950/95 border-b border-green-800'
      } backdrop-blur-sm`}
    >
      <div className="flex items-center gap-3">
        <span className="text-gray-400">Now:</span>
        <span className={totalBalance >= 0 ? 'text-green-400 font-medium' : 'text-red-400 font-medium'}>
          {formatCurrency(totalBalance)}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-gray-400">
          {isNegative ? 'Gap:' : 'Low:'}
        </span>
        <span className={`font-bold ${isNegative ? 'text-red-400' : 'text-green-400'}`}>
          {isNegative ? `-${formatCurrency(lowest.end)}` : formatCurrency(lowest.end)}
        </span>
        <span className="text-gray-500 text-xs">
          w/c {format(lowest.weekStart, 'dd MMM')}
        </span>
      </div>
    </div>
  )
}
