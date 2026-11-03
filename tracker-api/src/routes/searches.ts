import { Router } from 'express'
import { runSavedSearch } from '../services/search-runner'
import {
  createSearch,
  deleteSearch,
  getAllSearches,
  updateSearch,
} from '../store/searches'

const router = Router()

router.get('/', async (_req, res) => {
  try {
    const searches = await getAllSearches()
    res.json(searches)
  } catch {
    res.status(500).json({ error: 'Failed to load searches' })
  }
})

router.post('/', async (req, res) => {
  const { name, query, maxPrice, location, radius, resultsPerSearch } = req.body

  if (!name || typeof name !== 'string' || !name.trim()) {
    res.status(400).json({ error: 'Name is required' })
    return
  }

  if (!query || typeof query !== 'string' || !query.trim()) {
    res.status(400).json({ error: 'Query is required' })
    return
  }

  if (!location || typeof location !== 'string' || !location.trim()) {
    res.status(400).json({ error: 'Location is required' })
    return
  }

  if (radius === undefined || typeof radius !== 'number' || radius <= 0) {
    res.status(400).json({ error: 'Radius must be a positive number' })
    return
  }

  if (
    maxPrice !== undefined &&
    maxPrice !== null &&
    (typeof maxPrice !== 'number' || maxPrice <= 0)
  ) {
    res.status(400).json({ error: 'Max price must be a positive number' })
    return
  }

  if (
    resultsPerSearch !== undefined &&
    (typeof resultsPerSearch !== 'number' ||
      ![5, 10, 20, 50].includes(resultsPerSearch))
  ) {
    res.status(400).json({ error: 'Results per search must be 5, 10, 20, or 50' })
    return
  }

  try {
    const search = await createSearch({
      name: name.trim(),
      query: query.trim(),
      maxPrice: maxPrice ?? null,
      location: location.trim(),
      radius,
      resultsPerSearch: resultsPerSearch ?? 10,
    })
    res.status(201).json(search)
  } catch {
    res.status(500).json({ error: 'Failed to create search' })
  }
})

router.patch('/:id', async (req, res) => {
  const { name, query, maxPrice, location, radius, resultsPerSearch } = req.body

  if (name !== undefined && (typeof name !== 'string' || !name.trim())) {
    res.status(400).json({ error: 'Name is required' })
    return
  }

  if (query !== undefined && (typeof query !== 'string' || !query.trim())) {
    res.status(400).json({ error: 'Query is required' })
    return
  }

  if (location !== undefined && (typeof location !== 'string' || !location.trim())) {
    res.status(400).json({ error: 'Location is required' })
    return
  }

  if (radius !== undefined && (typeof radius !== 'number' || radius <= 0)) {
    res.status(400).json({ error: 'Radius must be a positive number' })
    return
  }

  if (
    maxPrice !== undefined &&
    maxPrice !== null &&
    (typeof maxPrice !== 'number' || maxPrice <= 0)
  ) {
    res.status(400).json({ error: 'Max price must be a positive number' })
    return
  }

  if (
    resultsPerSearch !== undefined &&
    (typeof resultsPerSearch !== 'number' ||
      ![5, 10, 20, 50].includes(resultsPerSearch))
  ) {
    res.status(400).json({ error: 'Results per search must be 5, 10, 20, or 50' })
    return
  }

  try {
    const search = await updateSearch(req.params.id, {
      ...(name !== undefined && { name: name.trim() }),
      ...(query !== undefined && { query: query.trim() }),
      ...(location !== undefined && { location: location.trim() }),
      ...(radius !== undefined && { radius }),
      ...(maxPrice !== undefined && { maxPrice }),
      ...(resultsPerSearch !== undefined && { resultsPerSearch }),
    })

    if (!search) {
      res.status(404).json({ error: 'Search not found' })
      return
    }

    res.json(search)
  } catch {
    res.status(500).json({ error: 'Failed to update search' })
  }
})

router.post('/:id/run', async (req, res) => {
  try {
    const result = await runSavedSearch(req.params.id)

    if (!result) {
      res.status(404).json({ error: 'Search not found' })
      return
    }

    res.json(result)
  } catch (error) {
    console.error('Failed to run search:', error)

    if (error instanceof Error && error.cause) {
      console.error('Caused by:', error.cause)
    }

    res.status(500).json({ error: 'Failed to run search' })
  }
})

router.delete('/:id', async (req, res) => {
  try {
    const deleted = await deleteSearch(req.params.id)

    if (!deleted) {
      res.status(404).json({ error: 'Search not found' })
      return
    }

    res.status(204).send()
  } catch {
    res.status(500).json({ error: 'Failed to delete search' })
  }
})

export default router
