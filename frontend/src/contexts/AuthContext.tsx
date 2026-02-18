import { createContext, useContext, useState, useEffect, ReactNode } from "react"

interface User {
  username: string
}

interface AuthContextType {
  token: string | null
  user: User | null
  login: (token: string, username: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"))
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const savedToken = localStorage.getItem("token")
    const savedUsername = localStorage.getItem("username")
    
    if (savedToken && !token) {
      setToken(savedToken)
    }
    
    if (savedUsername && !user) {
      setUser({ username: savedUsername })
    }
  }, [token, user])

  const login = (newToken: string, username: string) => {
    localStorage.setItem("token", newToken)
    localStorage.setItem("username", username)
    setToken(newToken)
    setUser({ username })
  }

  const logout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("username")
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
