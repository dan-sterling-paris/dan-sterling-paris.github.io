import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import type { Loan } from '../lib/types'

export function useLoans() {
  const [loans, setLoans] = useState<Loan[]>([])
  const [loading, setLoading] = useState(true)

  const fetchLoans = useCallback(async () => {
    const { data } = await supabase
      .from('loans')
      .select('*')
      .order('settled', { ascending: true })
      .order('loan_date', { ascending: true })
    if (data) setLoans(data)
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchLoans()
  }, [fetchLoans])

  const addLoan = async (loan: Omit<Loan, 'id' | 'created_at'>) => {
    await supabase.from('loans').insert(loan)
    fetchLoans()
  }

  const updateLoan = async (id: string, updates: Partial<Loan>) => {
    await supabase.from('loans').update(updates).eq('id', id)
    fetchLoans()
  }

  const deleteLoan = async (id: string) => {
    await supabase.from('loans').delete().eq('id', id)
    fetchLoans()
  }

  return { loans, loading, addLoan, updateLoan, deleteLoan }
}
