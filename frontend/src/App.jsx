import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Recommendations from './pages/Recommendations'
import Profile from './pages/Profile'
import ResumeReview from './pages/ResumeReview'
import Teams from './pages/Teams'
import TeamForm from './pages/TeamForm'
import TeamDetail from './pages/TeamDetail'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="skeleton" style={{ width: 180, height: 20, marginBottom: 24 }} />
          <div className="skeleton" style={{ width: '100%', height: 40, marginBottom: 12 }} />
          <div className="skeleton" style={{ width: '100%', height: 40, marginBottom: 12 }} />
          <div className="skeleton" style={{ width: '60%', height: 40 }} />
        </div>
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return null
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/teammates" element={<Recommendations />} />
        <Route path="/developers/:userId" element={<Profile />} />
        <Route path="/review-resume" element={<ResumeReview />} />
        <Route path="/teams" element={<Teams />} />
        <Route path="/teams/new" element={<TeamForm mode="create" />} />
        <Route path="/teams/:id" element={<TeamDetail />} />
        <Route path="/teams/:id/edit" element={<TeamForm mode="edit" />} />
      </Route>
      <Route path="/recommendations" element={<Navigate to="/teammates" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
