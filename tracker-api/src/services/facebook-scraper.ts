import * as fs from 'fs'
import * as path from 'path'
import { chromium, type Page } from 'playwright'
import { ListingInput } from '../store/listings'

export const FACEBOOK_MARKETPLACE_SOURCE = 'facebook-marketplace'

const FACEBOOK_STORAGE_STATE_PATH = path.join(
  process.cwd(),
  'storage',
  'facebook-state.json',
)

export type ScrapeOptions = {
  headless?: boolean
  maxListings?: number
  listingWaitTimeoutMs?: number
  onPageReady?: (page: Page) => Promise<void>
}

export class ScraperError extends Error {
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options)
    this.name = 'ScraperError'
  }
}

export type MarketplaceSearchParams = {
  query: string
  location: string
  radius: number
  maxPrice?: number | null
}

export function buildMarketplaceSearchUrl(
  params: MarketplaceSearchParams,
): string {
  const locationSlug = params.location.toLowerCase().replace(/\s+/g, '')
  const searchParams = new URLSearchParams({
    query: params.query,
    exact: 'false',
    radius: String(params.radius),
  })

  if (params.maxPrice) {
    searchParams.set('maxPrice', String(params.maxPrice))
  }

  return `https://www.facebook.com/marketplace/${locationSlug}/search/?${searchParams.toString()}`
}

// TODO: Validate that scraped listing locations fall within the requested radius.

function parseListingText(text: string): {
  title: string | null
  price: string | null
  location: string | null
} {
  const lines = text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  const price = lines.find((line) => /^\$[\d,]+/.test(line)) ?? null
  const title =
    lines.find(
      (line) =>
        line !== price &&
        !line.match(/^(Free|Just listed|Yesterday|Today|\d+ miles?)$/i) &&
        !line.includes(','),
    ) ??
    lines[0] ??
    null
  const location =
    lines.find(
      (line) =>
        line !== price &&
        line !== title &&
        (line.includes(',') || /\d+\s*miles?\b/i.test(line)),
    ) ?? null

  return { title, price, location }
}

async function detectLoginRequired(page: Page): Promise<boolean> {
  const url = page.url()

  if (url.includes('/login') || url.includes('checkpoint')) {
    return true
  }

  const emailField = page.locator('input[name="email"]')
  const passwordField = page.locator('input[name="pass"]')

  const hasEmail = await emailField.first().isVisible().catch(() => false)
  const hasPassword = await passwordField.first().isVisible().catch(() => false)

  return hasEmail && hasPassword
}

async function pageTextIncludes(page: Page, needle: string): Promise<boolean> {
  const lower = needle.toLowerCase()
  const content = await page.content().catch(() => '')
  if (content.toLowerCase().includes(lower)) {
    return true
  }
  const bodyText = await page.locator('body').innerText().catch(() => '')
  return bodyText.toLowerCase().includes(lower)
}

async function detectCaptcha(page: Page): Promise<boolean> {
  const url = page.url().toLowerCase()
  if (url.includes('captcha') || url.includes('/checkpoint/')) {
    return true
  }

  const captchaSelectors = [
    'iframe[src*="captcha"]',
    'iframe[src*="recaptcha"]',
    '[id*="captcha" i]',
    '[class*="captcha" i]',
    '#captcha',
  ]

  for (const selector of captchaSelectors) {
    const visible = await page
      .locator(selector)
      .first()
      .isVisible()
      .catch(() => false)
    if (visible) return true
  }

  return (
    (await pageTextIncludes(page, 'security check')) ||
    (await pageTextIncludes(page, 'confirm you')) ||
    (await pageTextIncludes(page, 'captcha'))
  )
}

export type EmptyScrapeDiagnostics = {
  capturedAt: string
  query: string
  location: string
  initialUrl: string
  finalUrl: string
  pageTitle: string
  loginFieldsExist: boolean
  captchaExists: boolean
  marketplaceUnavailable: boolean
  somethingWentWrong: boolean
  listingAnchorCount: number
  screenshotPath: string
  htmlPath: string
  metaPath: string
}

