import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function OAuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { loginWithToken } = useAuth()
  const { toast } = useToast()
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      // The provider redirects to its own callback URL which serves this
      // page; the provider name was stashed before leaving.
      const provider =
        sessionStorage.getItem('devmatch_oauth_provider') || 'google'
      const code = searchParams.get('code')
      const state = searchParams.get('state')
      const providerError =
        searchParams.get('error_description') || searchParams.get('error')
      if (providerError) {
        if (!cancelled) setError(providerError)
        return
      }
      if (!code || !state) {
        if (!cancelled) setError('Social login was interrupted. Please try again.')
        return
      }
      try {
        const res = await api.completeOAuthLogin(provider, { code, state })
        const from = sessionStorage.getItem('devmatch_oauth_from') || '/home'
        sessionStorage.removeItem('devmatch_oauth_provider')
        sessionStorage.removeItem('devmatch_oauth_from')
        await loginWithToken(res.access_token)
        if (!cancelled) {
          toast('Welcome to DevMatch')
          navigate(from, { replace: true })
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Social login failed')
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [searchParams, loginWithToken, navigate, toast])

  if (error) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h2 className="auth-title">Sign-in failed</h2>
          <p className="auth-card-sub">{error}</p>
          <div className="empty-action">
            <Link to="/login" className="btn btn-secondary">
              Back to login
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="skeleton" style={{ width: 200, height: 24, marginBottom: 16 }} />
        <div className="skeleton" style={{ width: '100%', height: 16, marginBottom: 10 }} />
        <div className="skeleton" style={{ width: '70%', height: 16 }} />
        <p className="auth-card-sub" style={{ marginTop: 16 }}>
          Completing sign-in…
        </p>
      </div>
    </div>
  )
}
