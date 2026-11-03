import { beforeEach, describe, expect, it, vi } from 'vitest'

const mockPrisma = vi.hoisted(() => ({
  savedSearch: {
    create: vi.fn(),
    update: vi.fn(),
    findUnique: vi.fn(),
  },
}))

vi.mock('../../src/lib/prisma', () => ({
  prisma: mockPrisma,
}))

import { createSearch, updateSearch } from '../../src/store/searches'
import type { CreateSearchInput, UpdateSearchInput } from '../../src/types/search'

const baseCreateInput: CreateSearchInput = {
  name: 'Test search',
  query: 'bike',
  location: 'Philadelphia, PA',
  radius: 10,
}

const existingSearch = {
  id: 'search-1',
  name: 'Test search',
  query: 'bike',
  maxPrice: null,
  location: 'Philadelphia, PA',
  radius: 10,
  resultsPerSearch: 10,
  isActive: true,
  lastCheckedAt: null,
  lastNewListings: 0,
  lastTotalScraped: 0,
  lastSkippedDuplicates: 0,
  lastRunNewListingIds: [],
  createdAt: new Date(),
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('createSearch maxPrice validation', () => {
  it('throws for a negative maxPrice', async () => {
    await expect(
      createSearch({ ...baseCreateInput, maxPrice: -1 }),
    ).rejects.toThrow('Invalid maxPrice')

    expect(mockPrisma.savedSearch.create).not.toHaveBeenCalled()
  })

  it('throws for a maxPrice of 0', async () => {
    await expect(
      createSearch({ ...baseCreateInput, maxPrice: 0 }),
    ).rejects.toThrow('Invalid maxPrice')

    expect(mockPrisma.savedSearch.create).not.toHaveBeenCalled()
  })

  it('succeeds for a positive maxPrice and passes it through to prisma', async () => {
    mockPrisma.savedSearch.create.mockResolvedValueOnce({
      ...existingSearch,
      maxPrice: 100,
    })

    await createSearch({ ...baseCreateInput, maxPrice: 100 })

    expect(mockPrisma.savedSearch.create).toHaveBeenCalledWith({
      data: expect.objectContaining({ maxPrice: 100 }),
    })
  })

  it('succeeds when maxPrice is null', async () => {
    mockPrisma.savedSearch.create.mockResolvedValueOnce(existingSearch)

    await createSearch({ ...baseCreateInput, maxPrice: null })

    expect(mockPrisma.savedSearch.create).toHaveBeenCalledWith({
      data: expect.objectContaining({ maxPrice: null }),
    })
  })

  it('succeeds when maxPrice is omitted', async () => {
    mockPrisma.savedSearch.create.mockResolvedValueOnce(existingSearch)

    await createSearch({ ...baseCreateInput })

    expect(mockPrisma.savedSearch.create).toHaveBeenCalledWith({
      data: expect.objectContaining({ maxPrice: null }),
    })
  })

  it('throws for an invalid resultsPerSearch', async () => {
    await expect(
      createSearch({ ...baseCreateInput, resultsPerSearch: 7 }),
    ).rejects.toThrow('Invalid resultsPerSearch')

    expect(mockPrisma.savedSearch.create).not.toHaveBeenCalled()
  })
})

describe('updateSearch maxPrice validation', () => {
  beforeEach(() => {
    mockPrisma.savedSearch.findUnique.mockResolvedValue(existingSearch)
  })

  it('throws for a negative maxPrice', async () => {
    await expect(
      updateSearch('search-1', { maxPrice: -1 } as UpdateSearchInput),
    ).rejects.toThrow('Invalid maxPrice')

    expect(mockPrisma.savedSearch.update).not.toHaveBeenCalled()
  })

  it('throws for a maxPrice of 0', async () => {
    await expect(
      updateSearch('search-1', { maxPrice: 0 } as UpdateSearchInput),
    ).rejects.toThrow('Invalid maxPrice')

    expect(mockPrisma.savedSearch.update).not.toHaveBeenCalled()
  })

  it('succeeds for a positive maxPrice and passes it through to prisma', async () => {
    mockPrisma.savedSearch.update.mockResolvedValueOnce({
      ...existingSearch,
      maxPrice: 250,
    })

    await updateSearch('search-1', { maxPrice: 250 })

    expect(mockPrisma.savedSearch.update).toHaveBeenCalledWith({
      where: { id: 'search-1' },
      data: { maxPrice: 250 },
    })
  })

  it('succeeds when maxPrice is null', async () => {
    mockPrisma.savedSearch.update.mockResolvedValueOnce(existingSearch)

    await updateSearch('search-1', { maxPrice: null })

    expect(mockPrisma.savedSearch.update).toHaveBeenCalledWith({
      where: { id: 'search-1' },
      data: { maxPrice: null },
    })
  })

  it('succeeds when maxPrice is omitted, leaving it untouched', async () => {
    mockPrisma.savedSearch.update.mockResolvedValueOnce(existingSearch)

    await updateSearch('search-1', { name: 'Renamed search' })

    expect(mockPrisma.savedSearch.update).toHaveBeenCalledWith({
      where: { id: 'search-1' },
      data: { name: 'Renamed search' },
    })

    const callArgs = mockPrisma.savedSearch.update.mock.calls[0][0]
    expect(callArgs.data).not.toHaveProperty('maxPrice')
  })

  it('throws for an invalid resultsPerSearch', async () => {
    await expect(
      updateSearch('search-1', { resultsPerSearch: 7 } as UpdateSearchInput),
    ).rejects.toThrow('Invalid resultsPerSearch')

    expect(mockPrisma.savedSearch.update).not.toHaveBeenCalled()
  })
})
