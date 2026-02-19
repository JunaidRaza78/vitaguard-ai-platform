import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { Mail, ArrowLeft, Send } from 'lucide-react'
import toast from 'react-hot-toast'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import api from '@/lib/axios'

const schema = z.object({
  email: z.string().email('Invalid email address'),
})

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await api.post('/api/v1/auth/forgot-password', data)
      setSent(true)
      toast.success('Reset link sent to your email')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send reset link')
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-4">
        <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 flex items-center justify-center mx-auto mb-4">
          <Send className="w-7 h-7 text-emerald-400" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Check your email</h2>
        <p className="text-sm text-white/40 mb-6">
          We've sent a password reset link to your email address.
        </p>
        <Link to="/login" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium">
          Back to sign in
        </Link>
      </motion.div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
      <h2 className="text-xl font-bold text-white mb-1">Forgot password?</h2>
      <p className="text-sm text-white/40 mb-6">Enter your email to receive a reset link</p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Email"
          type="email"
          placeholder="you@example.com"
          icon={Mail}
          error={errors.email?.message}
          {...register('email')}
        />
        <Button type="submit" loading={loading} className="w-full">
          Send Reset Link
        </Button>
      </form>

      <p className="text-center mt-6">
        <Link to="/login" className="text-sm text-white/40 hover:text-white/60 transition-colors inline-flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Back to sign in
        </Link>
      </p>
    </motion.div>
  )
}
