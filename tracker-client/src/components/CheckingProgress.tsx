import { useEffect, useState } from 'react'
import { CHECK_PROGRESS_MESSAGES } from '../lib/copy'

export function CheckingProgress() {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((current) => (current + 1) % CHECK_PROGRESS_MESSAGES.length)
    }, 2800)

    return () => clearInterval(interval)
  }, [])

  return (
    <p className="flex items-center gap-2 text-sm text-stone-500">
      <span className="inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-stone-300 border-t-stone-700" />
      {CHECK_PROGRESS_MESSAGES[index]}
    </p>
  )
}
