import type { ProviderId } from '../../types/provider-connection'
import { facebookConnectionService } from './facebook'
import type { ProviderConnectionService } from './types'

/**
 * Registry of connection services. Add future providers (e.g. Craigslist)
 * here without changing route handlers.
 */
const services: Record<ProviderId, ProviderConnectionService> = {
  facebook: facebookConnectionService,
}

export function listConnectionServices(): ProviderConnectionService[] {
  return Object.values(services)
}

export function getConnectionService(
  providerId: string,
): ProviderConnectionService | null {
  if (providerId in services) {
    return services[providerId as ProviderId]
  }
  return null
}
