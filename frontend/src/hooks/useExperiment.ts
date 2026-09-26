import { useEffect, useState } from 'react'
import { API_BASE_URL } from '../services/api'

interface ExperimentFlags {
  [experimentName: string]: 'A' | 'B'
}

export function useExperimentFlags() {
  const [flags, setFlags] = useState<ExperimentFlags>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchFlags = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/experiments/flags`, {
          credentials: 'include',
        })
        if (response.ok) {
          const data = await response.json()
          setFlags(data.flags || {})
        }
      } catch (error) {
        console.error('Failed to fetch experiment flags:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchFlags()
  }, [])

  return { flags, loading }
}

export function useVariant(experimentName: string, defaultVariant: 'A' | 'B' = 'A') {
  const { flags } = useExperimentFlags()
  return flags[experimentName] || defaultVariant
}
