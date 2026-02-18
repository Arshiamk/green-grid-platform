import { useBills } from "@/hooks/useBills"
import { useReadings } from "@/hooks/useReadings"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { TrendingUp, Wallet, Zap, Calendar, ArrowUpRight } from "lucide-react"
import { motion } from "framer-motion"

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
}

export default function Dashboard() {
  const { data: bills, isLoading: isLoadingBills } = useBills()
  const { data: readings, isLoading: isLoadingReadings } = useReadings()

  const currentBalance = bills
    ?.filter((b) => b.status !== "PAID")
    .reduce((sum, b) => sum + parseFloat(b.total_amount), 0)
    .toFixed(2)

  const currentMonth = new Date().getMonth()
  const usageThisMonth = readings
    ?.filter((r) => new Date(r.reading_at).getMonth() === currentMonth)
    .reduce((sum, r) => sum + parseFloat(r.value_kwh), 0)
    .toFixed(1)

  const chartData = readings
    ?.slice(0, 7)
    .map((r) => ({
      date: new Date(r.reading_at).toLocaleDateString("en-GB", { weekday: 'short' }),
      usage: parseFloat(r.value_kwh),
    }))
    .reverse()

  if (isLoadingBills || isLoadingReadings) {
    return (
      <div className="flex h-[400px] w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <motion.div 
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      <div className="flex flex-col gap-2">
        <h2 className="heading-display text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Overview
        </h2>
        <p className="text-slate-500">Welcome back. Here's what's happening today.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <motion.div variants={item}>
          <Card className="glass relative overflow-hidden border-none transition-all hover:shadow-2xl">
            <div className="absolute right-[-20px] top-[-20px] h-24 w-24 rounded-full bg-emerald-500/5" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Outstanding Balance</CardTitle>
              <div className="rounded-xl bg-orange-100 dark:bg-orange-500/10 p-2 text-orange-600 dark:text-orange-400">
                <Wallet className="h-5 w-5" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold heading-display">£{currentBalance || "0.00"}</div>
              <div className="mt-2 flex items-center text-xs font-semibold text-slate-400">
                <span className="capitalize">{bills?.length} pending invoices</span>
                <ArrowUpRight className="ml-1 h-3 w-3" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="glass relative overflow-hidden border-none transition-all hover:shadow-2xl">
            <div className="absolute right-[-20px] top-[-20px] h-24 w-24 rounded-full bg-primary/5" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Usage (This Month)</CardTitle>
              <div className="rounded-xl bg-emerald-100 dark:bg-emerald-500/10 p-2 text-emerald-600 dark:text-emerald-400">
                <Zap className="h-5 w-5 fill-current" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold heading-display">{usageThisMonth || "0"} kWh</div>
              <div className="mt-2 flex items-center text-xs font-semibold text-emerald-500">
                <TrendingUp className="mr-1 h-3 w-3" />
                <span>+2% from last month</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="glass relative overflow-hidden border-none transition-all hover:shadow-2xl">
            <div className="absolute right-[-20px] top-[-20px] h-24 w-24 rounded-full bg-blue-500/5" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Next Billing Cycle</CardTitle>
              <div className="rounded-xl bg-blue-100 dark:bg-blue-500/10 p-2 text-blue-600 dark:text-blue-400">
                <Calendar className="h-5 w-5" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold heading-display">March 1st</div>
              <div className="mt-2 text-xs font-semibold text-slate-400">
                Auto-generation scheduled
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div variants={item} className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <Card className="glass col-span-full border-none lg:col-span-4 p-2 shadow-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl font-bold tracking-tight">Consumption Trends</CardTitle>
                <p className="text-xs text-slate-500 font-medium">Daily kWh metrics for the current cycle</p>
              </div>
              <select className="text-xs font-bold bg-slate-100 dark:bg-slate-900 border-none rounded-lg p-2 outline-none">
                <option>Last 7 Days</option>
                <option>Last 30 Days</option>
              </select>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-[280px] w-full">
              {chartData && chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <defs>
                      <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={1} />
                        <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="date" 
                      fontSize={11} 
                      fontWeight={600}
                      tickLine={false} 
                      axisLine={false} 
                      tick={{ fill: 'currentColor', opacity: 0.5 }}
                    />
                    <YAxis 
                      fontSize={11} 
                      fontWeight={600}
                      tickLine={false} 
                      axisLine={false} 
                      tickFormatter={(value) => `${value}kWh`} 
                      tick={{ fill: 'currentColor', opacity: 0.5 }}
                    />
                    <Tooltip 
                      cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                      contentStyle={{ 
                        borderRadius: '12px', 
                        border: 'none', 
                        boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                        fontSize: '12px',
                        fontWeight: 'bold'
                      }}
                    />
                    <Bar dataKey="usage" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill="url(#barGradient)" />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-slate-400 font-medium text-sm">
                  No consumption data detected
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="glass col-span-full border-none lg:col-span-3 shadow-xl">
          <CardHeader>
              <CardTitle className="text-xl font-bold tracking-tight">Grid Health</CardTitle>
              <p className="text-xs text-slate-500 font-medium">Real-time infrastructure status</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {[
                { name: "South Grid Segment", status: "Optimal", color: "bg-emerald-500" },
                { name: "Central Hub", status: "Optimal", color: "bg-emerald-500" },
                { name: "Forecasting Engine", status: "Syncing", color: "bg-blue-500" },
                { name: "Billing Microservice", status: "Standby", color: "bg-slate-300 dark:bg-slate-700" }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`h-2 w-2 rounded-full ${item.color} shadow-[0_0_8px_rgba(0,0,0,0.2)]`} />
                    <span className="text-sm font-bold text-slate-700 dark:text-slate-300">{item.name}</span>
                  </div>
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">{item.status}</span>
                </div>
              ))}
              <div className="mt-4 rounded-xl bg-primary/5 p-4 text-center">
                <p className="text-xs font-bold text-primary">System load is 12% below average</p>
                <p className="mt-1 text-[10px] text-slate-400 font-medium">Auto-scaling currently inactive</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}
