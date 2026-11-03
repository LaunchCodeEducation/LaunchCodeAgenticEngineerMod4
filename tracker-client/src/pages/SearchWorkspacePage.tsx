import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { CheckingProgress } from '../components/CheckingProgress'
import { ListingCard } from '../components/ListingCard'
import { WatchRowMenu } from '../components/WatchRowMenu'
import { useAppData } from '../context/AppDataContext'
import {
  getCheckCompleteMessage,
  getWorkspaceResultSummary,
  HELPERS,
} from '../lib/copy'
import {
  formatCheckedAt,
  formatWatchLocationLines,
} from '../lib/format'
import { partitionListingsForSearch } from '../lib/listings'

type LocationState = {
  justCreated?: boolean
  displayName?: string
  autoCheck?: boolean
}

export function SearchWorkspacePage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const locationState = location.state as LocationState | null
  const { searches, listings, isLoading, runningId, checkMarketplace, statusVersion } =
    useAppData()

  const [showPrevious, setShowPrevious] = useState(false)
  const [isChecking, setIsChecking] = useState(false)
  const [checkCompleteMessage, setCheckCompleteMessage] = useState<string | null>(
    null,
  )
  const autoCheckStarted = useRef(false)

  const search = searches.find((item) => item.id === id)

  const buckets = useMemo(() => {
    if (!search) return null
    return partitionListingsForSearch(listings, search, statusVersion)
  }, [listings, search, statusVersion])

  const newListings = buckets?.new ?? []
  const previousListings = useMemo(() => {
    if (!buckets) return []
    return [...buckets.reviewed, ...buckets.archived]
  }, [buckets])

  const handleCheck = useCallback(async () => {
    if (!search) return

    setIsChecking(true)
    setCheckCompleteMessage(null)

    try {
      const result = await checkMarketplace(search.id)
      setCheckCompleteMessage(getCheckCompleteMessage(result.newListings))
    } catch {
      // error shown via context
    } finally {
      setIsChecking(false)
    }
  }, [search, checkMarketplace])

  useEffect(() => {
    if (!search || !locationState?.autoCheck || autoCheckStarted.current) return

    autoCheckStarted.current = true
    navigate(location.pathname, {
      replace: true,
      state: {
        justCreated: locationState.justCreated,
        displayName: locationState.displayName,
      },
    })
    void handleCheck()
  }, [search, locationState, navigate, location.pathname, handleCheck])

  if (isLoading) {
    return <p className="text-sm text-stone-500">One moment…</p>
  }

  if (!search || !buckets) {
    return (
      <div>
        <p className="text-stone-600">We couldn&apos;t find that watch.</p>
        <p className="mt-2 text-sm text-stone-500">
          It may have been removed from your list.
        </p>
        <Link to="/" className="mt-4 inline-block text-sm text-stone-800 underline">
          Back to Home
        </Link>
      </div>
    )
  }

  const checking = isChecking || runningId === search.id
  const newCount = newListings.length
  const locationLines = formatWatchLocationLines(search)

  const statusMessage = checking
    ? null
    : checkCompleteMessage ?? getWorkspaceResultSummary(newCount)

  return (
    <div className="space-y-8">
      <header className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <Link
            to="/"
            className="inline-flex min-h-11 items-center text-sm text-stone-500 active:text-stone-800"
          >
            ← Home
          </Link>
          <WatchRowMenu search={search} />
        </div>

        {locationState?.justCreated && (
          <p className="text-sm text-stone-600">
            Now watching &ldquo;{locationState.displayName ?? search.name}&rdquo;.
          </p>
        )}

        <div>
          <h1 className="text-[22px] font-semibold tracking-tight text-stone-900 sm:text-2xl">
            {search.name}
          </h1>
          <div className="mt-2 space-y-0.5 text-sm text-stone-500">
            {locationLines.map((line) => (
              <p key={line}>{line}</p>
            ))}
          </div>
          <p className="mt-2 text-sm text-stone-400">
            {formatCheckedAt(search.lastCheckedAt)}
          </p>
          <div className="mt-3 text-[15px] text-stone-700">
            {checking ? <CheckingProgress /> : statusMessage}
          </div>
        </div>

        {!checking && (
          <button
            type="button"
            onClick={() => void handleCheck()}
            className="flex min-h-12 w-full items-center justify-center rounded-2xl bg-stone-900 text-[15px] font-medium text-white active:bg-stone-800 sm:w-auto sm:px-5"
          >
            Check Marketplace
          </button>
        )}
      </header>

      {newCount > 0 && !checking && (
        <section className="space-y-3">
          <p className="text-xs text-stone-400">{HELPERS.newListingsOnly}</p>
          <ul className="grid gap-3 sm:grid-cols-2 sm:gap-4">
            {newListings.map((listing) => (
              <li key={listing.id}>
                <ListingCard listing={listing} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {previousListings.length > 0 && (
        <section className="border-t border-stone-200/60 pt-6">
          <button
            type="button"
            onClick={() => setShowPrevious((v) => !v)}
            className="inline-flex min-h-11 items-center text-sm text-stone-500 active:text-stone-800"
          >
            {showPrevious ? 'Hide' : 'View'} previously found (
            {previousListings.length})
          </button>

          {showPrevious && (
            <ul className="mt-4 grid gap-3 sm:grid-cols-2 sm:gap-4">
              {previousListings.map((listing) => (
                <li key={listing.id}>
                  <ListingCard listing={listing} />
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  )
}
