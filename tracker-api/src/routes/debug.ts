import * as fs from 'fs'
import { Router } from 'express'
import {
  getEmptyScrapeArtifactPaths,
  readEmptyScrapeMeta,
} from '../services/facebook-scraper'

/**
 * Temporary production diagnostics for empty Marketplace scrapes.
 * Remove once the local-vs-production difference is understood.
 */
const router = Router()

router.get('/marketplace-empty', (_req, res) => {
  const meta = readEmptyScrapeMeta()
  const paths = getEmptyScrapeArtifactPaths()

  res.json({
    available: Boolean(meta),
    meta,
    artifacts: {
      meta: '/debug/marketplace-empty',
      screenshot: '/debug/marketplace-empty/screenshot',
      html: '/debug/marketplace-empty/html',
    },
    filesOnDisk: {
      screenshotExists: fs.existsSync(paths.screenshotPath),
      htmlExists: fs.existsSync(paths.htmlPath),
      metaExists: fs.existsSync(paths.metaPath),
    },
  })
})

router.get('/marketplace-empty/screenshot', (_req, res) => {
  const { screenshotPath } = getEmptyScrapeArtifactPaths()
  if (!fs.existsSync(screenshotPath)) {
    res.status(404).json({ error: 'No empty-scrape screenshot captured yet' })
    return
  }
  res.type('png').send(fs.readFileSync(screenshotPath))
})

router.get('/marketplace-empty/html', (_req, res) => {
  const { htmlPath } = getEmptyScrapeArtifactPaths()
  if (!fs.existsSync(htmlPath)) {
    res.status(404).json({ error: 'No empty-scrape HTML captured yet' })
    return
  }
  res.type('html').send(fs.readFileSync(htmlPath, 'utf8'))
})

export default router
