import type { ListingStatus } from '../types'

const LAST_VISIT_KEY = 'marketplace-tracker:last-visit'
const LISTING_STATUS_KEY = 'marketplace-tracker:listing-status'

type StatusMap = Record<string, ListingStatus>

function readStatusMap(): StatusMap {
  try {
    const raw = localStorage.getItem(LISTING_STATUS_KEY)
    return raw ? (JSON.parse(raw) as StatusMap) : {}
  } catch {
    return {}
  }
}

function writeStatusMap(map: StatusMap) {
  localStorage.setItem(LISTING_STATUS_KEY, JSON.stringify(map))
}

export function getLastVisit(): string | null {
  return localStorage.getItem(LAST_VISIT_KEY)
}

export function recordVisit() {
  localStorage.setItem(LAST_VISIT_KEY, new Date().toISOString())
}

export function getListingStatus(
  listingId: string,
  isNewFromSearch: boolean,
): ListingStatus {
  const stored = readStatusMap()[listingId]
  if (stored) return stored
  return isNewFromSearch ? 'new' : 'reviewed'
}

export function setListingStatus(listingId: string, status: ListingStatus) {
  const map = readStatusMap()
  map[listingId] = status
  writeStatusMap(map)
}

export function markListingReviewed(listingId: string) {
  setListingStatus(listingId, 'reviewed')
}

export function markListingArchived(listingId: string) {
  setListingStatus(listingId, 'archived')
}
