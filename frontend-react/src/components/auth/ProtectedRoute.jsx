import { Navigate } from 'react-router-dom'
import useAuthStore from '@/stores/authStore'
import Spinner from '@/components/ui/Spinner'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="mesh-gradient" />
        <div className="text-center">
          <Spinner size="lg" className="mx-auto mb-4" />
          <p className="text-sm text-white/40">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}
