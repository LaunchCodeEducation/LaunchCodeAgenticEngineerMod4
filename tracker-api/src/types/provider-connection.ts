/**
 * Shared connection-management types for external marketplace providers.
 * Facebook is the first implementation; additional providers can reuse this shape.
 */

export type ProviderId = 'facebook'

export type ConnectionStatus =
  | 'not_connected'
  | 'connected'
  | 'session_expired'
  | 'connection_error'

export type ProviderConnection = {
  providerId: ProviderId
  displayName: string
  description: string
  status: ConnectionStatus
  lastConnectedAt: string | null
  message: string | null
}

export type ConnectActionMode =
  | 'external_script'
  | 'not_implemented'

export type ConnectProviderResult = {
  providerId: ProviderId
  connection: ProviderConnection
  action: {
    mode: ConnectActionMode
    /** Local auth utility command when mode is external_script */
    command: string | null
    message: string
  }
}

export type DisconnectProviderResult = {
  providerId: ProviderId
  implemented: boolean
  message: string
  connection: ProviderConnection
}
