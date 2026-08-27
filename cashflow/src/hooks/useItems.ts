import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import type { CashflowItem } from '../lib/types'

export function useItems(type: 'income' | 'expense') {
  const [items, setItems] = useState<CashflowItem[]>([])
  const [loading, setLoading] = useState(true)

  const fetchItems = useCallback(async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('cashflow_items')
      .select('*')
      .eq('type', type)
      .order('created_at', { ascending: true })
    if (error) {
      console.error('Failed to fetch items:', error)
    } else {
      setItems(data ?? [])
    }
    setLoading(false)
  }, [type])

  useEffect(() => {
    fetchItems()
  }, [fetchItems])

  const addItem = async (
    item: Omit<CashflowItem, 'id' | 'created_at'>
  ) => {
    const { error } = await supabase.from('cashflow_items').insert(item)
    if (error) {
      console.error('Failed to add item:', error)
      return
    }
    await fetchItems()
  }

  const updateItem = async (
    id: string,
    updates: Partial<Omit<CashflowItem, 'id' | 'created_at'>>
  ) => {
    const { error } = await supabase
      .from('cashflow_items')
      .update(updates)
      .eq('id', id)
    if (error) {
      console.error('Failed to update item:', error)
      return
    }
    await fetchItems()
  }

  const deleteItem = async (id: string) => {
    const { error } = await supabase
      .from('cashflow_items')
      .delete()
      .eq('id', id)
    if (error) {
      console.error('Failed to delete item:', error)
      return
    }
    await fetchItems()
  }

  return { items, loading, addItem, updateItem, deleteItem }
}
