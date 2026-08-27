import { useState } from 'react'
import { format } from 'date-fns'
import type { Loan } from '../lib/types'

interface LoansListProps {
  loans: Loan[]
  loading: boolean
  onAdd: (loan: Omit<Loan, 'id' | 'created_at'>) => void
  onUpdate: (id: string, updates: Partial<Loan>) => void
  onDelete: (id: string) => void
}

function formatCurrency(value: number): string {
  return `£${Math.abs(value).toLocaleString('en-GB', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

function LoanForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (loan: Omit<Loan, 'id' | 'created_at'>) => void
  onCancel: () => void
}) {
  const [type, setType] = useState<'borrowed' | 'lent'>('borrowed')
  const [detail, setDetail] = useState('')
  const [person, setPerson] = useState('')
  const [amount, setAmount] = useState('')
  const [loanDate, setLoanDate] = useState('')
  const [repayDate, setRepayDate] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      type,
      detail,
      person,
      amount: parseFloat(amount),
      loan_date: loanDate,
      repay_date: repayDate || null,
      settled: false,
    })
    onCancel()
  }

  return (
    <form onSubmit={handleSubmit} className="bg-gray-900 rounded-xl p-4 space-y-3">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setType('borrowed')}
          className={`flex-1 py-2 rounded-lg text-sm font-medium ${
            type === 'borrowed'
              ? 'bg-red-600 text-white'
              : 'bg-gray-800 text-gray-400'
          }`}
        >
          I borrowed
        </button>
        <button
          type="button"
          onClick={() => setType('lent')}
          className={`flex-1 py-2 rounded-lg text-sm font-medium ${
            type === 'lent'
              ? 'bg-green-600 text-white'
              : 'bg-gray-800 text-gray-400'
          }`}
        >
          I lent
        </button>
      </div>
      <input
        type="text"
        placeholder="What for"
        value={detail}
        onChange={(e) => setDetail(e.target.value)}
        className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white"
        required
      />
      <input
        type="text"
        placeholder={type === 'borrowed' ? 'From whom' : 'To whom'}
        value={person}
        onChange={(e) => setPerson(e.target.value)}
        className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white"
        required
      />
      <div>
        <label className="text-xs text-gray-500">Amount</label>
        <input
          type="number"
          step="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white"
          required
        />
      </div>
      <div>
        <label className="text-xs text-gray-500">
          {type === 'borrowed' ? 'Date received' : 'Date lent'}
        </label>
        <input
          type="date"
          value={loanDate}
          onChange={(e) => setLoanDate(e.target.value)}
          className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white"
          required
        />
      </div>
      <div>
        <label className="text-xs text-gray-500">
          {type === 'borrowed' ? 'Repay by (optional)' : 'Expect back by (optional)'}
        </label>
        <input
          type="date"
          value={repayDate}
          onChange={(e) => setRepayDate(e.target.value)}
          className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg text-sm font-medium"
        >
          Add
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg text-sm"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function LoansList({
  loans,
  loading,
  onAdd,
  onUpdate,
  onDelete,
}: LoansListProps) {
  const [showForm, setShowForm] = useState(false)

  const active = loans.filter((l) => !l.settled)
  const settled = loans.filter((l) => l.settled)

  const totalBorrowed = active
    .filter((l) => l.type === 'borrowed')
    .reduce((sum, l) => sum + l.amount, 0)
  const totalLent = active
    .filter((l) => l.type === 'lent')
    .reduce((sum, l) => sum + l.amount, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Loans</h2>
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg"
        >
          {showForm ? 'Close' : '+ Add'}
        </button>
      </div>

      <p className="text-xs text-gray-400">
        Active loans automatically appear in your cashflow forecast.
      </p>

      {showForm && (
        <LoanForm onSubmit={onAdd} onCancel={() => setShowForm(false)} />
      )}

      {/* Summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-900 rounded-xl p-4">
          <p className="text-xs text-gray-400 mb-1">I owe</p>
          <p className="text-xl font-bold text-red-400">
            {formatCurrency(totalBorrowed)}
          </p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <p className="text-xs text-gray-400 mb-1">Owed to me</p>
          <p className="text-xl font-bold text-green-400">
            {formatCurrency(totalLent)}
          </p>
        </div>
      </div>

      {/* Active */}
      {active.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-400">ACTIVE</h3>
          {active.map((loan) => (
            <div
              key={loan.id}
              className={`bg-gray-900 rounded-xl p-4 border-l-2 ${
                loan.type === 'borrowed' ? 'border-red-500' : 'border-green-500'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-200">
                    {loan.detail}
                  </p>
                  <p className="text-xs text-gray-500">
                    {loan.type === 'borrowed' ? 'From' : 'To'}: {loan.person}
                  </p>
                  <p className="text-xs text-gray-500">
                    {loan.type === 'borrowed' ? 'Received' : 'Lent'}:{' '}
                    {format(new Date(loan.loan_date), 'dd MMM yyyy')}
                  </p>
                  {loan.repay_date && (
                    <p className="text-xs text-gray-500">
                      {loan.type === 'borrowed' ? 'Repay by' : 'Expect back'}:{' '}
                      {format(new Date(loan.repay_date), 'dd MMM yyyy')}
                    </p>
                  )}
                </div>
                <p
                  className={`text-lg font-bold ${
                    loan.type === 'borrowed' ? 'text-red-400' : 'text-green-400'
                  }`}
                >
                  {formatCurrency(loan.amount)}
                </p>
              </div>
              <div className="flex gap-2 mt-3">
                <button
                  type="button"
                  onClick={() => onUpdate(loan.id, { settled: true })}
                  className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-green-400 rounded-lg text-xs"
                >
                  Mark settled
                </button>
                <button
                  type="button"
                  onClick={() => onDelete(loan.id)}
                  className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-red-400 rounded-lg text-xs"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Settled */}
      {settled.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-400">SETTLED</h3>
          {settled.map((loan) => (
            <div key={loan.id} className="bg-gray-900 rounded-xl p-3 opacity-50">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-400 line-through">
                    {loan.detail}
                  </p>
                  <p className="text-xs text-gray-600">
                    {loan.person}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">
                    {formatCurrency(loan.amount)}
                  </span>
                  <button
                    type="button"
                    onClick={() => onUpdate(loan.id, { settled: false })}
                    className="text-xs text-gray-500 hover:text-amber-400"
                  >
                    Reopen
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(loan.id)}
                    className="text-gray-600 hover:text-red-400 text-xs"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {active.length === 0 && settled.length === 0 && !showForm && (
        <div className="bg-gray-900 rounded-xl p-8 text-center">
          <p className="text-gray-500">No loans yet</p>
        </div>
      )}
    </div>
  )
}
