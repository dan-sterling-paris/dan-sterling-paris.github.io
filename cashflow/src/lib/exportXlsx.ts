import * as XLSX from 'xlsx'
import { format } from 'date-fns'
import type { Account, Loan, WeekForecast } from './types'

export function exportCashflow(
  accounts: Account[],
  forecast: WeekForecast[],
  loans: Loan[] = []
) {
  const wb = XLSX.utils.book_new()

  // Accounts sheet
  const accountRows = accounts.map((a) => ({
    Account: a.name,
    Balance: a.balance,
  }))
  accountRows.push({
    Account: 'TOTAL',
    Balance: accounts.reduce((sum, a) => sum + a.balance, 0),
  })
  const accountsWs = XLSX.utils.json_to_sheet(accountRows)
  XLSX.utils.book_append_sheet(wb, accountsWs, 'Accounts')

  // Weekly forecast sheet
  const forecastRows = forecast.map((week) => ({
    'Week Starting': format(week.weekStart, 'dd/MM/yyyy'),
    'Opening Balance': week.balance,
    In: week.in,
    Out: week.out,
    'Closing Balance': week.end,
    'Income Details': week.incomeItems.map((i) => `${i.detail} (£${i.amount.toFixed(2)})`).join(', ') || '-',
    'Expense Details': week.expenseItems.map((i) => `${i.detail} (£${i.amount.toFixed(2)})`).join(', ') || '-',
  }))
  const forecastWs = XLSX.utils.json_to_sheet(forecastRows)
  forecastWs['!cols'] = [
    { wch: 14 },
    { wch: 16 },
    { wch: 12 },
    { wch: 12 },
    { wch: 16 },
    { wch: 40 },
    { wch: 40 },
  ]
  XLSX.utils.book_append_sheet(wb, forecastWs, 'Weekly Forecast')

  // Loans sheet
  const activeLoans = loans.filter((l) => !l.settled)
  if (activeLoans.length > 0) {
    const loanRows = activeLoans.map((l) => ({
      Detail: l.detail,
      Type: l.type === 'borrowed' ? 'Borrowed' : 'Lent',
      Person: l.person,
      Amount: l.amount,
      Date: l.loan_date,
      'Repay/Return By': l.repay_date || '-',
    }))
    const loansWs = XLSX.utils.json_to_sheet(loanRows)
    XLSX.utils.book_append_sheet(wb, loansWs, 'Loans')
  }

  const dateStr = format(new Date(), 'yyyy-MM-dd')
  XLSX.writeFile(wb, `cashflow-${dateStr}.xlsx`)
}
