import { useMemo } from 'react'
import type { Listing, ListingStatus, SavedSearch } from '../types'
import { getListingStatus } from '../lib/storage'

export function getNewListingIdsForSearch(search: SavedSearch): Set<string> {
  return new Set(search.lastRunNewListingIds)
}

export function countAttentionListings(
  listings: Listing[],
  search: SavedSearch,
  statusVersion: number,
): number {
  void statusVersion

  const newIds = getNewListingIdsForSearch(search)

  return listings.filter((listing) => {
    if (listing.savedSearchId !== search.id) return false
    const status = getListingStatus(listing.id, newIds.has(listing.id))
    return status === 'new'
  }).length
}

export function partitionListingsForSearch(
  listings: Listing[],
  search: SavedSearch,
  statusVersion: number,
): Record<ListingStatus, Listing[]> {
  void statusVersion

  const newIds = getNewListingIdsForSearch(search)
  const forSearch = listings.filter((l) => l.savedSearchId === search.id)

  const buckets: Record<ListingStatus, Listing[]> = {
    new: [],
    reviewed: [],
    archived: [],
  }

  for (const listing of forSearch) {
    const status = getListingStatus(listing.id, newIds.has(listing.id))
    if (status === 'new') buckets.new.push(listing)
    else if (status === 'reviewed') buckets.reviewed.push(listing)
    else buckets.archived.push(listing)
  }

  return buckets
}

export function useAttentionCounts(
  searches: SavedSearch[],
  listings: Listing[],
  statusVersion: number,
) {
  return useMemo(() => {
    const perSearch = searches.map((search) => ({
      search,
      count: countAttentionListings(listings, search, statusVersion),
    }))

    const total = perSearch.reduce((sum, item) => sum + item.count, 0)
    const withNew = perSearch.filter((item) => item.count > 0).length

    return { perSearch, total, withNew }
  }, [searches, listings, statusVersion])
}
