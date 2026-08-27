import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import type { Account } from '../lib/types'

export function useAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)

  const fetchAccounts = useCallback(async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('accounts')
      .select('*')
      .order('created_at', { ascending: true })
    if (error) {
      console.error('Failed to fetch accounts:', error)
    } else {
      setAccounts(data ?? [])
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchAccounts()
  }, [fetchAccounts])

  const addAccount = async (name: string, balance: number) => {
    const { error } = await supabase
      .from('accounts')
      .insert({ name, balance })
    if (error) {
      console.error('Failed to add account:', error)
      return
    }
    await fetchAccounts()
  }

  const updateAccount = async (id: string, updates: Partial<Pick<Account, 'name' | 'balance'>>) => {
    const { error } = await supabase
      .from('accounts')
      .update(updates)
      .eq('id', id)
    if (error) {
      console.error('Failed to update account:', error)
      return
    }
    await fetchAccounts()
  }

  const deleteAccount = async (id: string) => {
    const { error } = await supabase
      .from('accounts')
      .delete()
      .eq('id', id)
    if (error) {
      console.error('Failed to delete account:', error)
      return
    }
    await fetchAccounts()
  }

  return { accounts, loading, addAccount, updateAccount, deleteAccount }
}
