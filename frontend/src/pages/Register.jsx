import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Users, Target, Zap } from 'lucide-react'
import Logo from '../components/Logo'
import SocialLoginButtons from '../components/SocialLoginButtons'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function Register() {
  const { register } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/home'

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const trimmedUsername = username.trim()
    const trimmedEmail = email.trim()
    if (trimmedUsername.length < 3) {
      setError('Username must be at least 3 characters')
      return
    }
    if (!/^[a-zA-Z0-9_.-]+$/.test(trimmedUsername)) {
      setError('Username may only contain letters, numbers, dots, dashes, and underscores')
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setError('Enter a valid email address')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)
    try {
      await register(trimmedUsername, trimmedEmail, password)
      toast('Account created — welcome to DevMatch')
      navigate(from, { replace: true })
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
            <span className="auth-brand-name">Dev<span className="brand-accent">Match</span></span>
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
              autoFocus
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
              type={showPassword ? 'text' : 'password'}
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              hint="Must be at least 8 characters"
              minLength={8}
            />
            <label className="auth-show-password">
              <input
                type="checkbox"
                checked={showPassword}
                onChange={(e) => setShowPassword(e.target.checked)}
              />
              Show password
            </label>
            <Input
              label="Confirm password"
              name="confirmPassword"
              type={showConfirm ? 'text' : 'password'}
              placeholder="Repeat your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
            <label className="auth-show-password">
              <input
                type="checkbox"
                checked={showConfirm}
                onChange={(e) => setShowConfirm(e.target.checked)}
              />
              Show confirm password
            </label>
            {error && <div className="auth-error" role="alert">{error}</div>}
            <Button type="submit" loading={loading} className="auth-submit">
              Create account <ArrowRight size={16} />
            </Button>
          </form>

          <SocialLoginButtons from={from} />

          <p className="auth-switch">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
