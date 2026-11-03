import { useEffect, useState } from 'react'
import { useAppData } from '../context/AppDataContext'
import type { NewSearchForm, SavedSearch } from '../types'

const RESULTS_OPTIONS = ['5', '10', '20', '50'] as const

function searchToForm(search: SavedSearch): NewSearchForm {
  return {
    name: search.name,
    query: search.query,
    location: search.location,
    radius: String(search.radius),
    maxPrice: search.maxPrice ? String(search.maxPrice) : '',
    resultsPerSearch: String(search.resultsPerSearch),
  }
}

type Props = {
  search: SavedSearch
  isOpen: boolean
  onClose: () => void
  mode: 'edit' | 'rename'
}

export function WatchSettingsDialog({ search, isOpen, onClose, mode }: Props) {
  const { updateSearch } = useAppData()
  const [form, setForm] = useState(() => searchToForm(search))
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setForm(searchToForm(search))
    }
  }, [isOpen, search])

  if (!isOpen) return null

  function updateField(field: keyof NewSearchForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault()
    setIsSaving(true)
    try {
      await updateSearch(search.id, form)
      onClose()
    } finally {
      setIsSaving(false)
    }
  }

  const isRename = mode === 'rename'

  return (
    <div
      className="fixed inset-0 z-30 flex items-end justify-center bg-stone-900/20 sm:items-center"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-md overflow-y-auto bg-[#f7f6f3] px-6 py-6 sm:rounded-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-medium text-stone-900">
          {isRename ? 'Rename' : 'Edit'}
        </h2>
        <p className="mt-1 text-sm text-stone-500">
          {isRename
            ? 'Change how this watch appears on your list.'
            : 'Update location, price, and what you are looking for.'}
        </p>

        <form onSubmit={handleSave} className="mt-6 space-y-5">
          {isRename ? (
            <Field label="Name">
              <input
                value={form.name}
                onChange={(e) => updateField('name', e.target.value)}
                autoFocus
                className={inputClass}
              />
            </Field>
          ) : (
            <>
              <Field label="Looking for">
                <input
                  value={form.query}
                  onChange={(e) => updateField('query', e.target.value)}
                  required
                  className={inputClass}
                />
              </Field>

              <Field label="Location">
                <input
                  value={form.location}
                  onChange={(e) => updateField('location', e.target.value)}
                  required
                  className={inputClass}
                />
              </Field>

              <div className="grid gap-5 sm:grid-cols-2">
                <Field label="Radius (miles)">
                  <input
                    type="number"
                    value={form.radius}
                    onChange={(e) => updateField('radius', e.target.value)}
                    required
                    min={1}
                    className={inputClass}
                  />
                </Field>

                <Field label="Max price (optional)">
                  <input
                    type="number"
                    value={form.maxPrice}
                    onChange={(e) => updateField('maxPrice', e.target.value)}
                    placeholder="No limit"
                    min={1}
                    className={inputClass}
                  />
                </Field>
              </div>

              <Field label="Listings to check">
                <div className="flex flex-wrap gap-2">
                  {RESULTS_OPTIONS.map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => updateField('resultsPerSearch', value)}
                      className={`rounded-full px-3 py-1.5 text-sm ${
                        form.resultsPerSearch === value
                          ? 'bg-stone-900 text-white'
                          : 'text-stone-600 hover:bg-stone-100'
                      }`}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </Field>
            </>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isSaving}
              className="rounded-lg bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
            >
              {isSaving ? 'Saving…' : 'Save'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-stone-500 hover:text-stone-800"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <label className="block">
      <span className="text-sm text-stone-600">{label}</span>
      <div className="mt-1.5">{children}</div>
    </label>
  )
}

const inputClass =
  'w-full border-b border-stone-200 bg-transparent py-2 text-sm text-stone-900 focus:border-stone-800 focus:outline-none'
