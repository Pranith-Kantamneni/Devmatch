import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Users, Target, Zap } from 'lucide-react'
import Logo from '../components/Logo'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function Register() {
  const { register } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (username.length < 3) {
      setError('Username must be at least 3 characters')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading(true)
    try {
      await register(username, email, password)
      toast('Account created — welcome to DevMatch')
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-hero">
        <div className="auth-hero-content">
          <div className="auth-brand">
            <Logo size={36} />
            <span className="auth-brand-name">DevMatch</span>
          </div>
          <h1 className="auth-headline">
            Start forming your
            <span className="auth-headline-accent"> dream team</span>
          </h1>
          <p className="auth-sub">
            Create your developer profile, add your skills and projects, and let
            DevMatch surface the teammates worth building with.
          </p>
          <div className="auth-stats">
            <div className="auth-stat">
              <span className="auth-stat-value">Skill-based</span>
              <span className="auth-stat-label">vector matching</span>
            </div>
            <div className="auth-stat">
              <span className="auth-stat-value">Top-K</span>
              <span className="auth-stat-label">ranked teammates</span>
            </div>
            <div className="auth-stat">
              <span className="auth-stat-value">Fast</span>
              <span className="auth-stat-label">team formation</span>
            </div>
          </div>
        </div>
      </div>

      <div className="auth-panel">
        <div className="auth-card">
          <h2 className="auth-title">Create your account</h2>
          <p className="auth-card-sub">It only takes a minute</p>

          <form onSubmit={handleSubmit} className="auth-form">
            <Input
              label="Username"
              name="username"
              placeholder="e.g. ada_lovelace"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
            <Input
              label="Email"
              name="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
            <Input
              label="Password"
              name="password"
              type="password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              hint="Must be at least 8 characters"
            />
            {error && <div className="auth-error">{error}</div>}
            <Button type="submit" loading={loading} className="auth-submit">
              Create account <ArrowRight size={16} />
            </Button>
          </form>

          <p className="auth-switch">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
