import { prisma } from '../lib/prisma'
import { Listing } from '../types/listing'

export type ListingInput = {
  source: string
  listingUrl: string
  title: string | null
  price: string | null
  location: string | null
  imageUrl: string | null
}

export async function getAllListings(): Promise<Listing[]> {
  return prisma.listing.findMany({
    orderBy: { seenAt: 'desc' },
  })
}

export async function saveNewListings(
  listings: ListingInput[],
  savedSearchId?: string,
): Promise<{ saved: number; skipped: number; newListingIds: string[] }> {
  const newListingIds: string[] = []
  let saved = 0
  let skipped = 0

  for (const listing of listings) {
    try {
      const created = await prisma.listing.create({
        data: {
          ...listing,
          savedSearchId: savedSearchId ?? null,
          priceObservations: listing.price
            ? { create: { price: listing.price } }
            : undefined,
        },
      })
      newListingIds.push(created.id)
      saved++
    } catch (error) {
      if (
        typeof error === 'object' &&
        error !== null &&
        'code' in error &&
        error.code === 'P2002'
      ) {
        skipped++
        await recordPriceChangeIfAny(listing)
      } else {
        throw error
      }
    }
  }

  return { saved, skipped, newListingIds }
}

// A re-scraped listing (matched by listingUrl) never overwrites history: the
// existing PriceObservation rows stay untouched, and a rescan only appends a
// new one when the price actually differs from the last-known price.
async function recordPriceChangeIfAny(listing: ListingInput): Promise<void> {
  if (!listing.price) {
    return
  }

  const existing = await prisma.listing.findUnique({
    where: { listingUrl: listing.listingUrl },
  })

  if (!existing || existing.price === listing.price) {
    return
  }

  await prisma.$transaction([
    prisma.listing.update({
      where: { id: existing.id },
      data: { price: listing.price },
    }),
    prisma.priceObservation.create({
      data: { listingId: existing.id, price: listing.price },
    }),
  ])
}
