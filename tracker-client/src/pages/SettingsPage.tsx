import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchConnections } from '../api'
import { ProviderConnectionCard } from '../components/connections/ProviderConnectionCard'
import { SectionLabel } from '../components/SectionLabel'
import { useFacebookConnection } from '../context/FacebookConnectionContext'
import type { ProviderConnection } from '../types'

export function SettingsPage() {
  const { refreshStatus } = useFacebookConnection()
  const [connections, setConnections] = useState<ProviderConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchConnections()
        if (!cancelled) setConnections(data)
      } catch {
        if (!cancelled) setError('Could not load connections.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleUpdated(next: ProviderConnection) {
    setConnections((prev) =>
      prev.map((item) =>
        item.providerId === next.providerId ? next : item,
      ),
    )
    if (next.providerId === 'facebook') {
      await refreshStatus()
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/"
          className="inline-flex min-h-11 items-center text-sm text-stone-500 active:text-stone-800"
        >
          ← Home
        </Link>
        <h1 className="mt-2 text-[22px] font-semibold tracking-tight text-stone-900">
          Settings
        </h1>
        <p className="mt-1 text-sm text-stone-500">
          Optional. Scout searches Marketplace anonymously by default.
        </p>
      </div>

      <div className="space-y-3">
        <SectionLabel>Providers</SectionLabel>

        {loading && <p className="text-sm text-stone-500">Loading…</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}

        {!loading &&
          !error &&
          connections.map((connection) => (
            <ProviderConnectionCard
              key={connection.providerId}
              connection={connection}
              onUpdated={handleUpdated}
            />
          ))}

        {!loading && !error && connections.length === 0 && (
          <p className="text-sm text-stone-500">No providers yet.</p>
        )}
      </div>
    </div>
  )
}
