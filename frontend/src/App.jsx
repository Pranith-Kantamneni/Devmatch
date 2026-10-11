import { Routes, Route, Navigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Home from './pages/Home'
import Recommendations from './pages/Recommendations'
import Profile from './pages/Profile'
import ResumeReview from './pages/ResumeReview'
import OAuthCallback from './pages/OAuthCallback'
import Teams from './pages/Teams'
import TeamForm from './pages/TeamForm'
import TeamDetail from './pages/TeamDetail'
import Messages from './pages/Messages'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()
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
  if (!isAuthenticated)
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return children
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()
  if (loading) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="skeleton" style={{ width: 180, height: 20, marginBottom: 24 }} />
          <div className="skeleton" style={{ width: '100%', height: 40, marginBottom: 12 }} />
          <div className="skeleton" style={{ width: '100%', height: 40 }} />
        </div>
      </div>
    )
  }
  if (isAuthenticated) {
    const from = location.state?.from || '/home'
    return <Navigate to={from} replace />
  }
  return children
}

function NotFound() {
  const { isAuthenticated } = useAuth()
  return (
    <div className="page">
      <div className="empty-state">
        <h3 className="empty-title">Page not found</h3>
        <p className="empty-desc">The page you are looking for does not exist.</p>
        <div className="empty-action">
          <Link to={isAuthenticated ? '/home' : '/'} className="btn btn-secondary">
            Go {isAuthenticated ? 'home' : 'to landing'}
          </Link>
        </div>
      </div>
    </div>
  )
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
      <Route path="/auth/callback" element={<OAuthCallback />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/home" element={<Home />} />
        <Route path="/teammates" element={<Recommendations />} />
        <Route path="/developers/:userId" element={<Profile />} />
        <Route path="/review-resume" element={<ResumeReview />} />
        <Route path="/teams" element={<Teams />} />
        <Route path="/messages" element={<Messages />} />
        <Route path="/teams/new" element={<TeamForm mode="create" />} />
        <Route path="/teams/:id" element={<TeamDetail />} />
        <Route path="/teams/:id/edit" element={<TeamForm mode="edit" />} />
      </Route>
      <Route path="/recommendations" element={<Navigate to="/teammates" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
