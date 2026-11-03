import { Router } from 'express'
import {
  getConnectionService,
  listConnectionServices,
} from '../services/connections'

const router = Router()

/** GET /connections — all provider connection statuses */
router.get('/', async (_req, res) => {
  try {
    const connections = await Promise.all(
      listConnectionServices().map((service) => service.getConnection()),
    )
    res.json({ connections })
  } catch (error) {
    console.error('Failed to list connections:', error)
    res.status(500).json({ error: 'Failed to list connections' })
  }
})

/** GET /connections/:providerId */
router.get('/:providerId', async (req, res) => {
  const service = getConnectionService(req.params.providerId)
  if (!service) {
    res.status(404).json({ error: 'Unknown provider' })
    return
  }

  try {
    const connection = await service.getConnection()
    res.json(connection)
  } catch (error) {
    console.error(`Failed to get ${req.params.providerId} connection:`, error)
    res.status(500).json({ error: 'Failed to get connection status' })
  }
})

/** POST /connections/:providerId/connect */
router.post('/:providerId/connect', async (req, res) => {
  const service = getConnectionService(req.params.providerId)
  if (!service) {
    res.status(404).json({ error: 'Unknown provider' })
    return
  }

  try {
    const result = await service.connect()
    res.json(result)
  } catch (error) {
    console.error(`Failed to connect ${req.params.providerId}:`, error)
    res.status(500).json({ error: 'Failed to start connection' })
  }
})

/** POST /connections/:providerId/reconnect */
router.post('/:providerId/reconnect', async (req, res) => {
  const service = getConnectionService(req.params.providerId)
  if (!service) {
    res.status(404).json({ error: 'Unknown provider' })
    return
  }

  try {
    const result = await service.reconnect()
    res.json(result)
  } catch (error) {
    console.error(`Failed to reconnect ${req.params.providerId}:`, error)
    res.status(500).json({ error: 'Failed to start reconnection' })
  }
})

/** DELETE /connections/:providerId — disconnect (may be placeholder) */
router.delete('/:providerId', async (req, res) => {
  const service = getConnectionService(req.params.providerId)
  if (!service) {
    res.status(404).json({ error: 'Unknown provider' })
    return
  }

  try {
    const result = await service.disconnect()
    if (!result.implemented) {
      res.status(501).json(result)
      return
    }
    res.json(result)
  } catch (error) {
    console.error(`Failed to disconnect ${req.params.providerId}:`, error)
    res.status(500).json({ error: 'Failed to disconnect' })
  }
})

export default router
