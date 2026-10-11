import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { api, setToken, getToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [authError, setAuthError] = useState(null)

  useEffect(() => {
    if (!getToken()) {
      setLoading(false)
      return
    }
    api
      .getMe()
      .then((me) => {
        setUser(me)
        setAuthError(null)
      })
      .catch((err) => {
        // Only a 401 means the token is bad. Network/500 errors must not
        // silently log the user out — surface them instead.
        if (err?.status === 401) {
          setToken(null)
          setUser(null)
        } else {
          setAuthError(err?.message || 'Could not reach the server')
        }
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const handleUnauthorized = () => setUser(null)
    window.addEventListener('devmatch:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('devmatch:unauthorized', handleUnauthorized)
  }, [])

  const login = useCallback(async (email, password) => {
    try {
      const res = await api.login({ email, password })
      setToken(res.access_token)
      try {
        const me = await api.getMe()
        setUser(me)
        setAuthError(null)
        return me
      } catch (err) {
        // Token is valid but profile fetch failed — don't leave a half-auth
        // state; roll back so the user can retry cleanly.
        setToken(null)
        setUser(null)
        throw err
      }
    } catch (err) {
      setUser(null)
      throw err
    }
  }, [])

  const register = useCallback(async (username, email, password) => {
    await api.register({ username, email, password })
    return login(email, password)
  }, [login])

  // Used after OAuth callbacks: the backend already verified the identity.
  const loginWithToken = useCallback(async (accessToken) => {
    setToken(accessToken)
    try {
      const me = await api.getMe()
      setUser(me)
      setAuthError(null)
      return me
    } catch (err) {
      setToken(null)
      setUser(null)
      throw err
    }
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, authError, retryAuth: () => window.location.reload(), login, register, loginWithToken, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
