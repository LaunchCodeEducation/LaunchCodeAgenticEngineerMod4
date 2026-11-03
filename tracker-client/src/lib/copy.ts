export const HELPERS = {
  newListingsOnly: 'Only listings new since your last check.',
  notFacebook: 'Opens on Facebook. Scout only monitors.',
} as const

export const CHECK_PROGRESS_MESSAGES = [
  'Checking Facebook Marketplace…',
  'Looking for new listings…',
  'Comparing against previous results…',
] as const

export function getHomeStatus(watchesWithNew: number): string {
  if (watchesWithNew > 0) {
    return watchesWithNew === 1
      ? '1 search has new listings.'
      : `${watchesWithNew} searches have new listings.`
  }

  return "Everything you're watching is up to date."
}

export function getWatchStatusLabel(
  count: number,
  isChecking: boolean,
): string {
  if (isChecking) return 'Checking Facebook Marketplace…'
  if (count > 0) {
    return count === 1 ? '1 new listing' : `${count} new listings`
  }
  return 'No new listings'
}

export function getCompactWatchStatus(
  count: number,
  isChecking: boolean,
): string {
  if (isChecking) return 'Checking…'
  if (count > 0) return `${count} new`
  return 'Up to date'
}

export function getWorkspaceResultSummary(newCount: number): string {
  if (newCount === 0) return 'No new listings since your last check.'
  return newCount === 1
    ? '1 new listing since your last check'
    : `${newCount} new listings since your last check`
}

export function getCheckCompleteMessage(newCount: number): string {
  if (newCount === 0) return 'No new listings.'
  return newCount === 1
    ? 'Found 1 new listing.'
    : `Found ${newCount} new listings.`
}
