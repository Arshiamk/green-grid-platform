import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider } from "@/contexts/AuthContext"
import ProtectedRoute from "@/components/ProtectedRoute"
import DashboardLayout from "@/components/layout/DashboardLayout"
import Login from "@/pages/auth/Login"
import Dashboard from "@/pages/dashboard/Dashboard"
import Billing from "@/pages/billing/Billing"
import Meters from "@/pages/meters/Meters"
import Profile from "@/pages/profile/Profile"

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/billing" element={<Billing />} />
                <Route path="/meters" element={<Meters />} />
                <Route path="/profile" element={<Profile />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
