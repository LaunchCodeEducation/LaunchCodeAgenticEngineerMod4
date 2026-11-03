export type Search = {
  id: string
  name: string
  query: string
  maxPrice: number | null
  location: string
  radius: number
  resultsPerSearch: number
  isActive: boolean
  lastCheckedAt: Date | null
  lastNewListings: number
  lastTotalScraped: number
  lastSkippedDuplicates: number
  lastRunNewListingIds: string[]
  createdAt: Date
}

export type CreateSearchInput = {
  name: string
  query: string
  maxPrice?: number | null
  location: string
  radius: number
  resultsPerSearch?: number
}

export type UpdateSearchInput = {
  name?: string
  query?: string
  maxPrice?: number | null
  location?: string
  radius?: number
  resultsPerSearch?: number
}
