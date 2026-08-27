import { useState } from 'react'
import type { Account } from '../lib/types'

interface AccountsListProps {
  accounts: Account[]
  loading: boolean
  onAdd: (name: string, balance: number) => Promise<void>
  onUpdate: (id: string, updates: Partial<Pick<Account, 'name' | 'balance'>>) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

function formatCurrency(value: number): string {
  return `£${value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function AccountsList({
  accounts,
  loading,
  onAdd,
  onUpdate,
  onDelete,
}: AccountsListProps) {
  const [showForm, setShowForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newBalance, setNewBalance] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editBalance, setEditBalance] = useState('')
  const [editName, setEditName] = useState('')

  const totalBalance = accounts.reduce((sum, a) => sum + a.balance, 0)

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim() || !newBalance) return
    await onAdd(newName.trim(), parseFloat(newBalance))
    setNewName('')
    setNewBalance('')
    setShowForm(false)
  }

  const startEditing = (account: Account) => {
    setEditingId(account.id)
    setEditBalance(account.balance.toString())
    setEditName(account.name)
  }

  const saveEdit = async (id: string) => {
    await onUpdate(id, {
      name: editName.trim(),
      balance: parseFloat(editBalance),
    })
    setEditingId(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">Loading accounts...</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-white">Accounts</h2>

      {accounts.map((account) => (
        <div
          key={account.id}
          className="bg-gray-900 rounded-xl p-4 flex items-center justify-between"
        >
          {editingId === account.id ? (
            <div className="flex-1 flex flex-col gap-2">
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
              />
              <div className="flex gap-2">
                <input
                  type="number"
                  step="0.01"
                  value={editBalance}
                  onChange={(e) => setEditBalance(e.target.value)}
                  className="flex-1 bg-gray-800 text-white border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => saveEdit(account.id)}
                  className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-2 rounded-lg transition-colors"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setEditingId(null)}
                  className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-3 py-2 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <button
                type="button"
                onClick={() => startEditing(account)}
                className="flex-1 text-left"
              >
                <p className="text-white font-medium">{account.name}</p>
                <p
                  className={`text-lg font-semibold ${
                    account.balance >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {formatCurrency(account.balance)}
                </p>
              </button>
              <button
                type="button"
                onClick={() => onDelete(account.id)}
                className="text-gray-600 hover:text-red-400 text-xl ml-3 transition-colors"
                title="Delete account"
              >
                ✕
              </button>
            </>
          )}
        </div>
      ))}

      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <div className="flex items-center justify-between">
          <p className="text-gray-400 font-medium">Total</p>
          <p
            className={`text-xl font-bold ${
              totalBalance >= 0 ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {formatCurrency(totalBalance)}
          </p>
        </div>
      </div>

      {showForm ? (
        <form
          onSubmit={handleAdd}
          className="bg-gray-900 rounded-xl p-4 space-y-3"
        >
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Account name"
            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
            autoFocus
          />
          <input
            type="number"
            step="0.01"
            value={newBalance}
            onChange={(e) => setNewBalance(e.target.value)}
            placeholder="Balance"
            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg px-4 py-3 transition-colors"
            >
              Add account
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-lg px-4 py-3 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="w-full bg-gray-900 hover:bg-gray-800 text-blue-400 font-medium rounded-xl p-4 transition-colors border border-dashed border-gray-700"
        >
          + Add account
        </button>
      )}
    </div>
  )
}
