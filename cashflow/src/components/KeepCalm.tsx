import { useMemo } from 'react'
import { format } from 'date-fns'
import { calculateForecast } from '../lib/forecast'
import { applySelections } from '../lib/applySelections'
import type { Account, CashflowItem, Loan } from '../lib/types'

interface KeepCalmProps {
  accounts: Account[]
  incomeItems: CashflowItem[]
  expenseItems: CashflowItem[]
  loans: Loan[]
  selectedIds: Set<string>
  onToggle: (id: string) => void
  onClear: () => void
}

function formatCurrency(value: number): string {
  return `£${Math.abs(value).toLocaleString('en-GB', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export default function KeepCalm({
  accounts,
  incomeItems,
  expenseItems,
  loans,
  selectedIds,
  onToggle,
  onClear,
}: KeepCalmProps) {
  const allItems = useMemo(
    () => [...incomeItems, ...expenseItems],
    [incomeItems, expenseItems]
  )

  const totalBalance = accounts.reduce((sum, a) => sum + a.balance, 0)

  // Base forecast (no Keep Calm modifications)
  const baseForecast = useMemo(
    () => calculateForecast(accounts, allItems, loans),
    [accounts, allItems, loans]
  )

  const baseLowest = useMemo(() => {
    if (baseForecast.length === 0) return null
    return baseForecast.reduce((min, w) => (w.end < min.end ? w : min))
  }, [baseForecast])

  const baseGap = baseLowest ? Math.min(baseLowest.end, 0) : 0
  const baseInTrouble = baseGap < 0

  // Adjusted forecast (with Keep Calm selections applied)
  const modifiedItems = useMemo(
    () => applySelections(allItems, selectedIds),
    [allItems, selectedIds]
  )

  const adjustedForecast = useMemo(
    () => calculateForecast(accounts, modifiedItems, loans),
    [accounts, modifiedItems, loans]
  )

  const adjustedLowest = useMemo(() => {
    if (adjustedForecast.length === 0) return null
    return adjustedForecast.reduce((min, w) => (w.end < min.end ? w : min))
  }, [adjustedForecast])

  const adjustedGap = adjustedLowest ? Math.min(adjustedLowest.end, 0) : 0
  const adjustedInTrouble = adjustedGap < 0
  const hasSelections = selectedIds.size > 0
  const gapImproved = adjustedGap > baseGap

  // Categorise items
  const chaseable = useMemo(
    () =>
      incomeItems
        .filter((item) => !item.confirmed && item.amount > 0)
        .sort((a, b) => b.amount - a.amount),
    [incomeItems]
  )

  const outstanding = useMemo(
    () =>
      incomeItems
        .filter(
          (item) =>
            item.confirmed &&
            item.frequency === 'once' &&
            item.due_date &&
            new Date(item.due_date) > new Date()
        )
        .sort(
          (a, b) =>
            new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime()
        ),
    [incomeItems]
  )

  const delayable = useMemo(
    () =>
      expenseItems
        .filter((item) => item.frequency === 'once' && item.due_date)
        .sort((a, b) => b.amount - a.amount),
    [expenseItems]
  )

  const monthlyCosts = useMemo(
    () => expenseItems.filter((item) => item.frequency === 'monthly'),
    [expenseItems]
  )
  const monthlyTotal = monthlyCosts.reduce((sum, i) => sum + i.amount, 0)
  const chaseableTotal = chaseable.reduce((sum, i) => sum + i.amount, 0)

  // Check if an individual item impacts the dip (for visual hint, not for disabling)
  // Income: bringing it forward only helps if it's currently AFTER the lowest week
  //   (moving income from before/during the dip week doesn't change the dip,
  //    because the running balance carries forward and cancels out)
  // Expense: removing it only helps if it falls ON or BEFORE the lowest week
  function itemImpactsDip(item: CashflowItem): boolean {
    if (!baseLowest || !baseInTrouble) return false
    const lowestEnd = new Date(baseLowest.weekStart.getTime() + 6 * 86400000)

    if (item.type === 'income') {
      if (item.frequency === 'once' && item.due_date) {
        return new Date(item.due_date) > lowestEnd
      }
      return false
    }
    if (item.type === 'expense') {
      if (item.frequency === 'once' && item.due_date) {
        return new Date(item.due_date) <= lowestEnd
      }
      if (item.frequency === 'monthly') return true
    }
    return false
  }

  function renderItem(
    item: CashflowItem,
    defaultBorderColor: string,
    defaultTextColor: string,
    subtitle?: string
  ) {
    const selected = selectedIds.has(item.id)
    const impacts = itemImpactsDip(item)

    return (
      <button
        key={item.id}
        type="button"
        onClick={() => onToggle(item.id)}
        className={`w-full flex justify-between items-center py-2 border-l-2 pl-3 text-left transition-colors rounded-r-lg ${
          selected
            ? 'border-green-500 bg-green-950/50'
            : `${defaultBorderColor} hover:bg-gray-800`
        }`}
      >
        <div>
          <p className={`text-sm ${selected ? 'text-green-300' : 'text-gray-200'}`}>
            {selected && '✓ '}{item.detail}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500">{subtitle}</p>
          )}
          {baseInTrouble && !impacts && (
            <p className="text-xs text-gray-600">Won't affect the dip</p>
          )}
        </div>
        <span className={`font-medium ${selected ? 'text-green-400' : defaultTextColor}`}>
          {formatCurrency(item.amount)}
        </span>
      </button>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status banner - sticky */}
      <div
        className={`rounded-xl p-5 text-center sticky top-0 z-10 transition-colors ${
          adjustedInTrouble
            ? 'bg-red-950 border border-red-800'
            : baseInTrouble
            ? 'bg-green-950 border border-green-800'
            : 'bg-green-950 border border-green-800'
        }`}
      >
        {adjustedInTrouble ? (
          <>
            <p className="text-2xl mb-1">⚠️</p>
            <p className="text-lg font-bold text-red-300">
              You need to find {formatCurrency(adjustedGap)}
            </p>
            {hasSelections && gapImproved && (
              <p className="text-sm text-amber-400 mt-1">
                Was {formatCurrency(baseGap)} - recovered {formatCurrency(adjustedGap - baseGap)} so far
              </p>
            )}
            {hasSelections && !gapImproved && (
              <p className="text-sm text-gray-400 mt-1">
                Selected items don't affect the dip
              </p>
            )}
            {adjustedLowest && (
              <p className="text-sm text-red-400 mt-1">
                Lowest w/c {format(adjustedLowest.weekStart, 'dd MMM')}
              </p>
            )}
          </>
        ) : baseInTrouble ? (
          <>
            <p className="text-2xl mb-1">🎯</p>
            <p className="text-lg font-bold text-green-300">
              You've covered it!
            </p>
            <p className="text-sm text-green-400 mt-1">
              Gap was {formatCurrency(baseGap)} - surplus of {formatCurrency(adjustedLowest?.end ?? 0)} if these come through
            </p>
          </>
        ) : (
          <>
            <p className="text-2xl mb-1">✅</p>
            <p className="text-lg font-bold text-green-300">
              You're above water
            </p>
            <p className="text-sm text-green-400 mt-1">
              Lowest point: {formatCurrency(baseLowest?.end ?? 0)} w/c{' '}
              {baseLowest ? format(baseLowest.weekStart, 'dd MMM') : '-'}
            </p>
          </>
        )}

        {hasSelections && (
          <button
            type="button"
            onClick={onClear}
            className="mt-2 text-xs text-gray-400 underline"
          >
            Clear selections
          </button>
        )}
      </div>

      {/* Quick maths */}
      <div className="bg-gray-900 rounded-xl p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-3">YOUR POSITION</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-300">Cash in accounts</span>
            <span className={totalBalance >= 0 ? 'text-green-400' : 'text-red-400'}>
              {formatCurrency(totalBalance)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-300">Unconfirmed income</span>
            <span className="text-amber-400">{formatCurrency(chaseableTotal)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-300">Monthly outgoings</span>
            <span className="text-red-400">{formatCurrency(monthlyTotal)}/mo</span>
          </div>
        </div>
      </div>

      {/* Chase unconfirmed income */}
      {chaseable.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-sm font-medium text-amber-400 mb-3">
            💰 CHASE / CONFIRM THESE
          </h3>
          <p className="text-xs text-gray-400 mb-3">
            Tap to bring forward and update forecast
          </p>
          <div className="space-y-2">
            {chaseable.map((item) =>
              renderItem(
                item,
                'border-amber-500',
                'text-amber-400',
                item.due_date
                  ? `Expected: ${format(new Date(item.due_date), 'dd MMM yyyy')}`
                  : item.frequency === 'monthly'
                  ? 'Monthly'
                  : undefined
              )
            )}
          </div>
        </div>
      )}

      {/* Outstanding invoices */}
      {outstanding.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-sm font-medium text-blue-400 mb-3">
            📋 ADVANCE THESE INVOICES
          </h3>
          <p className="text-xs text-gray-400 mb-3">
            Tap to bring forward and update forecast
          </p>
          <div className="space-y-2">
            {outstanding.map((item) =>
              renderItem(
                item,
                'border-blue-500',
                'text-blue-400',
                `Due: ${format(new Date(item.due_date!), 'dd MMM yyyy')}`
              )
            )}
          </div>
        </div>
      )}

      {/* Delay expenses */}
      {delayable.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-sm font-medium text-purple-400 mb-3">
            ⏸️ DELAY THESE
          </h3>
          <p className="text-xs text-gray-400 mb-3">
            Tap to remove from forecast
          </p>
          <div className="space-y-2">
            {delayable.map((item) =>
              renderItem(
                item,
                'border-purple-500',
                'text-purple-400',
                `Due: ${format(new Date(item.due_date!), 'dd MMM yyyy')}`
              )
            )}
          </div>
        </div>
      )}

      {/* Monthly costs */}
      {monthlyCosts.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-3">
            🔁 CUT THESE ({formatCurrency(monthlyTotal)}/mo)
          </h3>
          <p className="text-xs text-gray-400 mb-3">
            Tap to remove from forecast
          </p>
          <div className="space-y-2">
            {monthlyCosts.map((item) =>
              renderItem(
                item,
                'border-gray-600',
                'text-gray-300',
                `Day ${item.monthly_day} each month`
              )
            )}
          </div>
        </div>
      )}

      {/* Brainstorm */}
      <div className="bg-gray-900 rounded-xl p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-3">
          🧠 OTHER IDEAS
        </h3>
        <ul className="space-y-3 text-sm text-gray-300">
          <li className="flex gap-3">
            <span className="text-gray-500 shrink-0">□</span>
            <span>Any clients who owe you that aren't on this list?</span>
          </li>
          <li className="flex gap-3">
            <span className="text-gray-500 shrink-0">□</span>
            <span>Quick freelance work you could pick up this week?</span>
          </li>
          <li className="flex gap-3">
            <span className="text-gray-500 shrink-0">□</span>
            <span>Anything you could sell (equipment, unused subscriptions)?</span>
          </li>
          <li className="flex gap-3">
            <span className="text-gray-500 shrink-0">□</span>
            <span>Can you extend your overdraft or credit facility temporarily?</span>
          </li>
          <li className="flex gap-3">
            <span className="text-gray-500 shrink-0">□</span>
            <span>Anyone who owes you a favour or could lend short-term?</span>
          </li>
          <li className="flex gap-3">
            <span className="text-gray-500 shrink-0">□</span>
            <span>Matched betting, cashback, or sign-up offers?</span>
          </li>
        </ul>
      </div>

      {/* Breathe */}
      <div className="bg-gray-900 rounded-xl p-4 text-center">
        <p className="text-gray-400 text-sm">
          This is temporary. You've been here before and you've sorted it.
          <br />
          Focus on the next 7 days, not the next 90.
        </p>
      </div>
    </div>
  )
}
