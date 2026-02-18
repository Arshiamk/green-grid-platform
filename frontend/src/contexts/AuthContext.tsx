import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import api from "@/api/axios"

interface AuthContextType {
  token: string | null
  user: any | null
  login: (token: string, username: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"))
  const [user, setUser] = useState<any | null>(null)

  useEffect(() => {
    if (token) {
      // Decode token or fetch user profile? 
      // For now, just trust the token exists. 
      // Ideally we'd hit /api/me/ or decode JWT to get username.
      // We can persist username in localStorage too for UI.
      const username = localStorage.getItem("username")
      if (username) setUser({ username })
    }
  }, [token])

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

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
