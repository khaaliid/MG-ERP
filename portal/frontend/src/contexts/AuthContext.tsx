import React, { createContext, useContext, useEffect, useState } from 'react'

interface User {
  id: number
  email: string
  username?: string
  full_name?: string
  role?: string
  is_active: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    if (!savedToken) { setIsLoading(false); return }
    ;(async () => {
      try {
        const resp = await fetch(`${import.meta.env.VITE_AUTH_BASE_URL}/api/v1/auth/profile`, {
          headers: { Authorization: `Bearer ${savedToken}` }
        })
        if (resp.ok) {
          const u = await resp.json()
          setToken(savedToken)
          setUser(u)
          localStorage.setItem('auth_user', JSON.stringify(u))
        } else {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_user')
        }
      } finally {
        setIsLoading(false)
      }
    })()
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true)
    try {
      const resp = await fetch(`${import.meta.env.VITE_AUTH_BASE_URL}/api/v1/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      if (!resp.ok) return false
      const tokens = await resp.json() as { access_token: string }
      const prof = await fetch(`${import.meta.env.VITE_AUTH_BASE_URL}/api/v1/auth/profile`, {
        headers: { Authorization: `Bearer ${tokens.access_token}` }
      })
      if (!prof.ok) return false
      const u = await prof.json()
      setToken(tokens.access_token)
      setUser(u)
      localStorage.setItem('auth_token', tokens.access_token)
      localStorage.setItem('auth_user', JSON.stringify(u))
      return true
    } catch {
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  const value: AuthContextType = { user, token, login, logout, isLoading }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
