import { Link } from 'react-router-dom'
import type { ConnectionStatus } from '../types'
import { SectionLabel } from './SectionLabel'

type Props = {
  facebookStatus: ConnectionStatus | null
  loading?: boolean
}

function facebookLabel(status: ConnectionStatus | null, loading?: boolean): string {
  if (loading || !status) return '…'
  if (status === 'connected') return 'Connected'
  // Anonymous scraping works without a saved session
  return 'Available'
}

export function ProviderStatusList({ facebookStatus, loading }: Props) {
  const items = [
    {
      id: 'facebook',
      name: 'Facebook Marketplace',
      statusLabel: facebookLabel(facebookStatus, loading),
      live: facebookStatus === 'connected',
    },
    {
      id: 'craigslist',
      name: 'Craigslist',
      statusLabel: 'Coming soon',
      live: false,
    },
    {
      id: 'offerup',
      name: 'OfferUp',
      statusLabel: 'Planned',
      live: false,
    },
  ]

  return (
    <section className="space-y-2">
      <SectionLabel
        action={
          <Link
            to="/settings"
            className="text-[13px] font-medium text-stone-500 active:text-stone-800"
          >
            Settings
          </Link>
        }
      >
        Providers
      </SectionLabel>
      <ul className="overflow-hidden rounded-2xl border border-stone-200/70 bg-white">
        {items.map((item, index) => (
          <li
            key={item.id}
            className={`flex min-h-12 items-center justify-between gap-3 px-4 ${
              index > 0 ? 'border-t border-stone-100' : ''
            }`}
          >
            <span className="text-[15px] text-stone-900">{item.name}</span>
            <span
              className={`shrink-0 text-sm ${
                item.live ? 'font-medium text-emerald-700' : 'text-stone-400'
              }`}
            >
              {item.statusLabel}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
