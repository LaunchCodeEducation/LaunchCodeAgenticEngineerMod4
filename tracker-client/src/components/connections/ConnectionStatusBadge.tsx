import type { ConnectionStatus } from '../../types'

const STATUS_LABELS: Record<ConnectionStatus, string> = {
  not_connected: 'Not Connected',
  connected: 'Connected',
  session_expired: 'Session Expired',
  connection_error: 'Connection Error',
}

const STATUS_STYLES: Record<ConnectionStatus, string> = {
  not_connected: 'bg-stone-100 text-stone-600 ring-stone-200/80',
  connected: 'bg-emerald-50 text-emerald-800 ring-emerald-200/80',
  session_expired: 'bg-amber-50 text-amber-900 ring-amber-200/80',
  connection_error: 'bg-red-50 text-red-800 ring-red-200/80',
}

type ConnectionStatusBadgeProps = {
  status: ConnectionStatus
}

export function ConnectionStatusBadge({ status }: ConnectionStatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}
