import { Router } from 'express'
import { getAllListings } from '../store/listings'

const router = Router()

router.get('/', async (_req, res) => {
  try {
    const listings = await getAllListings()
    res.json(listings)
  } catch {
    res.status(500).json({ error: 'Failed to load listings' })
  }
})

export default router
