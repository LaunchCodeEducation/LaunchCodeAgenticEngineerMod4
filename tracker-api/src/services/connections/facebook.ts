import * as fs from 'fs'
import * as path from 'path'
import type {
  ConnectProviderResult,
  DisconnectProviderResult,
  ProviderConnection,
} from '../../types/provider-connection'
import type { ProviderConnectionService } from './types'

/**
 * Same path the scraper and facebook:auth script use.
 * Kept here (not imported into the scraper) so connection management
 * can evolve without touching scrape behavior.
 */
const FACEBOOK_STORAGE_STATE_PATH = path.join(
  process.cwd(),
  'storage',
  'facebook-state.json',
)

const AUTH_COMMAND = 'npm run facebook:auth'

function baseConnection(
  partial: Pick<ProviderConnection, 'status' | 'lastConnectedAt' | 'message'>,
): ProviderConnection {
  return {
    providerId: 'facebook',
    displayName: 'Facebook Marketplace',
    description:
      'Optional authenticated Facebook session. Scout searches Marketplace anonymously by default.',
    ...partial,
  }
}

function readSessionFileMeta(): {
  exists: boolean
  lastConnectedAt: string | null
  parseError: boolean
} {
  if (!fs.existsSync(FACEBOOK_STORAGE_STATE_PATH)) {
    return { exists: false, lastConnectedAt: null, parseError: false }
  }

  let lastConnectedAt: string | null = null
  try {
    const stats = fs.statSync(FACEBOOK_STORAGE_STATE_PATH)
    lastConnectedAt = stats.mtime.toISOString()
  } catch {
    lastConnectedAt = null
  }

  try {
    const raw = fs.readFileSync(FACEBOOK_STORAGE_STATE_PATH, 'utf8')
    const parsed = JSON.parse(raw) as { cookies?: unknown }
    if (!parsed || !Array.isArray(parsed.cookies)) {
      return { exists: true, lastConnectedAt, parseError: true }
    }
    return { exists: true, lastConnectedAt, parseError: false }
  } catch {
    return { exists: true, lastConnectedAt, parseError: true }
  }
}

function resolveConnection(): ProviderConnection {
  const meta = readSessionFileMeta()

  if (!meta.exists) {
    return baseConnection({
      status: 'not_connected',
      lastConnectedAt: null,
      message:
        'No authenticated session saved. Scout still searches Marketplace anonymously.',
    })
  }

  if (meta.parseError) {
    return baseConnection({
      status: 'connection_error',
      lastConnectedAt: meta.lastConnectedAt,
      message:
        'A Facebook session file was found but could not be read. Reconnect to fix this.',
    })
  }

  // session_expired is reserved for later detection (e.g. scraper hits login).
  // A valid session file means an optional authenticated fallback is available.
  return baseConnection({
    status: 'connected',
    lastConnectedAt: meta.lastConnectedAt,
    message:
      'Optional authenticated session is saved. Scout searches Marketplace anonymously by default.',
  })
}

function connectViaExistingAuthScript(): ConnectProviderResult {
  const connection = resolveConnection()

  return {
    providerId: 'facebook',
    connection,
    action: {
      mode: 'external_script',
      command: AUTH_COMMAND,
      message:
        connection.status === 'connected'
          ? 'An authenticated session is already saved. To refresh it, run the optional auth utility in tracker-api, then refresh status here.'
          : 'Optional: complete Facebook login with the auth utility in tracker-api (`npm run facebook:auth`), then refresh status. Marketplace searches work anonymously without this.',
    },
  }
}

export const facebookConnectionService: ProviderConnectionService = {
  providerId: 'facebook',

  async getConnection() {
    return resolveConnection()
  },

  async connect() {
    return connectViaExistingAuthScript()
  },

  async reconnect() {
    return connectViaExistingAuthScript()
  },

  async disconnect() {
    return {
      providerId: 'facebook',
      implemented: false,
      message:
        'Disconnect is not implemented yet. Remove storage/facebook-state.json manually if you need to clear the session.',
      connection: resolveConnection(),
    }
  },
}
