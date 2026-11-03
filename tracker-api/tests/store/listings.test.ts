import { beforeEach, describe, expect, it, vi } from 'vitest'

const mockPrisma = vi.hoisted(() => ({
  listing: {
    create: vi.fn(),
    findUnique: vi.fn(),
    update: vi.fn(),
  },
  priceObservation: {
    create: vi.fn(),
  },
  $transaction: vi.fn((operations: unknown[]) => Promise.all(operations)),
}))

vi.mock('../../src/lib/prisma', () => ({
  prisma: mockPrisma,
}))

import { saveNewListings } from '../../src/store/listings'
import type { ListingInput } from '../../src/store/listings'

// Prisma throws this shape for a unique-constraint violation, which is how
// saveNewListings detects that a scraped listing already exists (see
// src/store/listings.ts). Rescans of an already-seen listing always hit this
// path, since listingUrl is unique.
const duplicateListingError = { code: 'P2002' }

const rescannedListing: ListingInput = {
  source: 'facebook',
  listingUrl: 'https://facebook.com/marketplace/item/123',
  title: 'Test item',
  price: '$100',
  location: 'Philadelphia, PA',
  imageUrl: null,
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('saveNewListings price-change behavior on rescan', () => {
  it('does not create a PriceObservation when the rescanned price is unchanged', async () => {
    mockPrisma.listing.create.mockRejectedValueOnce(duplicateListingError)
    mockPrisma.listing.findUnique.mockResolvedValueOnce({
      id: 'listing-1',
      price: rescannedListing.price,
    })

    const result = await saveNewListings([rescannedListing])

    expect(result).toEqual({ saved: 0, skipped: 1, newListingIds: [] })
    expect(mockPrisma.listing.update).not.toHaveBeenCalled()
    expect(mockPrisma.priceObservation.create).not.toHaveBeenCalled()
  })

  it('updates Listing.price and creates a PriceObservation when the rescanned price changed', async () => {
    mockPrisma.listing.create.mockRejectedValueOnce(duplicateListingError)
    mockPrisma.listing.findUnique.mockResolvedValueOnce({
      id: 'listing-1',
      price: '$90',
    })

    const result = await saveNewListings([rescannedListing])

    expect(result).toEqual({ saved: 0, skipped: 1, newListingIds: [] })
    expect(mockPrisma.listing.update).toHaveBeenCalledWith({
      where: { id: 'listing-1' },
      data: { price: '$100' },
    })
    expect(mockPrisma.priceObservation.create).toHaveBeenCalledWith({
      data: { listingId: 'listing-1', price: '$100' },
    })
    expect(mockPrisma.$transaction).toHaveBeenCalledTimes(1)
  })

  it('does not look up or record a price change when the rescanned listing has no usable price', async () => {
    mockPrisma.listing.create.mockRejectedValueOnce(duplicateListingError)

    const result = await saveNewListings([{ ...rescannedListing, price: null }])

    expect(result).toEqual({ saved: 0, skipped: 1, newListingIds: [] })
    expect(mockPrisma.listing.findUnique).not.toHaveBeenCalled()
    expect(mockPrisma.listing.update).not.toHaveBeenCalled()
    expect(mockPrisma.priceObservation.create).not.toHaveBeenCalled()
  })
})