const EMPTY_SCRAPE_DIR = path.join(process.cwd(), 'storage')
const EMPTY_SCREENSHOT_PATH = path.join(EMPTY_SCRAPE_DIR, 'marketplace-empty.png')
const EMPTY_HTML_PATH = path.join(EMPTY_SCRAPE_DIR, 'marketplace-empty.html')
const EMPTY_META_PATH = path.join(EMPTY_SCRAPE_DIR, 'marketplace-empty.json')

async function captureEmptyScrapeDiagnostics(
  page: Page,
  searchParams: MarketplaceSearchParams,
  initialUrl: string,
): Promise<EmptyScrapeDiagnostics> {
  const finalUrl = page.url()
  const pageTitle = await page.title()
  const loginFieldsExist = await detectLoginRequired(page)
  const captchaExists = await detectCaptcha(page)
  const marketplaceUnavailable = await pageTextIncludes(
    page,
    "Marketplace isn't available",
  )
  const somethingWentWrong = await pageTextIncludes(page, 'Something went wrong')
  const listingAnchorCount = await page
    .locator('a[href*="/marketplace/item/"]')
    .count()

  console.log(`[marketplace-empty] Final URL: ${finalUrl}`)
  console.log(`[marketplace-empty] Page title: ${pageTitle}`)
  console.log(`[marketplace-empty] Login fields exist: ${loginFieldsExist}`)
  console.log(`[marketplace-empty] CAPTCHA exists: ${captchaExists}`)
  console.log(
    `[marketplace-empty] "Marketplace isn't available" exists: ${marketplaceUnavailable}`,
  )
  console.log(
    `[marketplace-empty] "Something went wrong" exists: ${somethingWentWrong}`,
  )
  console.log(
    `[marketplace-empty] Listing anchors exist: ${listingAnchorCount > 0} (count=${listingAnchorCount})`,
  )

  fs.mkdirSync(EMPTY_SCRAPE_DIR, { recursive: true })
  await page.screenshot({ path: EMPTY_SCREENSHOT_PATH, fullPage: true })
  fs.writeFileSync(EMPTY_HTML_PATH, await page.content(), 'utf8')

  const diagnostics: EmptyScrapeDiagnostics = {
    capturedAt: new Date().toISOString(),
    query: searchParams.query,
    location: searchParams.location,
    initialUrl,
    finalUrl,
    pageTitle,
    loginFieldsExist,
    captchaExists,
    marketplaceUnavailable,
    somethingWentWrong,
    listingAnchorCount,
    screenshotPath: EMPTY_SCREENSHOT_PATH,
    htmlPath: EMPTY_HTML_PATH,
    metaPath: EMPTY_META_PATH,
  }

  fs.writeFileSync(EMPTY_META_PATH, JSON.stringify(diagnostics, null, 2), 'utf8')

  console.log(`[marketplace-empty] Saved screenshot: ${EMPTY_SCREENSHOT_PATH}`)
  console.log(`[marketplace-empty] Saved HTML: ${EMPTY_HTML_PATH}`)
  console.log(`[marketplace-empty] Saved meta: ${EMPTY_META_PATH}`)
  console.log(
    '[marketplace-empty] Inspect via GET /debug/marketplace-empty (and /screenshot, /html)',
  )

  return diagnostics
}

export function getEmptyScrapeArtifactPaths() {
  return {
    screenshotPath: EMPTY_SCREENSHOT_PATH,
    htmlPath: EMPTY_HTML_PATH,
    metaPath: EMPTY_META_PATH,
  }
}

export function readEmptyScrapeMeta(): EmptyScrapeDiagnostics | null {
  if (!fs.existsSync(EMPTY_META_PATH)) return null
  try {
    return JSON.parse(
      fs.readFileSync(EMPTY_META_PATH, 'utf8'),
    ) as EmptyScrapeDiagnostics
  } catch {
    return null
  }
}

async function waitForListings(page: Page, timeoutMs: number): Promise<void> {
  await page
    .waitForSelector('a[href*="/marketplace/item/"]', { timeout: timeoutMs })
    .catch(() => undefined)
}

