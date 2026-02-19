import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

const variants = {
  primary: 'btn-gradient-cyan text-white',
  secondary: 'btn-gradient-violet text-white',
  success: 'btn-gradient-emerald text-white',
  ghost: 'glass glass-hover text-white',
  danger: 'bg-gradient-to-r from-rose-500 to-red-600 text-white hover:shadow-[0_0_25px_rgba(244,63,94,0.4)]',
  outline: 'border border-white/20 text-white hover:bg-white/10',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-5 py-2.5 text-sm rounded-xl',
  lg: 'px-7 py-3 text-base rounded-xl',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className,
  as,
  ...props
}) {
  const Component = as || motion.button
  const motionProps = as ? {} : {
    whileHover: { scale: disabled ? 1 : 1.02 },
    whileTap: { scale: disabled ? 1 : 0.98 },
  }

  return (
    <Component
      {...motionProps}
      className={cn(
        'font-medium transition-all duration-300 flex items-center justify-center gap-2',
        variants[variant],
        sizes[size],
        (disabled || loading) && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </Component>
  )
}
