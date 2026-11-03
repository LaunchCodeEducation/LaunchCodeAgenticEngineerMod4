import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppData } from '../context/AppDataContext'
import type { NewSearchForm } from '../types'

const SUGGESTIONS = [
  'PS5',
  'Road bike',
  'Floor lamp',
  'Canon camera',
  'Patio furniture',
  'Pokemon cards',
]

const RESULTS_OPTIONS = ['5', '10', '20', '50'] as const

const defaultDetails = {
  location: 'Philadelphia',
  radius: '25',
  maxPrice: '',
  resultsPerSearch: '10',
  name: '',
}

type Props = {
  isFirstVisit?: boolean
}

export function WatchSearch({ isFirstVisit = false }: Props) {
  const navigate = useNavigate()
  const { startWatching } = useAppData()

  const [query, setQuery] = useState('')
  const [showDetails, setShowDetails] = useState(false)
  const [details, setDetails] = useState(defaultDetails)
  const [phase, setPhase] = useState<'idle' | 'setting-up'>('idle')
  const [error, setError] = useState<string | null>(null)

  function revealDetails() {
    const trimmed = query.trim()
    if (!trimmed) return
    setQuery(trimmed)
    setShowDetails(true)
    setError(null)
  }

  function handleQueryKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') {
      event.preventDefault()
      revealDetails()
    }
  }

  function updateDetail(field: keyof typeof defaultDetails, value: string) {
    setDetails((current) => ({ ...current, [field]: value }))
  }

  async function handleStartWatching(event: React.FormEvent) {
    event.preventDefault()
    if (!query.trim() || !details.location.trim() || !details.radius.trim()) return

    const form: NewSearchForm = {
      query: query.trim(),
      name: details.name,
      location: details.location,
      radius: details.radius,
      maxPrice: details.maxPrice,
      resultsPerSearch: details.resultsPerSearch,
    }

    setPhase('setting-up')
    setError(null)

    try {
      const search = await startWatching(form)
      navigate(`/search/${search.id}`, {
        state: {
          justCreated: true,
          displayName: search.name,
          autoCheck: true,
        },
      })
    } catch {
      setPhase('idle')
      setError("That didn't work — try again.")
    }
  }

  return (
    <section className="space-y-4">
      <div>
        <label
          htmlFor="watch-search"
          className="block text-[17px] font-semibold tracking-tight text-stone-900"
        >
          What should I search for?
        </label>
        <p className="mt-1 text-sm text-stone-500">
          Search once. Scout keeps watching.
        </p>
        <input
          id="watch-search"
          type="search"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            if (showDetails && !e.target.value.trim()) setShowDetails(false)
          }}
          onKeyDown={handleQueryKeyDown}
          placeholder="PS5, bike, camera…"
          className="mt-3 w-full rounded-2xl border border-stone-200/80 bg-white px-4 py-3.5 text-[17px] text-stone-900 shadow-sm shadow-stone-900/5 placeholder:text-stone-400 focus:border-stone-300 focus:outline-none"
          autoComplete="off"
          enterKeyHint="search"
          autoCapitalize="off"
          autoCorrect="off"
        />
      </div>

      {!showDetails && (
        <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                setQuery(suggestion)
              }}
              className="shrink-0 rounded-full bg-stone-200/50 px-3.5 py-2 text-sm text-stone-600 active:bg-stone-200"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {isFirstVisit && !showDetails && (
        <p className="text-sm text-stone-500">
          Monitoring starts after you save a search.
        </p>
      )}

      {showDetails && (
        <form
          onSubmit={handleStartWatching}
          className="space-y-4 border-t border-stone-200/60 pt-4"
        >
          <p className="text-sm text-stone-600">
            Watching for{' '}
            <span className="font-medium text-stone-900">{query.trim()}</span>
          </p>

          <Field label="Location">
            <input
              value={details.location}
              onChange={(e) => updateDetail('location', e.target.value)}
              placeholder="Philadelphia"
              required
              className={inputClass}
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Radius">
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  inputMode="numeric"
                  value={details.radius}
                  onChange={(e) => updateDetail('radius', e.target.value)}
                  placeholder="25"
                  required
                  min={1}
                  className={inputClass}
                />
                <span className="shrink-0 text-sm text-stone-500">mi</span>
              </div>
            </Field>

            <Field label="Max price">
              <div className="flex items-center gap-2">
                <span className="shrink-0 text-sm text-stone-500">$</span>
                <input
                  type="number"
                  inputMode="numeric"
                  value={details.maxPrice}
                  onChange={(e) => updateDetail('maxPrice', e.target.value)}
                  placeholder="Any"
                  min={1}
                  className={inputClass}
                />
              </div>
            </Field>
          </div>

          <Field label="Listings to check">
            <div className="flex flex-wrap gap-2">
              {RESULTS_OPTIONS.map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => updateDetail('resultsPerSearch', value)}
                  className={`min-h-11 min-w-11 rounded-full px-3.5 text-sm font-medium ${
                    details.resultsPerSearch === value
                      ? 'bg-stone-900 text-white'
                      : 'bg-stone-200/50 text-stone-600 active:bg-stone-200'
                  }`}
                >
                  {value}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Nickname">
            <input
              value={details.name}
              onChange={(e) => updateDetail('name', e.target.value)}
              placeholder={query.trim() || 'Optional'}
              className={inputClass}
            />
          </Field>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={phase === 'setting-up'}
            className="flex min-h-12 w-full items-center justify-center rounded-2xl bg-stone-900 text-[15px] font-medium text-white active:bg-stone-800 disabled:opacity-60 sm:w-auto sm:px-6"
          >
            {phase === 'setting-up' ? 'Setting up…' : 'Start watching'}
          </button>
        </form>
      )}
    </section>
  )
}

function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <label className="block">
      <span className="text-sm text-stone-500">{label}</span>
      <div className="mt-1.5">{children}</div>
    </label>
  )
}

const inputClass =
  'min-h-11 w-full rounded-xl border border-stone-200/80 bg-white px-3.5 text-[16px] text-stone-900 placeholder:text-stone-400 focus:border-stone-300 focus:outline-none'
