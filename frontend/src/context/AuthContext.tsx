import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { loginUser, registerUser } from '../services/api'

type User = { email: string; name?: string }
type AuthContextValue = {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('plagiarism_user')
    return saved ? JSON.parse(saved) as User : null
  })

  const saveUser = (next: User) => {
    setUser(next)
    localStorage.setItem('plagiarism_user', JSON.stringify(next))
  }

  useEffect(() => {
    const expireSession = () => setUser(null)
    window.addEventListener('plagiarism:session-expired', expireSession)
    return () => window.removeEventListener('plagiarism:session-expired', expireSession)
  }, [])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isAuthenticated: Boolean(user),
    async login(email, password) {
      const response = await loginUser(email, password)
      const token = response.access_token
      if (token) localStorage.setItem('plagiarism_token', token)
      saveUser({ email, name: response.user?.name })
    },
    async register(name, email, password) {
      const response = await registerUser(name, email, password)
      if (response.access_token) localStorage.setItem('plagiarism_token', response.access_token)
      saveUser({ email, name })
    },
    logout() {
      localStorage.removeItem('plagiarism_token')
      localStorage.removeItem('plagiarism_user')
      setUser(null)
    },
  }), [user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