async function collectListings(
  page: Page,
  maxListings: number,
): Promise<ListingInput[]> {
  const anchors = page.locator('a[href*="/marketplace/item/"]')
  const total = await anchors.count()
  const results: ListingInput[] = []
  const seenUrls = new Set<string>()

  for (let i = 0; i < total && results.length < maxListings; i++) {
    const anchor = anchors.nth(i)
    const href = await anchor.getAttribute('href')

    if (!href) {
      continue
    }

    const listingUrl = href.startsWith('http')
      ? href.split('?')[0]
      : `https://www.facebook.com${href.split('?')[0]}`

    if (seenUrls.has(listingUrl)) {
      continue
    }

    seenUrls.add(listingUrl)

    const text = (await anchor.innerText().catch(() => '')) || ''
    const { title, price, location } = parseListingText(text)
    const imageUrl =
      (await anchor.locator('img').first().getAttribute('src').catch(() => null)) ??
      null

    results.push({
      source: FACEBOOK_MARKETPLACE_SOURCE,
      listingUrl,
      title,
      price,
      location,
      imageUrl,
    })
  }

  return results
}

export async function scrapeMarketplaceSearch(
  searchParams: MarketplaceSearchParams,
  options: ScrapeOptions = {},
): Promise<ListingInput[]> {
  const {
    headless = true,
    maxListings = 5,
    listingWaitTimeoutMs = 30_000,
    onPageReady,
  } = options

  const searchUrl = buildMarketplaceSearchUrl(searchParams)
  const browser = await chromium.launch({ headless })

  // Default: use anonymous Marketplace scraping.
  // If USE_FACEBOOK_AUTH=true, load the saved Facebook session instead.
  const rawUseFacebookAuth = process.env.USE_FACEBOOK_AUTH
  const useFacebookAuth = rawUseFacebookAuth === 'true'
  const stateFileExists = fs.existsSync(FACEBOOK_STORAGE_STATE_PATH)
  const loadingAuthenticatedSession = useFacebookAuth && stateFileExists

  console.log(`USE_FACEBOOK_AUTH=${rawUseFacebookAuth ?? '(unset)'}`)
  console.log(`facebook-state.json exists: ${stateFileExists}`)
  console.log(`Loading authenticated session: ${loadingAuthenticatedSession}`)
  if (loadingAuthenticatedSession) {
    console.log('Creating authenticated Playwright context (storageState will be passed)')
  } else {
    console.log('Creating anonymous Playwright context')
  }

  const context = loadingAuthenticatedSession
    ? await browser.newContext({ storageState: FACEBOOK_STORAGE_STATE_PATH })
    : await browser.newContext()

  if (loadingAuthenticatedSession) {
    console.log(
      `Using authenticated Facebook session from ${FACEBOOK_STORAGE_STATE_PATH}`,
    )
  } else if (useFacebookAuth && !stateFileExists) {
    console.log(
      'USE_FACEBOOK_AUTH=true but no storage state found — using anonymous browser session',
    )
  } else {
    console.log('Using anonymous Facebook Marketplace session')
  }

  const page = await context.newPage()

  try {
    console.log(`[marketplace] Search query: ${searchParams.query}`)
    console.log(`[marketplace] Initial URL: ${searchUrl}`)

    await page.goto(searchUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 60_000,
    })

    const finalUrl = page.url()
    const pageTitle = await page.title()
    const loginUiDetected = await detectLoginRequired(page)

    console.log(`[marketplace] Final URL: ${finalUrl}`)
    console.log(`[marketplace] Page title: ${pageTitle}`)
    console.log(`[marketplace] Login UI detected: ${loginUiDetected}`)

    if (onPageReady) {
      await onPageReady(page)
    } else if (loginUiDetected) {
      console.warn(
        'Facebook login UI detected during anonymous scrape. Continuing without waiting for manual login.',
      )
    }

    await waitForListings(page, listingWaitTimeoutMs)

    const anchorCount = await page
      .locator('a[href*="/marketplace/item/"]')
      .count()
    console.log(`[marketplace] Listing anchors found: ${anchorCount}`)

    // Must await before the finally block runs, otherwise browser.close()
    // executes while collectListings() is still using the page.
    const listings = await collectListings(page, maxListings)
    console.log(`[marketplace] Listings returned: ${listings.length}`)

    if (listings.length === 0) {
      await captureEmptyScrapeDiagnostics(page, searchParams, searchUrl)
    }

    return listings
  } catch (error) {
    throw new ScraperError(
      `Failed to scrape Marketplace for query "${searchParams.query}"`,
      { cause: error },
    )
  } finally {
    await browser.close()
  }
}

export { detectLoginRequired }
