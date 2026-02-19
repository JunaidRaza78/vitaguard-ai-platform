import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import { Toaster } from 'react-hot-toast'
import useAuthStore from '@/stores/authStore'
import useThemeStore from '@/stores/themeStore'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AppLayout from '@/components/layout/AppLayout'
import AuthLayout from '@/components/layout/AuthLayout'
import Spinner from '@/components/ui/Spinner'

// Lazy-loaded pages for code splitting
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'))
const ForgotPasswordPage = lazy(() => import('@/pages/auth/ForgotPasswordPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const ChatPage = lazy(() => import('@/pages/ChatPage'))
const DocumentsPage = lazy(() => import('@/pages/DocumentsPage'))
const ProfilePage = lazy(() => import('@/pages/ProfilePage'))
const FamilyPage = lazy(() => import('@/pages/FamilyPage'))
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage'))
const LabReportsPage = lazy(() => import('@/pages/LabReportsPage'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-20">
      <Spinner size="lg" />
    </div>
  )
}

export default function App() {
  const initialize = useAuthStore((s) => s.initialize)
  const isDark = useThemeStore((s) => s.isDark)

  useEffect(() => {
    initialize()
  }, [initialize])

  useEffect(() => {
    document.documentElement.classList.toggle('light-mode', !isDark)
  }, [isDark])

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'rgba(255,255,255,0.1)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.15)',
            color: 'white',
            fontSize: '14px',
          },
        }}
      />

      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public auth routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          </Route>

          {/* Protected app routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/family" element={<FamilyPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/lab-reports" element={<LabReportsPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
