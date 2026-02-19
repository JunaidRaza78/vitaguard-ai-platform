import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

const Textarea = forwardRef(({ label, error, className, ...props }, ref) => {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="text-sm font-medium text-white/70">{label}</label>
      )}
      <textarea
        ref={ref}
        className={cn(
          'glass-input w-full px-4 py-3 text-sm resize-none min-h-[100px]',
          error && 'border-rose-500/50',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-rose-400">{error}</p>}
    </div>
  )
})

Textarea.displayName = 'Textarea'
export default Textarea
