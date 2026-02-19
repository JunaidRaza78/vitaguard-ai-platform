import { cn } from '@/lib/utils'

const colors = {
  cyan: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  emerald: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  violet: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  rose: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  amber: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  gray: 'bg-white/10 text-white/60 border-white/20',
}

export default function Badge({ children, color = 'cyan', className }) {
  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full border',
      colors[color],
      className
    )}>
      {children}
    </span>
  )
}
