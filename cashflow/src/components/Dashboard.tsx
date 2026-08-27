import { useMemo } from 'react'
import { format } from 'date-fns'
import { calculateForecast } from '../lib/forecast'
import type { Account, CashflowItem, Loan } from '../lib/types'
import ForecastChart from './ForecastChart'

interface DashboardProps {
  accounts: Account[]
  incomeItems: CashflowItem[]
  expenseItems: CashflowItem[]
  loans: Loan[]
}

function formatCurrency(value: number): string {
  return `£${value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function Dashboard({
  accounts,
  incomeItems,
  expenseItems,
  loans,
}: DashboardProps) {
  const allItems = useMemo(
    () => [...incomeItems, ...expenseItems],
    [incomeItems, expenseItems]
  )

  const forecast = useMemo(
    () => calculateForecast(accounts, allItems, loans),
    [accounts, allItems, loans]
  )

  const totalBalance = accounts.reduce((sum, a) => sum + a.balance, 0)

  const lowestPoint = useMemo(() => {
    if (forecast.length === 0) return null
    return forecast.reduce((min, week) =>
      week.end < min.end ? week : min
    )
  }, [forecast])

  const nextBigOutgoing = useMemo(() => {
    const confirmed = expenseItems.filter((item) => item.confirmed)
    if (confirmed.length === 0) return null
    return confirmed.reduce((max, item) =>
      item.amount > max.amount ? item : max
    )
  }, [expenseItems])

  const unconfirmedIncome = useMemo(() => {
    return incomeItems
      .filter((item) => !item.confirmed)
      .reduce((sum, item) => sum + item.amount, 0)
  }, [incomeItems])

  return (
    <div className="space-y-4">
      <div className="bg-gray-900 rounded-xl p-6 text-center">
        <p className="text-gray-400 text-sm mb-1">Total balance</p>
        <p
          className={`text-4xl font-bold ${
            totalBalance >= 0 ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {formatCurrency(totalBalance)}
        </p>
      </div>

      <ForecastChart forecast={forecast} />

      <div className="grid grid-cols-1 gap-3">
        {lowestPoint && (
          <div className="bg-gray-900 rounded-xl p-4">
            <p className="text-gray-400 text-sm mb-1">Lowest point</p>
            <p
              className={`text-xl font-semibold ${
                lowestPoint.end >= 0 ? 'text-white' : 'text-red-400'
              }`}
            >
              {formatCurrency(lowestPoint.end)}
            </p>
            <p className="text-gray-500 text-xs">
              Week of {format(lowestPoint.weekStart, 'dd MMM yyyy')}
            </p>
          </div>
        )}

        {nextBigOutgoing && (
          <div className="bg-gray-900 rounded-xl p-4">
            <p className="text-gray-400 text-sm mb-1">Next big outgoing</p>
            <p className="text-xl font-semibold text-red-400">
              {formatCurrency(nextBigOutgoing.amount)}
            </p>
            <p className="text-gray-500 text-xs">{nextBigOutgoing.detail}</p>
          </div>
        )}

        <div className="bg-gray-900 rounded-xl p-4">
          <p className="text-gray-400 text-sm mb-1">Unconfirmed income</p>
          <p className="text-xl font-semibold text-amber-400">
            {formatCurrency(unconfirmedIncome)}
          </p>
        </div>
      </div>
    </div>
  )
}
