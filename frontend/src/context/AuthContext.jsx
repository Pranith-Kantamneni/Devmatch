import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { api, setToken, getToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!getToken()) {
      setLoading(false)
      return
    }
    api
      .getMe()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const handleUnauthorized = () => setUser(null)
    window.addEventListener('devmatch:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('devmatch:unauthorized', handleUnauthorized)
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.login({ email, password })
    setToken(res.access_token)
    const me = await api.getMe()
    setUser(me)
    return me
  }, [])

  const register = useCallback(async (username, email, password) => {
    await api.register({ username, email, password })
    return login(email, password)
  }, [login])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
