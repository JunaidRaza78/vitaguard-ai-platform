import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export default function GlassCard({ children, className, hover = true, glow, animate = true, ...props }) {
  const Component = animate ? motion.div : 'div'
  const animateProps = animate ? {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 },
  } : {}

  return (
    <Component
      className={cn(
        'glass rounded-2xl p-6',
        hover && 'glass-hover transition-all duration-300',
        glow && `glow-${glow}`,
        className
      )}
      {...animateProps}
      {...props}
    >
      {children}
    </Component>
  )
}
