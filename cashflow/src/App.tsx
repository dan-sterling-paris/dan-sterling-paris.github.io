import { useState, useMemo, useCallback } from 'react'
import TokenGate from './components/TokenGate'
import BottomNav, { type Tab } from './components/BottomNav'
import GapHeader from './components/GapHeader'
import Dashboard from './components/Dashboard'
import AccountsList from './components/AccountsList'
import ItemsList from './components/ItemsList'
import WeeklyView from './components/WeeklyView'
import KeepCalm from './components/KeepCalm'
import LoansList from './components/LoansList'
import { useAccounts } from './hooks/useAccounts'
import { useItems } from './hooks/useItems'
import { useLoans } from './hooks/useLoans'
import { useSelections } from './hooks/useSelections'
import { applySelections } from './lib/applySelections'

function AuthenticatedApp() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')

  const { accounts, loading: accountsLoading, addAccount, updateAccount, deleteAccount } = useAccounts()
  const { items: incomeItems, loading: incomeLoading, addItem: addIncome, updateItem: updateIncome, deleteItem: deleteIncome } = useItems('income')
  const { items: expenseItems, loading: expenseLoading, addItem: addExpense, updateItem: updateExpense, deleteItem: deleteExpense } = useItems('expense')
  const { loans, loading: loansLoading, addLoan, updateLoan, deleteLoan } = useLoans()
  const { selectedIds, toggleSelected, clearSelections } = useSelections()

  const updateAnyItem = useCallback(
    async (id: string, updates: Partial<Omit<import('./lib/types').CashflowItem, 'id' | 'created_at'>>) => {
      if (incomeItems.some((i) => i.id === id)) {
        await updateIncome(id, updates)
      } else {
        await updateExpense(id, updates)
      }
    },
    [incomeItems, updateIncome, updateExpense]
  )

  const allItems = useMemo(
    () => [...incomeItems, ...expenseItems],
    [incomeItems, expenseItems]
  )

  const modifiedItems = useMemo(
    () => applySelections(allItems, selectedIds),
    [allItems, selectedIds]
  )

  const modifiedIncome = useMemo(
    () => modifiedItems.filter((i) => i.type === 'income'),
    [modifiedItems]
  )
  const modifiedExpenses = useMemo(
    () => modifiedItems.filter((i) => i.type === 'expense'),
    [modifiedItems]
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <GapHeader accounts={accounts} items={modifiedItems} loans={loans} />
      <div className="max-w-lg mx-auto px-4 pt-4 pb-20">
        {activeTab === 'dashboard' && (
          <Dashboard
            accounts={accounts}
            incomeItems={modifiedIncome}
            expenseItems={modifiedExpenses}
            loans={loans}
          />
        )}
        {activeTab === 'weekly' && (
          <WeeklyView
            accounts={accounts}
            incomeItems={modifiedIncome}
            expenseItems={modifiedExpenses}
            loans={loans}
            onUpdateItem={updateAnyItem}
          />
        )}
        {activeTab === 'keepcalm' && (
          <KeepCalm
            accounts={accounts}
            incomeItems={incomeItems}
            expenseItems={expenseItems}
            loans={loans}
            selectedIds={selectedIds}
            onToggle={toggleSelected}
            onClear={clearSelections}
          />
        )}
        {activeTab === 'loans' && (
          <LoansList
            loans={loans}
            loading={loansLoading}
            onAdd={addLoan}
            onUpdate={updateLoan}
            onDelete={deleteLoan}
          />
        )}
        {activeTab === 'accounts' && (
          <AccountsList
            accounts={accounts}
            loading={accountsLoading}
            onAdd={addAccount}
            onUpdate={updateAccount}
            onDelete={deleteAccount}
          />
        )}
        {activeTab === 'income' && (
          <ItemsList
            type="income"
            items={incomeItems}
            loading={incomeLoading}
            onAdd={addIncome}
            onUpdate={updateIncome}
            onDelete={deleteIncome}
          />
        )}
        {activeTab === 'expenses' && (
          <ItemsList
            type="expense"
            items={expenseItems}
            loading={expenseLoading}
            onAdd={addExpense}
            onUpdate={updateExpense}
            onDelete={deleteExpense}
          />
        )}
      </div>
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}

export default function App() {
  const [authed, setAuthed] = useState(
    () => localStorage.getItem('cashflow_auth') === 'true'
  )

  if (!authed) {
    return <TokenGate onAuth={() => setAuthed(true)} />
  }

  return <AuthenticatedApp />
}
