import { useMemo } from 'react'
import type { SavedSearch } from '../types'
import { buildRecentActivity, formatActivityTime } from '../lib/activity'
import { SectionLabel } from './SectionLabel'

type Props = {
  searches: SavedSearch[]
}

export function RecentActivity({ searches }: Props) {
  const events = useMemo(() => buildRecentActivity(searches), [searches])

  if (events.length === 0) return null

  return (
    <section className="space-y-2">
      <SectionLabel>Activity</SectionLabel>
      <ul className="overflow-hidden rounded-2xl border border-stone-200/70 bg-white">
        {events.map((event, index) => (
          <li
            key={event.id}
            className={`flex min-h-12 items-baseline justify-between gap-3 px-4 py-3 text-sm ${
              index > 0 ? 'border-t border-stone-100' : ''
            }`}
          >
            <span className="min-w-0 text-stone-700">{event.message}</span>
            <span className="shrink-0 text-stone-400">
              {formatActivityTime(event.timestamp)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
