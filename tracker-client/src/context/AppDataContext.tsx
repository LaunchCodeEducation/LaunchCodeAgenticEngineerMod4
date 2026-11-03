import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  checkHealth,
  createSearch,
  deleteSearch,
  fetchListings,
  fetchSearches,
  runSearch,
  updateSearch as updateSearchApi,
} from '../api'
import type { Listing, NewSearchForm, RunSearchResult, SavedSearch } from '../types'

type AppDataContextValue = {
  searches: SavedSearch[]
  listings: Listing[]
  isLoading: boolean
  error: string | null
  isConnected: boolean | null
  runningId: string | null
  statusVersion: number
  refresh: () => Promise<void>
  saveSearch: (form: NewSearchForm) => Promise<SavedSearch>
  startWatching: (form: NewSearchForm) => Promise<SavedSearch>
  updateSearch: (id: string, form: NewSearchForm) => Promise<SavedSearch>
  removeSearch: (id: string) => Promise<void>
  checkMarketplace: (id: string) => Promise<RunSearchResult>
  bumpStatusVersion: () => void
}

const AppDataContext = createContext<AppDataContextValue | null>(null)

function formToPayload(form: NewSearchForm) {
  const query = form.query.trim()
  const location = form.location.trim()
  const radius = Number(form.radius)
  const maxPrice = form.maxPrice.trim() ? Number(form.maxPrice) : null
  const resultsPerSearch = Number(form.resultsPerSearch)
  const name = form.name.trim() || query

  return {
    name,
    query,
    location,
    radius,
    maxPrice,
    resultsPerSearch,
  }
}

export function AppDataProvider({ children }: { children: ReactNode }) {
  const [searches, setSearches] = useState<SavedSearch[]>([])
  const [listings, setListings] = useState<Listing[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState<boolean | null>(null)
  const [runningId, setRunningId] = useState<string | null>(null)
  const [statusVersion, setStatusVersion] = useState(0)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const [searchData, listingData, healthy] = await Promise.all([
        fetchSearches(),
        fetchListings(),
        checkHealth(),
      ])
      setSearches(searchData)
      setListings(listingData)
      setIsConnected(healthy)
    } catch {
      setError('Having trouble loading — make sure the app is running.')
      setIsConnected(false)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const saveSearch = useCallback(
    async (form: NewSearchForm): Promise<SavedSearch> => {
      const search = await createSearch(formToPayload(form))
      await refresh()
      return search
    },
    [refresh],
  )

  const startWatching = useCallback(
    async (form: NewSearchForm): Promise<SavedSearch> => {
      setError(null)
      return saveSearch(form)
    },
    [saveSearch],
  )

  const updateSearch = useCallback(
    async (id: string, form: NewSearchForm): Promise<SavedSearch> => {
      const search = await updateSearchApi(id, formToPayload(form))
      await refresh()
      return search
    },
    [refresh],
  )

  const removeSearch = useCallback(
    async (id: string) => {
      await deleteSearch(id)
      await refresh()
    },
    [refresh],
  )

  const checkMarketplace = useCallback(
    async (id: string): Promise<RunSearchResult> => {
      setRunningId(id)
      setError(null)

      try {
        const result = await runSearch(id)
        await refresh()
        return result
      } catch {
        setError("Couldn't check Marketplace just now. Try again in a moment.")
        throw new Error('check failed')
      } finally {
        setRunningId(null)
      }
    },
    [refresh],
  )

  const bumpStatusVersion = useCallback(() => {
    setStatusVersion((v) => v + 1)
  }, [])

  const value = useMemo(
    () => ({
      searches,
      listings,
      isLoading,
      error,
      isConnected,
      runningId,
      statusVersion,
      refresh,
      saveSearch,
      startWatching,
      updateSearch,
      removeSearch,
      checkMarketplace,
      bumpStatusVersion,
    }),
    [
      searches,
      listings,
      isLoading,
      error,
      isConnected,
      runningId,
      statusVersion,
      refresh,
      saveSearch,
      startWatching,
      updateSearch,
      removeSearch,
      checkMarketplace,
      bumpStatusVersion,
    ],
  )

  return (
    <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>
  )
}

export function useAppData() {
  const context = useContext(AppDataContext)
  if (!context) {
    throw new Error('useAppData must be used within AppDataProvider')
  }
  return context
}
