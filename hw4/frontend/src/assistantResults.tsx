import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ProductResults } from './api'

/**
 * Shared state for the products the chatbot wants on the page.
 * ChatWidget writes it when /api/chat returns `results`; AssistantResults renders it.
 * `version` changes on every update so the section can scroll into view and re-animate.
 */
interface AssistantResultsState {
  results: ProductResults | null
  version: number
  show: (results: ProductResults) => void
  clear: () => void
}

const AssistantResultsContext = createContext<AssistantResultsState | null>(null)

export function AssistantResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ProductResults | null>(null)
  const [version, setVersion] = useState(0)

  const value: AssistantResultsState = {
    results,
    version,
    show: (r) => {
      setResults(r)
      setVersion((v) => v + 1)
    },
    clear: () => setResults(null),
  }
  return <AssistantResultsContext.Provider value={value}>{children}</AssistantResultsContext.Provider>
}

export function useAssistantResults(): AssistantResultsState {
  const ctx = useContext(AssistantResultsContext)
  if (!ctx) throw new Error('useAssistantResults must be used inside <AssistantResultsProvider>')
  return ctx
}
