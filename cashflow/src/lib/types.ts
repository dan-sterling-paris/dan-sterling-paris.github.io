export interface Account {
  id: string
  name: string
  balance: number
  created_at: string
}

export interface CashflowItem {
  id: string
  detail: string
  type: 'income' | 'expense'
  due_date: string | null
  frequency: 'once' | 'weekly' | 'monthly'
  monthly_day: number | null
  amount: number
  confirmed: boolean
  created_at: string
}

export interface Loan {
  id: string
  detail: string
  type: 'borrowed' | 'lent'
  person: string
  amount: number
  loan_date: string
  repay_date: string | null
  settled: boolean
  created_at: string
}

export interface WeekForecast {
  weekStart: Date
  balance: number
  in: number
  out: number
  end: number
  incomeItems: CashflowItem[]
  expenseItems: CashflowItem[]
}
