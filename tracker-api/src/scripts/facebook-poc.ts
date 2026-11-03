import * as readline from 'readline'
import { prisma } from '../lib/prisma'
import { saveNewListings } from '../store/listings'
import {
  buildMarketplaceSearchUrl,
  detectLoginRequired,
  scrapeMarketplaceSearch,
} from '../services/facebook-scraper'

const POC_SEARCH = {
  query: 'gsxr 1000',
  location: 'philly',
  radius: 65,
  maxPrice: 6500,
}

function waitForEnter(message: string): Promise<void> {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    })

    rl.question(message, () => {
      rl.close()
      resolve()
    })
  })
}

function printListings(
  listings: Awaited<ReturnType<typeof scrapeMarketplaceSearch>>,
) {
  listings.forEach((listing, index) => {
    console.log(`--- Result ${index + 1} ---`)
    console.log(`Title:    ${listing.title ?? '(not found)'}`)
    console.log(`Price:    ${listing.price ?? '(not found)'}`)
    console.log(`Location: ${listing.location ?? '(not found)'}`)
    console.log(`Image:    ${listing.imageUrl ?? '(not found)'}`)
    console.log(`URL:      ${listing.listingUrl}`)
    console.log()
  })
}

async function main() {
  console.log('Launching Chromium (visible window)...')
  console.log('This is a disposable feasibility test, not a production scraper.\n')
  console.log(`Search URL: ${buildMarketplaceSearchUrl(POC_SEARCH)}\n`)

  const listings = await scrapeMarketplaceSearch(POC_SEARCH, {
    headless: false,
    onPageReady: async (page) => {
      console.log(`Page title: ${await page.title()}\n`)

      if (await detectLoginRequired(page)) {
        console.log('Login appears to be required.')
        console.log('Use the browser window to log in manually if prompted.')
        console.log('This script will not try to bypass login, CAPTCHA, or other security checks.\n')
        await waitForEnter('Press Enter after you are logged in and listings are visible... ')
      } else {
        console.log('Waiting up to 30 seconds for listings to appear...')
      }
    },
  })

  if (listings.length === 0) {
    console.log('No listing links found.')
    return
  }

  console.log(`Collected ${listings.length} listing(s):\n`)
  printListings(listings)

  console.log('Saving new listings to PostgreSQL...')
  const { saved, skipped } = await saveNewListings(listings)
  console.log(`Saved ${saved} new listing(s), skipped ${skipped} duplicate(s).`)
}

main()
  .catch((error) => {
    console.error('Script failed:', error)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
