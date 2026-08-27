import { startOfWeek, addWeeks, addDays, parseISO } from 'date-fns'
import type { Account, CashflowItem, Loan, WeekForecast } from './types'

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

    const incomeItems = items.filter(
      (item) => item.type === 'income' && fallsInWeek(item, weekStart, weekEnd)
    )
    const expenseItems = items.filter(
      (item) => item.type === 'expense' && fallsInWeek(item, weekStart, weekEnd)
    )

    // Loans affect cashflow:
    // Borrowed: money IN on loan_date, money OUT on repay_date
    // Lent: money OUT on loan_date, money IN on repay_date
    for (const loan of activeLoans) {
      const loanDate = parseISO(loan.loan_date)
      if (loanDate >= weekStart && loanDate <= weekEnd) {
        const loanItem: CashflowItem = {
          id: `loan-${loan.id}`,
          detail: `${loan.type === 'borrowed' ? '🔽' : '🔼'} ${loan.detail} (${loan.person})`,
          type: loan.type === 'borrowed' ? 'income' : 'expense',
          due_date: loan.loan_date,
          frequency: 'once',
          monthly_day: null,
          amount: loan.amount,
          confirmed: true,
          created_at: loan.created_at,
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
          const repayItem: CashflowItem = {
            id: `loan-repay-${loan.id}`,
            detail: `${loan.type === 'borrowed' ? '🔼' : '🔽'} Repay: ${loan.detail} (${loan.person})`,
            type: loan.type === 'borrowed' ? 'expense' : 'income',
            due_date: loan.repay_date,
            frequency: 'once',
            monthly_day: null,
            amount: loan.amount,
            confirmed: true,
            created_at: loan.created_at,
          }
          if (loan.type === 'borrowed') {
            expenseItems.push(repayItem)
          } else {
            incomeItems.push(repayItem)
          }
        }
      }
    }

    const weekIn = incomeItems.reduce((sum, item) => sum + item.amount, 0)
    const weekOut = expenseItems.reduce((sum, item) => sum + item.amount, 0)

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

function fallsInWeek(
  item: CashflowItem,
  weekStart: Date,
  weekEnd: Date
): boolean {
  if (item.frequency === 'once' && item.due_date) {
    const d = parseISO(item.due_date)
    return d >= weekStart && d <= weekEnd
  }
  if (item.frequency === 'weekly' && item.due_date) {
    return parseISO(item.due_date) <= weekEnd
  }
  if (item.frequency === 'monthly' && item.monthly_day) {
    for (let d = new Date(weekStart); d <= weekEnd; d = addDays(d, 1)) {
      if (d.getDate() === item.monthly_day) return true
    }
  }
  return false
}
