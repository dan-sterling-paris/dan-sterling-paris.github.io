import { startOfWeek, addWeeks, addDays, parseISO, format, getDay } from 'date-fns'
import type { Account, CashflowItem, Loan, WeekCashflowItem, WeekForecast } from './types'

export function calculateForecast(
  accounts: Account[],
  items: CashflowItem[],
  loans: Loan[] = [],
  weeks = 12
): WeekForecast[] {
  const startBalance = accounts.reduce((sum, a) => sum + a.balance, 0)
  const today = startOfWeek(new Date(), { weekStartsOn: 1 })

  const activeLoans = loans.filter((l) => !l.settled)

  let running = startBalance
  return Array.from({ length: weeks }, (_, i) => {
    const weekStart = addWeeks(today, i)
    const weekEnd = addDays(weekStart, 6)

    const incomeItems: WeekCashflowItem[] = []
    const expenseItems: WeekCashflowItem[] = []

    for (const item of items) {
      const occ = getOccurrenceDate(item, weekStart, weekEnd)
      if (!occ) continue
      const weekItem: WeekCashflowItem = {
        ...item,
        occurrenceDate: occ,
        accountedFor: isAccountedFor(item, occ),
      }
      if (item.type === 'income') incomeItems.push(weekItem)
      else expenseItems.push(weekItem)
    }

    // Loans affect cashflow:
    // Borrowed: money IN on loan_date, money OUT on repay_date
    // Lent: money OUT on loan_date, money IN on repay_date
    for (const loan of activeLoans) {
      const loanDate = parseISO(loan.loan_date)
      if (loanDate >= weekStart && loanDate <= weekEnd) {
        const loanItem: WeekCashflowItem = {
          id: `loan-${loan.id}`,
          detail: `${loan.type === 'borrowed' ? '🔽' : '🔼'} ${loan.detail} (${loan.person})`,
          type: loan.type === 'borrowed' ? 'income' : 'expense',
          due_date: loan.loan_date,
          frequency: 'once',
          monthly_day: null,
          amount: loan.amount,
          confirmed: true,
          paid_through: null,
          created_at: loan.created_at,
          occurrenceDate: loan.loan_date,
          accountedFor: false,
        }
        if (loan.type === 'borrowed') {
          incomeItems.push(loanItem)
        } else {
          expenseItems.push(loanItem)
        }
      }

      if (loan.repay_date) {
        const repayDate = parseISO(loan.repay_date)
        if (repayDate >= weekStart && repayDate <= weekEnd) {
          const repayItem: WeekCashflowItem = {
            id: `loan-repay-${loan.id}`,
            detail: `${loan.type === 'borrowed' ? '🔼' : '🔽'} Repay: ${loan.detail} (${loan.person})`,
            type: loan.type === 'borrowed' ? 'expense' : 'income',
            due_date: loan.repay_date,
            frequency: 'once',
            monthly_day: null,
            amount: loan.amount,
            confirmed: true,
            paid_through: null,
            created_at: loan.created_at,
            occurrenceDate: loan.repay_date,
            accountedFor: false,
          }
          if (loan.type === 'borrowed') {
            expenseItems.push(repayItem)
          } else {
            incomeItems.push(repayItem)
          }
        }
      }
    }

    const weekIn = incomeItems
      .filter((item) => !item.accountedFor)
      .reduce((sum, item) => sum + item.amount, 0)
    const weekOut = expenseItems
      .filter((item) => !item.accountedFor)
      .reduce((sum, item) => sum + item.amount, 0)

    const end = running + weekIn - weekOut
    const result: WeekForecast = {
      weekStart,
      balance: running,
      in: weekIn,
      out: weekOut,
      end,
      incomeItems,
      expenseItems,
    }
    running = end
    return result
  })
}

function getOccurrenceDate(
  item: CashflowItem,
  weekStart: Date,
  weekEnd: Date
): string | null {
  if (item.frequency === 'once' && item.due_date) {
    const d = parseISO(item.due_date)
    if (d >= weekStart && d <= weekEnd) return item.due_date
    return null
  }

  if (item.frequency === 'weekly' && item.due_date) {
    const dueDate = parseISO(item.due_date)
    if (dueDate > weekEnd) return null
    // Find the day within this week that matches due_date's day-of-week
    const dueDow = getDay(dueDate) // 0=Sun, 1=Mon, ..., 6=Sat
    for (let d = new Date(weekStart); d <= weekEnd; d = addDays(d, 1)) {
      if (getDay(d) === dueDow) return format(d, 'yyyy-MM-dd')
    }
    return null
  }

  if (item.frequency === 'monthly' && item.monthly_day) {
    for (let d = new Date(weekStart); d <= weekEnd; d = addDays(d, 1)) {
      if (d.getDate() === item.monthly_day) return format(d, 'yyyy-MM-dd')
    }
  }

  return null
}

function isAccountedFor(item: CashflowItem, occurrenceDate: string): boolean {
  if (!item.paid_through) return false
  return occurrenceDate <= item.paid_through
}
