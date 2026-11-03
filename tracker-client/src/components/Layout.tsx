import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAppData } from '../context/AppDataContext'

export function Layout() {
  const { error } = useAppData()
  const location = useLocation()
  const isSettings = location.pathname.startsWith('/settings')

  return (
    <div className="min-h-dvh bg-[#f7f6f3] text-stone-900">
      <header className="sticky top-0 z-20 border-b border-stone-200/70 bg-[#f7f6f3] pt-[env(safe-area-inset-top)]">
        <div className="mx-auto flex h-14 max-w-xl items-center justify-between gap-3 px-4 sm:px-5">
          <Link
            to="/"
            className="text-[17px] font-semibold tracking-tight text-stone-900"
          >
            Scout
          </Link>
          <Link
            to="/settings"
            className={`inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg px-3 text-sm font-medium transition ${
              isSettings
                ? 'bg-stone-200/70 text-stone-900'
                : 'text-stone-500 active:bg-stone-200/50'
            }`}
            aria-current={isSettings ? 'page' : undefined}
          >
            Settings
          </Link>
        </div>
      </header>

      {error && (
        <div className="mx-auto max-w-xl px-4 pt-3 sm:px-5">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <main className="mx-auto max-w-xl px-4 pb-[max(2rem,env(safe-area-inset-bottom))] pt-5 sm:px-5 sm:pt-6">
        <Outlet />
      </main>
    </div>
  )
}
