export type Tab = 'dashboard' | 'weekly' | 'keepcalm' | 'loans' | 'accounts' | 'income' | 'expenses'

interface BottomNavProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
}

const tabs: { id: Tab; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'weekly', label: 'Weekly' },
  { id: 'keepcalm', label: 'Keep Calm' },
  { id: 'loans', label: 'Loans' },
  { id: 'accounts', label: 'Accounts' },
  { id: 'income', label: 'Income' },
  { id: 'expenses', label: 'Expenses' },
]

export default function BottomNav({ activeTab, onTabChange }: BottomNavProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 z-50">
      <div className="max-w-lg mx-auto flex overflow-x-auto scrollbar-hide">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onTabChange(tab.id)}
            className={`shrink-0 px-4 py-3 text-xs font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'text-blue-400 border-t-2 border-blue-400'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
