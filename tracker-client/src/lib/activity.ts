import type { SavedSearch } from '../types'
import { formatRelativeTime } from './format'

export type ActivityEvent = {
  id: string
  message: string
  timestamp: string
}

export function buildRecentActivity(searches: SavedSearch[]): ActivityEvent[] {
  const events: ActivityEvent[] = []

  for (const search of searches) {
    events.push({
      id: `${search.id}-added`,
      message: `Added ${search.name}`,
      timestamp: search.createdAt,
    })

    if (search.lastCheckedAt) {
      events.push({
        id: `${search.id}-checked`,
        message: `Checked ${search.name}`,
        timestamp: search.lastCheckedAt,
      })

      if (search.lastNewListings > 0) {
        events.push({
          id: `${search.id}-found`,
          message:
            search.lastNewListings === 1
              ? `1 new listing · ${search.name}`
              : `${search.lastNewListings} new listings · ${search.name}`,
          timestamp: search.lastCheckedAt,
        })
      }
    }
  }

  return events
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    )
    .slice(0, 6)
}

export function formatActivityTime(timestamp: string): string {
  return formatRelativeTime(timestamp)
}
