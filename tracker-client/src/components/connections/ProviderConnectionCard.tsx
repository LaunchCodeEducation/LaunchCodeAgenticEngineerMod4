import { useState } from 'react'
import {
  connectProvider,
  disconnectProvider,
  fetchConnection,
  reconnectProvider,
} from '../../api'
import { formatRelativeTime } from '../../lib/format'
import type {
  ConnectProviderResult,
  ProviderConnection,
} from '../../types'
import { ConnectionStatusBadge } from './ConnectionStatusBadge'

type ProviderConnectionCardProps = {
  connection: ProviderConnection
  onUpdated: (connection: ProviderConnection) => void
}

export function ProviderConnectionCard({
  connection,
  onUpdated,
}: ProviderConnectionCardProps) {
  const [busy, setBusy] = useState(false)
  const [actionNote, setActionNote] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { status, providerId } = connection
  const needsConnect = status === 'not_connected'
  const needsReconnect =
    status === 'session_expired' || status === 'connection_error'
  const isConnected = status === 'connected'

  async function refreshStatus() {
    setBusy(true)
    setError(null)
    try {
      const next = await fetchConnection(providerId)
      onUpdated(next)
      setActionNote(null)
    } catch {
      setError('Could not refresh connection status.')
    } finally {
      setBusy(false)
    }
  }

  async function handleConnectOrReconnect(mode: 'connect' | 'reconnect') {
    setBusy(true)
    setError(null)
    try {
      const result: ConnectProviderResult =
        mode === 'reconnect'
          ? await reconnectProvider(providerId)
          : await connectProvider(providerId)

      onUpdated(result.connection)
      const commandHint = result.action.command
        ? ` Run \`${result.action.command}\` in tracker-api.`
        : ''
      setActionNote(`${result.action.message}${commandHint}`)
    } catch {
      setError(
        mode === 'reconnect'
          ? 'Could not start reconnection.'
          : 'Could not start connection.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function handleDisconnect() {
    setBusy(true)
    setError(null)
    try {
      const result = await disconnectProvider(providerId)
      onUpdated(result.connection)
      setActionNote(result.message)
    } catch {
      setError('Could not disconnect.')
    } finally {
      setBusy(false)
    }
  }

  const lastConnectedLabel = connection.lastConnectedAt
    ? formatRelativeTime(connection.lastConnectedAt)
    : 'Unavailable'

  return (
    <section className="rounded-2xl border border-stone-200/70 bg-white p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-[17px] font-semibold tracking-tight text-stone-900">
            {connection.displayName}
          </h2>
          <p className="mt-1 text-sm text-stone-500">
            Optional authenticated Facebook session
          </p>
          <p className="mt-1 text-sm text-stone-500">
            Scout searches Marketplace anonymously by default.
          </p>
        </div>
        <ConnectionStatusBadge status={status} />
      </div>

      <dl className="mt-4 grid gap-3 border-t border-stone-100 pt-4 sm:grid-cols-2">
        <div>
          <dt className="text-[13px] text-stone-400">Status</dt>
          <dd className="mt-1 text-sm text-stone-800">
            <ConnectionStatusBadge status={status} />
          </dd>
        </div>
        <div>
          <dt className="text-[13px] text-stone-400">Last connected</dt>
          <dd className="mt-1 text-sm text-stone-800">{lastConnectedLabel}</dd>
        </div>
      </dl>

      {connection.message && (
        <p className="mt-4 text-sm text-stone-600">{connection.message}</p>
      )}

      {actionNote && (
        <p className="mt-3 rounded-xl bg-stone-50 px-3.5 py-3 text-sm text-stone-700">
          {actionNote}
        </p>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        {needsConnect && (
          <button
            type="button"
            disabled={busy}
            onClick={() => handleConnectOrReconnect('connect')}
            className="flex min-h-11 items-center justify-center rounded-xl bg-stone-900 px-4 text-sm font-medium text-white active:bg-stone-800 disabled:opacity-50"
          >
            Connect Facebook
          </button>
        )}

        {(needsReconnect || isConnected) && (
          <button
            type="button"
            disabled={busy}
            onClick={() => handleConnectOrReconnect('reconnect')}
            className="flex min-h-11 items-center justify-center rounded-xl bg-stone-900 px-4 text-sm font-medium text-white active:bg-stone-800 disabled:opacity-50"
          >
            Reconnect Facebook
          </button>
        )}

        <button
          type="button"
          disabled={busy}
          onClick={refreshStatus}
          className="flex min-h-11 items-center justify-center rounded-xl border border-stone-200 bg-white px-4 text-sm font-medium text-stone-700 active:bg-stone-50 disabled:opacity-50"
        >
          Refresh status
        </button>

        <button
          type="button"
          disabled={busy || needsConnect}
          onClick={handleDisconnect}
          title="Disconnect is not fully implemented yet"
          className="flex min-h-11 items-center justify-center rounded-xl border border-stone-200 bg-white px-4 text-sm font-medium text-stone-500 active:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Disconnect
        </button>
      </div>
    </section>
  )
}
