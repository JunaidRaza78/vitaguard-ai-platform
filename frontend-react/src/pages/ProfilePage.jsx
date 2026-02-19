import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { User, Mail, Lock, Save, Shield } from 'lucide-react'
import toast from 'react-hot-toast'
import GlassCard from '@/components/ui/GlassCard'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import useAuthStore from '@/stores/authStore'
import { getInitials } from '@/lib/utils'
import api from '@/lib/axios'

const profileSchema = z.object({
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  email: z.string().email(),
})

const passwordSchema = z.object({
  current_password: z.string().min(6),
  new_password: z.string().min(8),
  confirm_password: z.string(),
}).refine(d => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

export default function ProfilePage() {
  const { user, updateProfile } = useAuthStore()
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)

  const profileForm = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
    },
  })

  const passwordForm = useForm({
    resolver: zodResolver(passwordSchema),
  })

  const handleProfileSave = async (data) => {
    setSavingProfile(true)
    try {
      await updateProfile(data)
      toast.success('Profile updated')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSavingProfile(false)
    }
  }

  const handlePasswordChange = async (data) => {
    setSavingPassword(true)
    try {
      await api.post('/api/v1/auth/change-password', {
        current_password: data.current_password,
        new_password: data.new_password,
      })
      toast.success('Password changed')
      passwordForm.reset()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password')
    } finally {
      setSavingPassword(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Profile header */}
      <GlassCard className="text-center py-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200 }}
          className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white glow-violet"
        >
          {getInitials(user?.first_name, user?.last_name)}
        </motion.div>
        <h2 className="text-xl font-bold text-white">
          {user?.first_name} {user?.last_name}
        </h2>
        <p className="text-sm text-white/40">{user?.email}</p>
      </GlassCard>

      {/* Edit Profile */}
      <GlassCard>
        <div className="flex items-center gap-2 mb-4">
          <User className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white/80">Edit Profile</h3>
        </div>
        <form onSubmit={profileForm.handleSubmit(handleProfileSave)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name"
              icon={User}
              error={profileForm.formState.errors.first_name?.message}
              {...profileForm.register('first_name')}
            />
            <Input
              label="Last Name"
              icon={User}
              error={profileForm.formState.errors.last_name?.message}
              {...profileForm.register('last_name')}
            />
          </div>
          <Input
            label="Email"
            type="email"
            icon={Mail}
            error={profileForm.formState.errors.email?.message}
            {...profileForm.register('email')}
          />
          <Button type="submit" loading={savingProfile}>
            <Save className="w-4 h-4" />
            Save Changes
          </Button>
        </form>
      </GlassCard>

      {/* Change Password */}
      <GlassCard>
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-4 h-4 text-violet-400" />
          <h3 className="text-sm font-semibold text-white/80">Change Password</h3>
        </div>
        <form onSubmit={passwordForm.handleSubmit(handlePasswordChange)} className="space-y-4">
          <Input
            label="Current Password"
            type="password"
            icon={Lock}
            error={passwordForm.formState.errors.current_password?.message}
            {...passwordForm.register('current_password')}
          />
          <Input
            label="New Password"
            type="password"
            icon={Lock}
            error={passwordForm.formState.errors.new_password?.message}
            {...passwordForm.register('new_password')}
          />
          <Input
            label="Confirm New Password"
            type="password"
            icon={Lock}
            error={passwordForm.formState.errors.confirm_password?.message}
            {...passwordForm.register('confirm_password')}
          />
          <Button type="submit" variant="secondary" loading={savingPassword}>
            <Lock className="w-4 h-4" />
            Change Password
          </Button>
        </form>
      </GlassCard>
    </div>
  )
}
