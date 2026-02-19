import { forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

const Select = forwardRef(({ label, error, options = [], className, ...props }, ref) => {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="text-sm font-medium text-white/70">{label}</label>
      )}
      <div className="relative">
        <select
          ref={ref}
          className={cn(
            'glass-input w-full px-4 py-3 text-sm appearance-none pr-10',
            error && 'border-rose-500/50',
            className
          )}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-[#12121a] text-white">
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
      </div>
      {error && <p className="text-xs text-rose-400">{error}</p>}
    </div>
  )
})

Select.displayName = 'Select'
export default Select
