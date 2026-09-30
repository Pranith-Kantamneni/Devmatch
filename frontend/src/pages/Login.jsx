import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Users, Code2, Zap } from 'lucide-react'
import Logo from '../components/Logo'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function Login() {
  const { login } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      toast('Welcome back')
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
            Find your next
            <span className="auth-headline-accent"> hackathon team</span>
          </h1>
          <p className="auth-sub">
            Log in to discover developers whose skills complement yours and start
            building together.
          </p>
          <div className="auth-features">
            <div className="auth-feature">
              <div className="auth-feature-icon"><Users size={18} /></div>
              <div>
                <p className="auth-feature-title">Teammate matching</p>
                <p className="auth-feature-desc">Ranked by how well developers complement your skills</p>
              </div>
            </div>
            <div className="auth-feature">
              <div className="auth-feature-icon"><Code2 size={18} /></div>
              <div>
                <p className="auth-feature-title">Skill-based profiles</p>
                <p className="auth-feature-desc">Your real tech stack shapes your matches</p>
              </div>
            </div>
            <div className="auth-feature">
              <div className="auth-feature-icon"><Zap size={18} /></div>
              <div>
                <p className="auth-feature-title">Built for hackathons</p>
                <p className="auth-feature-desc">Form teams fast, before the clock runs out</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="auth-panel">
        <div className="auth-card">
          <h2 className="auth-title">Welcome back</h2>
          <p className="auth-card-sub">Log in to find your teammates</p>

          <form onSubmit={handleSubmit} className="auth-form">
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
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            {error && <div className="auth-error">{error}</div>}
            <Button type="submit" loading={loading} className="auth-submit">
              Log in <ArrowRight size={16} />
            </Button>
          </form>

          <p className="auth-switch">
            New to DevMatch?{' '}
            <Link to="/register" className="auth-link">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
