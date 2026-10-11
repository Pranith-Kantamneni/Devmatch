import { useEffect, useState } from 'react'
import { Settings2 } from 'lucide-react'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

const PROVIDER_META = {
  google: { label: 'Google', badge: 'G' },
  github: { label: 'GitHub', badge: 'GH' },
  linkedin: { label: 'LinkedIn', badge: 'in' },
}

const PROVIDER_ORDER = ['google', 'github', 'linkedin']

function setupHint(provider) {
  const label = PROVIDER_META[provider]?.label || provider
  return (
    `${label} login isn't connected yet. ` +
    'Add the provider client ID and secret to the server .env to enable it.'
  )
}

export default function SocialLoginButtons({ from = '/home' }) {
  const { toast } = useToast()
  const [statusByProvider, setStatusByProvider] = useState({})
  const [loadingProvider, setLoadingProvider] = useState(null)

  useEffect(() => {
    api
      .getOAuthProviders()
      .then((list) => {
        const map = {}
        for (const p of list) map[p.provider] = p.enabled
        setStatusByProvider(map)
      })
      .catch(() => setStatusByProvider({}))
  }, [])

  const handleClick = async (provider) => {
    if (statusByProvider[provider] === false) {
      toast(setupHint(provider), 'error')
      return
    }
    setLoadingProvider(provider)
    try {
      const { authorization_url } = await api.getOAuthLoginUrl(provider)
      // Remember the provider + destination across the third-party redirect.
      sessionStorage.setItem('devmatch_oauth_provider', provider)
      sessionStorage.setItem('devmatch_oauth_from', from)
      window.location.href = authorization_url
    } catch (err) {
      toast(err.message, 'error')
      setLoadingProvider(null)
    }
  }

  return (
    <div className="social-login">
      <div className="social-divider">
        <span>or continue with</span>
      </div>
      <div className="social-buttons">
        {PROVIDER_ORDER.map((provider) => {
          const enabled = statusByProvider[provider] !== false
          return (
            <button
              key={provider}
              type="button"
              className={`btn btn-secondary social-btn ${enabled ? '' : 'social-btn-off'}`}
              disabled={loadingProvider !== null}
              onClick={() => handleClick(provider)}
              title={enabled ? `Continue with ${PROVIDER_META[provider].label}` : setupHint(provider)}
            >
              <span className={`social-badge social-${provider}`} aria-hidden="true">
                {PROVIDER_META[provider]?.badge || provider[0].toUpperCase()}
              </span>
              {loadingProvider === provider
                ? 'Redirecting…'
                : `Continue with ${PROVIDER_META[provider]?.label || provider}`}
              {!enabled && (
                <span className="social-setup-tag">
                  <Settings2 size={12} /> Setup
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
