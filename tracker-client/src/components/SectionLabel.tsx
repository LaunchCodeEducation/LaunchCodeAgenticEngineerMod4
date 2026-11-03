type SectionLabelProps = {
  children: React.ReactNode
  action?: React.ReactNode
}

export function SectionLabel({ children, action }: SectionLabelProps) {
  return (
    <div className="flex min-h-8 items-center justify-between gap-3">
      <h2 className="text-[13px] font-medium text-stone-500">{children}</h2>
      {action}
    </div>
  )
}
