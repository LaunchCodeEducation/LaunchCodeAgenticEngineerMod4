import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import {
  connectProvider,
  fetchConnection,
  reconnectProvider,
} from '../api'
import type { ConnectionStatus } from '../types'
import { FacebookConnectSheet } from '../components/connections/FacebookConnectSheet'

export function isFacebookMarketplaceReady(status: ConnectionStatus | null): boolean {
  return status === 'connected'
}

export function facebookNeedsAttention(status: ConnectionStatus | null): boolean {
  return status !== 'connected'
}

type EnsureOptions = {
  /** Prefer reconnect copy when session is expired/errored */
  preferReconnect?: boolean
}

type FacebookConnectionContextValue = {
  status: ConnectionStatus | null
  isLoading: boolean
  isReady: boolean
  needsAttention: boolean
  refreshStatus: () => Promise<ConnectionStatus | null>
  openConnectFlow: (options?: EnsureOptions) => void
  /** Resolves true when connected (or already ready); false if dismissed */
  ensureFacebookConnected: (options?: EnsureOptions) => Promise<boolean>
}

const FacebookConnectionContext =
  createContext<FacebookConnectionContextValue | null>(null)

export function FacebookConnectionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ConnectionStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSheetOpen, setIsSheetOpen] = useState(false)
  const [sheetMode, setSheetMode] = useState<'connect' | 'reconnect'>('connect')

  const pendingResolveRef = useRef<((ready: boolean) => void) | null>(null)

  const refreshStatus = useCallback(async (): Promise<ConnectionStatus | null> => {
    try {
      const connection = await fetchConnection('facebook')
      setStatus(connection.status)
      return connection.status
    } catch {
      setStatus(null)
      return null
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      try {
        const connection = await fetchConnection('facebook')
        if (!cancelled) setStatus(connection.status)
      } catch {
        if (!cancelled) setStatus(null)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  const settlePending = useCallback((ready: boolean) => {
    const resolve = pendingResolveRef.current
    pendingResolveRef.current = null
    resolve?.(ready)
  }, [])

  const closeSheet = useCallback(
    (ready: boolean) => {
      setIsSheetOpen(false)
      settlePending(ready)
    },
    [settlePending],
  )

  const openConnectFlow = useCallback(
    (options?: EnsureOptions) => {
      const reconnect =
        options?.preferReconnect ||
        status === 'session_expired' ||
        status === 'connection_error'
      setSheetMode(reconnect ? 'reconnect' : 'connect')
      setIsSheetOpen(true)
    },
    [status],
  )

  const ensureFacebookConnected = useCallback(
    (options?: EnsureOptions) => {
      if (status === 'connected') {
        return Promise.resolve(true)
      }

      return new Promise<boolean>((resolve) => {
        pendingResolveRef.current = resolve
        const reconnect =
          options?.preferReconnect ||
          status === 'session_expired' ||
          status === 'connection_error'
        setSheetMode(reconnect ? 'reconnect' : 'connect')
        setIsSheetOpen(true)
      })
    },
    [status],
  )

  const handleConnected = useCallback(async () => {
    const next = await refreshStatus()
    if (next === 'connected') {
      closeSheet(true)
    }
  }, [refreshStatus, closeSheet])

  const handleDismiss = useCallback(() => {
    closeSheet(false)
  }, [closeSheet])

  const startProviderConnect = useCallback(async () => {
    if (sheetMode === 'reconnect') {
      await reconnectProvider('facebook')
    } else {
      await connectProvider('facebook')
    }
  }, [sheetMode])

  const value = useMemo<FacebookConnectionContextValue>(
    () => ({
      status,
      isLoading,
      isReady: isFacebookMarketplaceReady(status),
      needsAttention: facebookNeedsAttention(status),
      refreshStatus,
      openConnectFlow,
      ensureFacebookConnected,
    }),
    [
      status,
      isLoading,
      refreshStatus,
      openConnectFlow,
      ensureFacebookConnected,
    ],
  )

  return (
    <FacebookConnectionContext.Provider value={value}>
      {children}
      <FacebookConnectSheet
        open={isSheetOpen}
        mode={sheetMode}
        onDismiss={handleDismiss}
        onConnected={handleConnected}
        startConnect={startProviderConnect}
        refreshStatus={refreshStatus}
      />
    </FacebookConnectionContext.Provider>
  )
}

export function useFacebookConnection() {
  const context = useContext(FacebookConnectionContext)
  if (!context) {
    throw new Error(
      'useFacebookConnection must be used within FacebookConnectionProvider',
    )
  }
  return context
}
