import type {
  ConnectProviderResult,
  DisconnectProviderResult,
  ProviderConnection,
  ProviderId,
} from '../../types/provider-connection'

/**
 * Contract for a provider's connection lifecycle.
 * Scraping stays separate — this only manages "is Scout linked to this service?"
 */
export type ProviderConnectionService = {
  readonly providerId: ProviderId
  getConnection(): Promise<ProviderConnection>
  connect(): Promise<ConnectProviderResult>
  reconnect(): Promise<ConnectProviderResult>
  disconnect(): Promise<DisconnectProviderResult>
}
