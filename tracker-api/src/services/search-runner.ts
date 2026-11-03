import { saveNewListings } from '../store/listings'
import { getSearchById, updateSearchAfterRun } from '../store/searches'
import { scrapeMarketplaceSearch } from './facebook-scraper'

// TODO: Add automatic scheduled searches so watches run on a timer.

export type RunSearchResult = {
  searchId: string
  searchName: string
  scannedAt: string
  totalScraped: number
  newListings: number
  skippedDuplicates: number
  newListingIds: string[]
}

export class RunSearchError extends Error {
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options)
    this.name = 'RunSearchError'
  }
}

export async function runSavedSearch(
  searchId: string,
): Promise<RunSearchResult | null> {
  const search = await getSearchById(searchId)

  if (!search) {
    return null
  }

  try {
    const listings = await scrapeMarketplaceSearch(
      {
        query: search.query || search.name,
        location: search.location,
        radius: search.radius,
        maxPrice: search.maxPrice,
      },
      {
        headless: process.env.MARKETPLACE_HEADLESS !== 'false',
        maxListings: search.resultsPerSearch,
      },
    )

    const { saved, skipped, newListingIds } = await saveNewListings(
      listings,
      search.id,
    )

    await updateSearchAfterRun(search.id, {
      newListings: saved,
      totalScraped: listings.length,
      skippedDuplicates: skipped,
      newListingIds,
    })

    return {
      searchId: search.id,
      searchName: search.name,
      scannedAt: new Date().toISOString(),
      totalScraped: listings.length,
      newListings: saved,
      skippedDuplicates: skipped,
      newListingIds,
    }
  } catch (error) {
    throw new RunSearchError(
      `Failed to run saved search "${search.name}" (${search.id})`,
      { cause: error },
    )
  }
}
