import { Link } from 'react-router-dom'
import type { SavedSearch } from '../types'
import { getCompactWatchStatus } from '../lib/copy'
import { SectionLabel } from './SectionLabel'
import { WatchRowMenu } from './WatchRowMenu'

export type WatchingItem = {
  search: SavedSearch
  count: number
}

type Props = {
  items: WatchingItem[]
  runningId: string | null
  lastCheckedLabel?: string | null
}

export function WatchingList({ items, runningId, lastCheckedLabel }: Props) {
  if (items.length === 0) return null

  return (
    <section className="space-y-2">
      <SectionLabel
        action={
          lastCheckedLabel ? (
            <span className="text-[13px] text-stone-400">{lastCheckedLabel}</span>
          ) : null
        }
      >
        Watching
      </SectionLabel>
      <ul className="overflow-hidden rounded-2xl border border-stone-200/70 bg-white">
        {items.map(({ search, count }, index) => {
          const isActive = count > 0
          const isChecking = runningId === search.id

          return (
            <li
              key={search.id}
              className={`flex items-center gap-1 ${
                index > 0 ? 'border-t border-stone-100' : ''
              }`}
            >
              <Link
                to={`/search/${search.id}`}
                className={`flex min-h-14 min-w-0 flex-1 items-center justify-between gap-3 px-4 py-3 active:bg-stone-50 ${
                  isActive ? '' : 'opacity-55'
                }`}
              >
                <span className="truncate text-[15px] font-medium text-stone-900">
                  {search.name}
                </span>
                <span
                  className={`shrink-0 text-sm ${
                    isActive
                      ? 'font-medium text-emerald-700'
                      : 'text-stone-400'
                  }`}
                >
                  {getCompactWatchStatus(count, isChecking)}
                </span>
              </Link>
              <div className="pr-2">
                <WatchRowMenu search={search} />
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
