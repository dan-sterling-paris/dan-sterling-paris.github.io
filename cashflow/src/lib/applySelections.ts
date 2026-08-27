import { startOfWeek, format } from 'date-fns'
import type { CashflowItem } from './types'

export function applySelections(
  items: CashflowItem[],
  selectedIds: Set<string>
): CashflowItem[] {
  if (selectedIds.size === 0) return items

  const todayStr = format(
    startOfWeek(new Date(), { weekStartsOn: 1 }),
    'yyyy-MM-dd'
  )

  return items.map((item) => {
    if (!selectedIds.has(item.id)) return item

    if (item.type === 'income') {
      // Bring forward to this week
      if (item.frequency === 'once' || item.frequency === 'weekly') {
        return { ...item, due_date: todayStr }
      }
      return item
    }

    if (item.type === 'expense') {
      // Push beyond forecast window
      if (item.frequency === 'once') {
        return { ...item, due_date: '2099-12-31' }
      }
      if (item.frequency === 'monthly') {
        return {
          ...item,
          frequency: 'once' as const,
          monthly_day: null,
          due_date: '2099-12-31',
        }
      }
    }

    return item
  })
}
