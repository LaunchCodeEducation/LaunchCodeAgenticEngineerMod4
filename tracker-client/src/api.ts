import type {
  ConnectProviderResult,
  DisconnectProviderResult,
  ProviderConnection,
  ProviderId,
  RunSearchResult,
  SavedSearch,
} from './types'

export const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3000'

export async function fetchSearches(): Promise<SavedSearch[]> {
  const response = await fetch(`${API_BASE}/searches`)
  if (!response.ok) throw new Error('Failed to load searches')
  return response.json()
}

export async function fetchListings() {
  const response = await fetch(`${API_BASE}/listings`)
  if (!response.ok) throw new Error('Failed to load listings')
  return response.json()
}

export async function createSearch(body: object): Promise<SavedSearch> {
  const response = await fetch(`${API_BASE}/searches`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error('Failed to save search')
  return response.json()
}

export async function deleteSearch(id: string) {
  const response = await fetch(`${API_BASE}/searches/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error('Failed to delete search')
}

export async function updateSearch(
  id: string,
  body: object,
): Promise<SavedSearch> {
  const response = await fetch(`${API_BASE}/searches/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error('Failed to update search')
  return response.json()
}

export async function runSearch(id: string): Promise<RunSearchResult> {
  const response = await fetch(`${API_BASE}/searches/${id}/run`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Failed to check search')
  return response.json()
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`)
  const data = await response.json()
  return data.status === 'ok'
}

export async function fetchConnections(): Promise<ProviderConnection[]> {
  const response = await fetch(`${API_BASE}/connections`)
  if (!response.ok) throw new Error('Failed to load connections')
  const data = (await response.json()) as { connections: ProviderConnection[] }
  return data.connections
}

export async function fetchConnection(
  providerId: ProviderId,
): Promise<ProviderConnection> {
  const response = await fetch(`${API_BASE}/connections/${providerId}`)
  if (!response.ok) throw new Error('Failed to load connection status')
  return response.json()
}

export async function connectProvider(
  providerId: ProviderId,
): Promise<ConnectProviderResult> {
  const response = await fetch(`${API_BASE}/connections/${providerId}/connect`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Failed to start connection')
  return response.json()
}

export async function reconnectProvider(
  providerId: ProviderId,
): Promise<ConnectProviderResult> {
  const response = await fetch(
    `${API_BASE}/connections/${providerId}/reconnect`,
    { method: 'POST' },
  )
  if (!response.ok) throw new Error('Failed to start reconnection')
  return response.json()
}

export async function disconnectProvider(
  providerId: ProviderId,
): Promise<DisconnectProviderResult> {
  const response = await fetch(`${API_BASE}/connections/${providerId}`, {
    method: 'DELETE',
  })
  const data = (await response.json()) as DisconnectProviderResult
  if (!response.ok && response.status !== 501) {
    throw new Error(data.message || 'Failed to disconnect')
  }
  return data
}
