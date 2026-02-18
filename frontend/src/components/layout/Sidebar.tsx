import { NavLink, useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "@/contexts/AuthContext"
import { LayoutDashboard, Receipt, Zap, User, LogOut, ChevronRight } from "lucide-react"
import { motion } from "framer-motion"

export default function Sidebar() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  const links = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/billing", icon: Receipt, label: "Billing" },
    { to: "/meters", icon: Zap, label: "Meters" },
    { to: "/profile", icon: User, label: "Profile" },
  ]

  return (
    <div className="flex h-screen w-72 flex-col bg-slate-50/50 dark:bg-slate-950/50 p-4 transition-all lg:flex">
      <div className="mb-8 flex h-14 items-center px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20 text-white">
            <Zap className="h-5 w-5 fill-current" />
          </div>
          <span className="heading-display text-xl font-bold tracking-tight text-slate-900 dark:text-white">
            Green<span className="text-primary">Grid</span>
          </span>
        </div>
      </div>

      <nav className="flex-1 space-y-2">
        {links.map((link) => {
          const isActive = location.pathname === link.to;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={`group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all ${
                isActive
                  ? "bg-white text-primary shadow-sm dark:bg-slate-900"
                  : "text-slate-500 hover:bg-white/50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900/50 dark:hover:text-slate-200"
              }`}
            >
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg transition-all ${
                isActive ? "bg-primary/10 text-primary" : "text-slate-400 group-hover:text-slate-600"
              }`}>
                <link.icon className="h-4.5 w-4.5" />
              </div>
              <span className="flex-1">{link.label}</span>
              {isActive && (
                <motion.div 
                  layoutId="sidebar-active"
                  className="absolute left-0 h-6 w-1 rounded-r-full bg-primary"
                />
              )}
              <ChevronRight className={`h-4 w-4 opacity-0 transition-all ${isActive ? "opacity-0" : "group-hover:translate-x-1 group-hover:opacity-100"}`} />
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-auto pt-4 border-t border-slate-200 dark:border-slate-800">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-500 hover:bg-destructive/10 hover:text-destructive transition-all"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-900 text-slate-400 group-hover:text-destructive">
            <LogOut className="h-4 w-4" />
          </div>
          Logout
        </button>
      </div>
    </div>
  )
}
