import { useAuth } from "@/contexts/AuthContext"
import { Search } from "lucide-react"

export default function Topbar() {
  const { user } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between px-8 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm border-b border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-4">
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search power metrics..." 
            className="h-9 w-64 rounded-xl bg-slate-100 dark:bg-slate-900 pl-10 pr-4 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3 pl-6 border-l border-slate-200 dark:border-slate-800">
          <div className="flex flex-col items-end">
            <span className="text-sm font-bold text-slate-900 dark:text-white capitalize">
              {user?.username}
            </span>
            <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
              Customer Account
            </span>
          </div>
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-emerald-600 shadow-md shadow-primary/20 flex items-center justify-center text-white font-bold">
            {user?.username?.[0].toUpperCase()}
          </div>
        </div>
      </div>
    </header>
  )
}
