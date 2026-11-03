import type { Listing, SavedSearch } from '../types'
import { formatRelativeTime } from '../lib/format'
import { SectionLabel } from './SectionLabel'

type Props = {
  listings: Listing[]
  searches: SavedSearch[]
  limit?: number
}

export function RecentListings({ listings, searches, limit = 6 }: Props) {
  const searchNameById = new Map(searches.map((s) => [s.id, s.name]))

  const recent = [...listings]
    .sort(
      (a, b) => new Date(b.seenAt).getTime() - new Date(a.seenAt).getTime(),
    )
    .slice(0, limit)

  if (recent.length === 0) return null

  return (
    <section className="space-y-2">
      <SectionLabel>Recently found</SectionLabel>
      <ul className="-mx-4 flex gap-3 overflow-x-auto px-4 pb-1 [-ms-overflow-style:none] [scrollbar-width:none] sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:px-0 sm:pb-0 [&::-webkit-scrollbar]:hidden">
        {recent.map((listing) => {
          const watchName = listing.savedSearchId
            ? searchNameById.get(listing.savedSearchId)
            : null

          return (
            <li
              key={listing.id}
              className="w-[72%] shrink-0 sm:w-auto sm:shrink"
            >
              <a
                href={listing.listingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="block overflow-hidden rounded-2xl border border-stone-200/70 bg-white active:bg-stone-50"
              >
                <div className="aspect-[4/3] bg-stone-100">
                  {listing.imageUrl ? (
                    <img
                      src={listing.imageUrl}
                      alt=""
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-sm text-stone-400">
                      No photo
                    </div>
                  )}
                </div>
                <div className="space-y-0.5 p-3">
                  <p className="text-[15px] font-semibold text-stone-900">
                    {listing.price ?? '—'}
                  </p>
                  <p className="line-clamp-2 text-sm text-stone-600">
                    {listing.title ?? 'Untitled'}
                  </p>
                  <p className="text-xs text-stone-400">
                    {watchName ? `${watchName} · ` : ''}
                    {formatRelativeTime(listing.seenAt)}
                  </p>
                </div>
              </a>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
