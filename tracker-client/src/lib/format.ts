export function formatMaxPrice(maxPrice: number): string {
  return `$${maxPrice.toLocaleString()}`
}

export function formatRelativeTime(value: string | null): string {
  if (!value) return "hasn't been checked yet"

  const diffMs = Date.now() - new Date(value).getTime()
  const minutes = Math.floor(diffMs / 60000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`

  const days = Math.floor(hours / 24)
  return `${days} day${days === 1 ? '' : 's'} ago`
}

export function formatCheckedAt(value: string | null): string {
  if (!value) return "Hasn't been checked yet"
  return `Checked ${formatRelativeTime(value)}`
}

export function formatWatchLocationLines(search: {
  location: string
  radius: number
  maxPrice: number | null
}): string[] {
  const lines = [search.location, `${search.radius} miles`]
  if (search.maxPrice) lines.push(`Under ${formatMaxPrice(search.maxPrice)}`)
  return lines
}

export function formatSeenDate(seenAt: string): string {
  return new Date(seenAt).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function formatWatchDetails(search: {
  location: string
  radius: number
  maxPrice: number | null
}): string {
  const parts = [search.location, `Within ${search.radius} miles`]
  if (search.maxPrice) parts.push(`Under ${formatMaxPrice(search.maxPrice)}`)
  return parts.join(' · ')
}

export function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export function getLatestCheckedAt(
  searches: { lastCheckedAt: string | null }[],
): string | null {
  const times = searches
    .map((s) => s.lastCheckedAt)
    .filter((t): t is string => Boolean(t))

  if (times.length === 0) return null

  return times.reduce((latest, current) =>
    new Date(current) > new Date(latest) ? current : latest,
  )
}
