import * as fs from 'fs'
import * as path from 'path'
import * as readline from 'readline'
import { chromium } from 'playwright'

const FACEBOOK_HOME_URL = 'https://www.facebook.com/'
const STORAGE_DIR = path.join(process.cwd(), 'storage')
const STORAGE_STATE_PATH = path.join(STORAGE_DIR, 'facebook-state.json')

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

async function main() {
  fs.mkdirSync(STORAGE_DIR, { recursive: true })

  console.log('Launching Chromium (visible window)...')
  console.log('Log in to Facebook in the browser window.')
  console.log('This script only saves your session — it does not scrape Marketplace.\n')

  const browser = await chromium.launch({ headless: false })
  const context = await browser.newContext()
  const page = await context.newPage()

  try {
    await page.goto(FACEBOOK_HOME_URL, {
      waitUntil: 'domcontentloaded',
      timeout: 60_000,
    })

    console.log(`Opened ${FACEBOOK_HOME_URL}`)
    console.log(`Page title: ${await page.title()}\n`)

    await waitForEnter(
      'Press Enter once you are logged in and can see your Facebook home feed... ',
    )

    await context.storageState({ path: STORAGE_STATE_PATH })
    console.log(`\nSaved authenticated session to ${STORAGE_STATE_PATH}`)
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  console.error('Facebook auth failed:', error)
  process.exit(1)
})
