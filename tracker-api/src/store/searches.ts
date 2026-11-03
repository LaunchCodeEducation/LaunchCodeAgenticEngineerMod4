import { prisma } from '../lib/prisma'
import { CreateSearchInput, Search, UpdateSearchInput } from '../types/search'

export async function getAllSearches(): Promise<Search[]> {
  return prisma.savedSearch.findMany({
    orderBy: { createdAt: 'desc' },
  })
}

export async function getSearchById(id: string): Promise<Search | null> {
  return prisma.savedSearch.findUnique({
    where: { id },
  })
}

const ALLOWED_RESULTS_PER_SEARCH = [5, 10, 20, 50]

export async function createSearch(input: CreateSearchInput): Promise<Search> {
  const resultsPerSearch = input.resultsPerSearch ?? 10

  if (!ALLOWED_RESULTS_PER_SEARCH.includes(resultsPerSearch)) {
    throw new Error('Invalid resultsPerSearch')
  }

  if (
    input.maxPrice !== undefined &&
    input.maxPrice !== null &&
    (typeof input.maxPrice !== 'number' || input.maxPrice <= 0)
  ) {
    throw new Error('Invalid maxPrice')
  }

  return prisma.savedSearch.create({
    data: {
      name: input.name,
      query: input.query,
      maxPrice: input.maxPrice ?? null,
      location: input.location,
      radius: input.radius,
      resultsPerSearch,
    },
  })
}

export async function updateSearch(
  id: string,
  input: UpdateSearchInput,
): Promise<Search | null> {
  const existing = await getSearchById(id)
  if (!existing) return null

  if (
    input.resultsPerSearch !== undefined &&
    !ALLOWED_RESULTS_PER_SEARCH.includes(input.resultsPerSearch)
  ) {
    throw new Error('Invalid resultsPerSearch')
  }

  if (
    input.maxPrice !== undefined &&
    input.maxPrice !== null &&
    (typeof input.maxPrice !== 'number' || input.maxPrice <= 0)
  ) {
    throw new Error('Invalid maxPrice')
  }

  return prisma.savedSearch.update({
    where: { id },
    data: {
      ...(input.name !== undefined && { name: input.name.trim() }),
      ...(input.query !== undefined && { query: input.query.trim() }),
      ...(input.location !== undefined && { location: input.location.trim() }),
      ...(input.radius !== undefined && { radius: input.radius }),
      ...(input.maxPrice !== undefined && { maxPrice: input.maxPrice }),
      ...(input.resultsPerSearch !== undefined && {
        resultsPerSearch: input.resultsPerSearch,
      }),
    },
  })
}

export async function updateSearchAfterRun(
  id: string,
  stats: {
    newListings: number
    totalScraped: number
    skippedDuplicates: number
    newListingIds: string[]
  },
): Promise<void> {
  await prisma.savedSearch.update({
    where: { id },
    data: {
      lastCheckedAt: new Date(),
      lastNewListings: stats.newListings,
      lastTotalScraped: stats.totalScraped,
      lastSkippedDuplicates: stats.skippedDuplicates,
      lastRunNewListingIds: stats.newListingIds,
    },
  })
}

export async function deleteSearch(id: string): Promise<boolean> {
  const result = await prisma.savedSearch.deleteMany({
    where: { id },
  })

  return result.count > 0
}
