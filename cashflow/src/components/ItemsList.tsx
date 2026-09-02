import { useState } from 'react'
import type { CashflowItem } from '../lib/types'

interface ItemsListProps {
  type: 'income' | 'expense'
  items: CashflowItem[]
  loading: boolean
  onAdd: (item: Omit<CashflowItem, 'id' | 'created_at'>) => Promise<void>
  onUpdate: (id: string, updates: Partial<Omit<CashflowItem, 'id' | 'created_at'>>) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

const frequencyLabels: Record<string, string> = {
  once: 'Once',
  weekly: 'Weekly',
  monthly: 'Monthly',
}

function formatCurrency(value: number): string {
  return `£${value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

interface ItemFormData {
  detail: string
  amount: string
  frequency: 'once' | 'weekly' | 'monthly'
  due_date: string
  monthly_day: string
  confirmed: boolean
}

const emptyForm: ItemFormData = {
  detail: '',
  amount: '',
  frequency: 'monthly',
  due_date: '',
  monthly_day: '',
  confirmed: false,
}

function ItemForm({
  initial,
  onSubmit,
  onCancel,
  submitLabel,
}: {
  initial: ItemFormData
  onSubmit: (data: ItemFormData) => void
  onCancel: () => void
  submitLabel: string
}) {
  const [form, setForm] = useState<ItemFormData>(initial)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.detail.trim() || !form.amount) return
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="bg-gray-900 rounded-xl p-4 space-y-3">
      <input
        type="text"
        value={form.detail}
        onChange={(e) => setForm({ ...form, detail: e.target.value })}
        placeholder="Description"
        className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
        autoFocus
      />
      <input
        type="number"
        step="0.01"
        value={form.amount}
        onChange={(e) => setForm({ ...form, amount: e.target.value })}
        placeholder="Amount"
        className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
      />
      <select
        value={form.frequency}
        onChange={(e) =>
          setForm({
            ...form,
            frequency: e.target.value as 'once' | 'weekly' | 'monthly',
          })
        }
        className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
      >
        <option value="once">Once</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
      </select>

      {(form.frequency === 'once' || form.frequency === 'weekly') && (
        <input
          type="date"
          value={form.due_date}
          onChange={(e) => setForm({ ...form, due_date: e.target.value })}
          className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
        />
      )}

      {form.frequency === 'monthly' && (
        <input
          type="number"
          min="1"
          max="31"
          value={form.monthly_day}
          onChange={(e) => setForm({ ...form, monthly_day: e.target.value })}
          placeholder="Day of month (1-31)"
          className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500"
        />
      )}

      <label className="flex items-center gap-3 text-white cursor-pointer">
        <input
          type="checkbox"
          checked={form.confirmed}
          onChange={(e) => setForm({ ...form, confirmed: e.target.checked })}
          className="w-5 h-5 rounded bg-gray-800 border-gray-700 accent-blue-500"
        />
        Confirmed
      </label>

      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg px-4 py-3 transition-colors"
        >
          {submitLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-lg px-4 py-3 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function ItemsList({
  type,
  items,
  loading,
  onAdd,
  onUpdate,
  onDelete,
}: ItemsListProps) {
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  const title = type === 'income' ? 'Income' : 'Expenses'

  const handleAdd = async (data: ItemFormData) => {
    await onAdd({
      detail: data.detail.trim(),
      type,
      amount: parseFloat(data.amount),
      frequency: data.frequency,
      due_date:
        data.frequency === 'once' || data.frequency === 'weekly'
          ? data.due_date || null
          : null,
      monthly_day:
        data.frequency === 'monthly' && data.monthly_day
          ? parseInt(data.monthly_day, 10)
          : null,
      confirmed: data.confirmed,
      paid_through: null,
    })
    setShowForm(false)
  }

  const handleUpdate = async (id: string, data: ItemFormData) => {
    await onUpdate(id, {
      detail: data.detail.trim(),
      amount: parseFloat(data.amount),
      frequency: data.frequency,
      due_date:
        data.frequency === 'once' || data.frequency === 'weekly'
          ? data.due_date || null
          : null,
      monthly_day:
        data.frequency === 'monthly' && data.monthly_day
          ? parseInt(data.monthly_day, 10)
          : null,
      confirmed: data.confirmed,
    })
    setEditingId(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">Loading {title.toLowerCase()}...</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-white">{title}</h2>

      {items.map((item) =>
        editingId === item.id ? (
          <ItemForm
            key={item.id}
            initial={{
              detail: item.detail,
              amount: item.amount.toString(),
              frequency: item.frequency,
              due_date: item.due_date ?? '',
              monthly_day: item.monthly_day?.toString() ?? '',
              confirmed: item.confirmed,
            }}
            onSubmit={(data) => handleUpdate(item.id, data)}
            onCancel={() => setEditingId(null)}
            submitLabel="Save"
          />
        ) : (
          <div
            key={item.id}
            className={`bg-gray-900 rounded-xl p-4 border-l-4 ${
              item.confirmed ? 'border-l-green-500' : 'border-l-amber-500'
            }`}
          >
            <div className="flex items-start justify-between">
              <button
                type="button"
                onClick={() => setEditingId(item.id)}
                className="flex-1 text-left"
              >
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-white font-medium">{item.detail}</p>
                  <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                    {frequencyLabels[item.frequency]}
                  </span>
                </div>
                <p
                  className={`text-lg font-semibold ${
                    type === 'income' ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {formatCurrency(item.amount)}
                </p>
                {item.due_date && (
                  <p className="text-gray-500 text-xs mt-1">
                    Due: {item.due_date}
                  </p>
                )}
                {item.frequency === 'monthly' && item.monthly_day && (
                  <p className="text-gray-500 text-xs mt-1">
                    Day {item.monthly_day} of each month
                  </p>
                )}
                {!item.confirmed && (
                  <p className="text-amber-500 text-xs mt-1">Unconfirmed</p>
                )}
                {item.paid_through && (
                  <p className="text-blue-400 text-xs mt-1">
                    Paid through: {new Date(item.paid_through + 'T00:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </p>
                )}
              </button>
              <button
                type="button"
                onClick={() => onDelete(item.id)}
                className="text-gray-600 hover:text-red-400 text-xl ml-3 transition-colors"
                title="Delete item"
              >
                ✕
              </button>
            </div>
          </div>
        )
      )}

      {showForm ? (
        <ItemForm
          initial={emptyForm}
          onSubmit={handleAdd}
          onCancel={() => setShowForm(false)}
          submitLabel={`Add ${type}`}
        />
      ) : (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="w-full bg-gray-900 hover:bg-gray-800 text-blue-400 font-medium rounded-xl p-4 transition-colors border border-dashed border-gray-700"
        >
          + Add {type}
        </button>
      )}
    </div>
  )
}
