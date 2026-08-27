import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'

export function useSelections() {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    supabase
      .from('keepcalm_selections')
      .select('item_id')
      .then(({ data }) => {
        if (data) {
          setSelectedIds(new Set(data.map((r) => r.item_id)))
        }
        setLoaded(true)
      })
  }, [])

  const toggleSelected = useCallback(
    async (id: string) => {
      setSelectedIds((prev) => {
        const next = new Set(prev)
        if (next.has(id)) {
          next.delete(id)
          supabase.from('keepcalm_selections').delete().eq('item_id', id).then()
        } else {
          next.add(id)
          supabase.from('keepcalm_selections').insert({ item_id: id }).then()
        }
        return next
      })
    },
    []
  )

  const clearSelections = useCallback(async () => {
    setSelectedIds(new Set())
    await supabase.from('keepcalm_selections').delete().neq('item_id', '')
  }, [])

  return { selectedIds, loaded, toggleSelected, clearSelections }
}
