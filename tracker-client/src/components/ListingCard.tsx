import type { Listing } from '../types'

type Props = {
  listing: Listing
}

export function ListingCard({ listing }: Props) {
  return (
    <article className="overflow-hidden rounded-lg bg-white shadow-sm shadow-stone-900/5">
      <div className="aspect-4/3 bg-stone-100">
        {listing.imageUrl ? (
          <img
            src={listing.imageUrl}
            alt={listing.title ?? 'Listing'}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-stone-400">
            No photo
          </div>
        )}
      </div>

      <div className="p-4">
        <p className="text-lg font-semibold text-stone-900">
          {listing.price ?? 'Price unavailable'}
        </p>
        <h3 className="mt-1 line-clamp-2 text-sm text-stone-700">
          {listing.title ?? 'Untitled listing'}
        </h3>
        <p className="mt-2 text-sm text-stone-500">
          {listing.location ?? 'Location unavailable'}
        </p>
        <a
          href={listing.listingUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-block text-sm font-medium text-stone-900 underline decoration-stone-300 underline-offset-4 hover:decoration-stone-500"
        >
          Open on Facebook
        </a>
      </div>
    </article>
  )
}
