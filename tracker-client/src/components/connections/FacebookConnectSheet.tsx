import { useEffect, useState } from 'react'
import type { ConnectionStatus } from '../../types'

type Props = {
  open: boolean
  mode: 'connect' | 'reconnect'
  onDismiss: () => void
  onConnected: () => void | Promise<void>
  startConnect: () => Promise<void>
  refreshStatus: () => Promise<ConnectionStatus | null>
}

type Phase = 'intro' | 'waiting'

export function FacebookConnectSheet({
  open,
  mode,
  onDismiss,
  onConnected,
  startConnect,
  refreshStatus,
}: Props) {
  const [phase, setPhase] = useState<Phase>('intro')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      setPhase('intro')
      setBusy(false)
      setError(null)
    }
  }, [open])

  useEffect(() => {
    if (!open || phase !== 'waiting') return

    const interval = window.setInterval(() => {
      void (async () => {
        const status = await refreshStatus()
        if (status === 'connected') {
          await onConnected()
        }
      })()
    }, 2500)

    return () => window.clearInterval(interval)
  }, [open, phase, refreshStatus, onConnected])

  if (!open) return null

  const title = mode === 'reconnect' ? 'Reconnect Facebook' : 'Connect Facebook'
  const primaryLabel =
    mode === 'reconnect' ? 'Reconnect Facebook' : 'Connect Facebook'

  async function handlePrimary() {
    setBusy(true)
    setError(null)
    try {
      await startConnect()
      const status = await refreshStatus()
      if (status === 'connected') {
        await onConnected()
        return
      }
      setPhase('waiting')
    } catch {
      setError('Could not start Facebook connection. Try again.')
    } finally {
      setBusy(false)
    }
  }

  async function handleContinue() {
    setBusy(true)
    setError(null)
    try {
      const status = await refreshStatus()
      if (status === 'connected') {
        await onConnected()
      } else {
        setError('Facebook is not connected yet. Finish signing in, then try again.')
      }
    } catch {
      setError('Could not check connection status.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4">
      <button
        type="button"
        className="absolute inset-0 bg-stone-900/40"
        aria-label="Dismiss"
        onClick={onDismiss}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="facebook-connect-title"
        className="relative z-10 w-full max-w-md rounded-t-3xl border border-stone-200/80 bg-[#f7f6f3] px-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-4 shadow-xl shadow-stone-900/10 sm:rounded-3xl sm:pb-5"
      >
        <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-stone-300 sm:hidden" />

        {phase === 'intro' && (
          <div className="space-y-5">
            <div>
              <h2
                id="facebook-connect-title"
                className="text-[20px] font-semibold tracking-tight text-stone-900"
              >
                {title}
              </h2>
              <p className="mt-2 text-[15px] leading-relaxed text-stone-600">
                Optional authenticated Facebook session.
              </p>
              <p className="mt-2 text-[15px] leading-relaxed text-stone-600">
                Scout searches Marketplace anonymously by default.
              </p>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex flex-col gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => void handlePrimary()}
                className="flex min-h-12 items-center justify-center rounded-2xl bg-stone-900 text-[15px] font-medium text-white active:bg-stone-800 disabled:opacity-60"
              >
                {busy ? 'Starting…' : primaryLabel}
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={onDismiss}
                className="flex min-h-12 items-center justify-center rounded-2xl text-[15px] font-medium text-stone-500 active:bg-stone-200/50"
              >
                Not now
              </button>
            </div>
          </div>
        )}

        {phase === 'waiting' && (
          <div className="space-y-5">
            <div>
              <h2
                id="facebook-connect-title"
                className="text-[20px] font-semibold tracking-tight text-stone-900"
              >
                Finish signing in
              </h2>
              <p className="mt-2 text-[15px] leading-relaxed text-stone-600">
                Complete Facebook login when prompted. When you&apos;re done,
                return here and continue — Scout will pick up where you left
                off.
              </p>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex flex-col gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleContinue()}
                className="flex min-h-12 items-center justify-center rounded-2xl bg-stone-900 text-[15px] font-medium text-white active:bg-stone-800 disabled:opacity-60"
              >
                {busy ? 'Checking…' : 'Continue'}
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={onDismiss}
                className="flex min-h-12 items-center justify-center rounded-2xl text-[15px] font-medium text-stone-500 active:bg-stone-200/50"
              >
                Not now
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
