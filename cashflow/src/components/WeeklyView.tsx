import { useState } from 'react'
import { format } from 'date-fns'
import type { Account, CashflowItem, Loan, WeekCashflowItem, WeekForecast } from '../lib/types'
import { calculateForecast } from '../lib/forecast'
import { exportCashflow } from '../lib/exportXlsx'

interface WeeklyViewProps {
  accounts: Account[]
  incomeItems: CashflowItem[]
  expenseItems: CashflowItem[]
  loans: Loan[]
  onUpdateItem?: (id: string, updates: Partial<Omit<CashflowItem, 'id' | 'created_at'>>) => Promise<void>
}

function WeekCard({
  week,
  index,
  onToggleAccounted,
}: {
  week: WeekForecast
  index: number
  onToggleAccounted?: (item: WeekCashflowItem) => void
}) {
  const [expanded, setExpanded] = useState(index === 0)
  const isNegative = week.end < 0

  return (
    <div className="bg-gray-900 rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left"
      >
        <div>
          <p className="text-sm text-gray-400">
            w/c {format(week.weekStart, 'dd MMM yyyy')}
          </p>
          <div className="flex gap-4 mt-1">
            {week.in > 0 && (
              <span className="text-sm text-green-400">
                +£{week.in.toFixed(2)}
              </span>
            )}
            {week.out > 0 && (
              <span className="text-sm text-red-400">
                -£{week.out.toFixed(2)}
              </span>
            )}
            {week.in === 0 && week.out === 0 && (
              <span className="text-sm text-gray-500">No activity</span>
            )}
          </div>
        </div>
        <div className="text-right">
          <p
            className={`text-lg font-bold ${
              isNegative ? 'text-red-400' : 'text-white'
            }`}
          >
            £{week.end.toFixed(2)}
          </p>
          <span className="text-gray-500 text-xs">
            {expanded ? '▲' : '▼'}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-800">
          <div className="grid grid-cols-2 gap-2 py-3 text-xs text-gray-400 border-b border-gray-800">
            <div>Opening: £{week.balance.toFixed(2)}</div>
            <div className="text-right">
              Closing: £{week.end.toFixed(2)}
            </div>
          </div>

          {week.incomeItems.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-green-400 mb-2">
                INCOME
              </p>
              {week.incomeItems.map((item) => {
                const isLoan = item.id.startsWith('loan-')
                const canToggle = index === 0 && !isLoan && !!onToggleAccounted

                return (
                  <button
                    key={item.id + week.weekStart.toISOString()}
                    type="button"
                    disabled={!canToggle}
                    onClick={() => canToggle && onToggleAccounted(item)}
                    className={`w-full flex justify-between py-1.5 border-l-2 pl-3 mb-1 text-left ${
                      item.accountedFor
                        ? 'border-gray-600 opacity-50'
                        : 'border-green-500'
                    } ${canToggle ? 'active:bg-gray-800' : ''}`}
                  >
                    <span className={`text-sm text-gray-300 ${item.accountedFor ? 'line-through' : ''}`}>
                      {item.accountedFor && '✓ '}
                      {item.detail}
                      {!item.confirmed && (
                        <span className="ml-2 text-xs text-amber-400">
                          (pending)
                        </span>
                      )}
                    </span>
                    <span className={`text-sm ${item.accountedFor ? 'text-gray-500 line-through' : 'text-green-400'}`}>
                      +£{item.amount.toFixed(2)}
                    </span>
                  </button>
                )
              })}
            </div>
          )}

          {week.expenseItems.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-red-400 mb-2">
                EXPENSES
              </p>
              {week.expenseItems.map((item) => {
                const isLoan = item.id.startsWith('loan-')
                const canToggle = index === 0 && !isLoan && !!onToggleAccounted

                return (
                  <button
                    key={item.id + week.weekStart.toISOString()}
                    type="button"
                    disabled={!canToggle}
                    onClick={() => canToggle && onToggleAccounted(item)}
                    className={`w-full flex justify-between py-1.5 border-l-2 pl-3 mb-1 text-left ${
                      item.accountedFor
                        ? 'border-gray-600 opacity-50'
                        : 'border-red-500'
                    } ${canToggle ? 'active:bg-gray-800' : ''}`}
                  >
                    <span className={`text-sm text-gray-300 ${item.accountedFor ? 'line-through' : ''}`}>
                      {item.accountedFor && '✓ '}
                      {item.detail}
                      {!item.confirmed && (
                        <span className="ml-2 text-xs text-amber-400">
                          (pending)
                        </span>
                      )}
                    </span>
                    <span className={`text-sm ${item.accountedFor ? 'text-gray-500 line-through' : 'text-red-400'}`}>
                      -£{item.amount.toFixed(2)}
                    </span>
                  </button>
                )
              })}
            </div>
          )}

          {week.incomeItems.length === 0 && week.expenseItems.length === 0 && (
            <p className="text-sm text-gray-500 mt-3">
              Nothing scheduled this week
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function WeeklyView({
  accounts,
  incomeItems,
  expenseItems,
  loans,
  onUpdateItem,
}: WeeklyViewProps) {
  const allItems = [...incomeItems, ...expenseItems]
  const forecast = calculateForecast(accounts, allItems, loans)

  const handleToggleAccounted = async (item: WeekCashflowItem) => {
    if (!onUpdateItem) return
    const newPaidThrough = item.accountedFor ? null : item.occurrenceDate
    await onUpdateItem(item.id, { paid_through: newPaidThrough })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold">Weekly Forecast</h2>
        <button
          type="button"
          onClick={() => exportCashflow(accounts, forecast, loans)}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
        >
          Export XLSX
        </button>
      </div>

      <div className="space-y-2">
        {forecast.map((week, i) => (
          <WeekCard
            key={week.weekStart.toISOString()}
            week={week}
            index={i}
            onToggleAccounted={i === 0 ? handleToggleAccounted : undefined}
          />
        ))}
      </div>
    </div>
  )
}
