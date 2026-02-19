import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

const Input = forwardRef(({ label, error, icon: Icon, className, ...props }, ref) => {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="text-sm font-medium text-white/70">{label}</label>
      )}
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
        )}
        <input
          ref={ref}
          className={cn(
            'glass-input w-full px-4 py-3 text-sm',
            Icon && 'pl-10',
            error && 'border-rose-500/50 focus:border-rose-500',
            className
          )}
          {...props}
        />
      </div>
      {error && (
        <p className="text-xs text-rose-400">{error}</p>
      )}
    </div>
  )
})

Input.displayName = 'Input'
export default Input
