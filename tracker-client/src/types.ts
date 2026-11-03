export type SavedSearch = {
  id: string
  name: string
  query: string
  maxPrice: number | null
  location: string
  radius: number
  resultsPerSearch: number
  isActive: boolean
  lastCheckedAt: string | null
  lastNewListings: number
  lastTotalScraped: number
  lastSkippedDuplicates: number
  lastRunNewListingIds: string[]
  createdAt: string
}

export type Listing = {
  id: string
  source: string
  listingUrl: string
  title: string | null
  price: string | null
  location: string | null
  imageUrl: string | null
  savedSearchId: string | null
  seenAt: string
}

export type ListingStatus = 'new' | 'reviewed' | 'archived'

export type RunSearchResult = {
  searchId: string
  searchName: string
  scannedAt: string
  totalScraped: number
  newListings: number
  skippedDuplicates: number
  newListingIds: string[]
}

export type NewSearchForm = {
  name: string
  query: string
  maxPrice: string
  location: string
  radius: string
  resultsPerSearch: string
}

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

export type ConnectProviderResult = {
  providerId: ProviderId
  connection: ProviderConnection
  action: {
    mode: 'external_script' | 'not_implemented'
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
