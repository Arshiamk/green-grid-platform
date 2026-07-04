import { useMemo, useState } from "react"
import { useBills, isOutstanding } from "@/hooks/useBills"
import { useReadings } from "@/hooks/useReadings"
import { useAnomalies, AnomalySeverity } from "@/hooks/useAnomalies"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { TrendingDown, TrendingUp, Wallet, Zap, Receipt } from "lucide-react"
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

const severityStyles: Record<AnomalySeverity, string> = {
  critical: "bg-red-500",
  warning: "bg-amber-500",
  info: "bg-blue-500",
}

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`

export default function Dashboard() {
  const { data: bills, isLoading: isLoadingBills } = useBills()
  const { data: readings, isLoading: isLoadingReadings } = useReadings()
  const { data: anomalies, isLoading: isLoadingAnomalies } = useAnomalies()
  const [rangeDays, setRangeDays] = useState<7 | 30>(7)

  const outstandingBills = bills?.filter(isOutstanding) ?? []
  const outstandingBalance = outstandingBills
    .reduce((sum, b) => sum + parseFloat(b.total_pounds), 0)
    .toFixed(2)

  // Month-to-date usage vs the same day range last month (real readings only)
  const now = new Date()
  const monthToDateKwh = (monthOffset: number) => {
    const target = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1)
    return (readings ?? [])
      .filter((r) => {
        const t = new Date(r.reading_at)
        return (
          t.getFullYear() === target.getFullYear() &&
          t.getMonth() === target.getMonth() &&
          t.getDate() <= now.getDate()
        )
      })
      .reduce((sum, r) => sum + parseFloat(r.value_kwh), 0)
  }
  const usageThisMonth = monthToDateKwh(0)
  const usageLastMonth = monthToDateKwh(-1)
  const monthDeltaPct =
    usageLastMonth > 0
      ? ((usageThisMonth - usageLastMonth) / usageLastMonth) * 100
      : null

  // Latest bill (API returns bills newest period first)
  const latestBill = bills?.[0]

  // Daily consumption totals for the selected range
  const chartData = useMemo(() => {
    if (!readings?.length) return []
    const totals = new Map<string, number>()
    for (const r of readings) {
      const key = dayKey(new Date(r.reading_at))
      totals.set(key, (totals.get(key) ?? 0) + parseFloat(r.value_kwh))
    }
    const today = new Date()
    const days = []
    for (let i = rangeDays - 1; i >= 0; i--) {
      const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - i)
      days.push({
        date: d.toLocaleDateString(
          "en-GB",
          rangeDays === 7 ? { weekday: "short" } : { day: "numeric", month: "short" },
        ),
        usage: Number((totals.get(dayKey(d)) ?? 0).toFixed(2)),
      })
    }
    return days
  }, [readings, rangeDays])

  const recentAlerts = anomalies?.slice(0, 4) ?? []

  if (isLoadingBills || isLoadingReadings || isLoadingAnomalies) {
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
              <div className="text-3xl font-bold heading-display">£{outstandingBalance}</div>
              <div className="mt-2 flex items-center text-xs font-semibold text-slate-400">
                <span>
                  {outstandingBills.length} unpaid {outstandingBills.length === 1 ? "bill" : "bills"}
                </span>
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
              <div className="text-3xl font-bold heading-display">{usageThisMonth.toFixed(1)} kWh</div>
              {monthDeltaPct !== null ? (
                <div
                  className={`mt-2 flex items-center text-xs font-semibold ${
                    monthDeltaPct > 0 ? "text-orange-500" : "text-emerald-500"
                  }`}
                >
                  {monthDeltaPct > 0 ? (
                    <TrendingUp className="mr-1 h-3 w-3" />
                  ) : (
                    <TrendingDown className="mr-1 h-3 w-3" />
                  )}
                  <span>
                    {monthDeltaPct > 0 ? "+" : ""}
                    {monthDeltaPct.toFixed(1)}% vs same period last month
                  </span>
                </div>
              ) : (
                <div className="mt-2 text-xs font-semibold text-slate-400">
                  No data for last month yet
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="glass relative overflow-hidden border-none transition-all hover:shadow-2xl">
            <div className="absolute right-[-20px] top-[-20px] h-24 w-24 rounded-full bg-blue-500/5" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Latest Bill</CardTitle>
              <div className="rounded-xl bg-blue-100 dark:bg-blue-500/10 p-2 text-blue-600 dark:text-blue-400">
                <Receipt className="h-5 w-5" />
              </div>
            </CardHeader>
            <CardContent>
              {latestBill ? (
                <>
                  <div className="text-3xl font-bold heading-display">£{latestBill.total_pounds}</div>
                  <div className="mt-2 text-xs font-semibold text-slate-400">
                    {new Date(latestBill.period_start).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                    {" – "}
                    {new Date(latestBill.period_end).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                    {" · "}
                    <span className="capitalize">{latestBill.status}</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="text-3xl font-bold heading-display">—</div>
                  <div className="mt-2 text-xs font-semibold text-slate-400">No bills issued yet</div>
                </>
              )}
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
                <p className="text-xs text-slate-500 font-medium">Total kWh per day from your meter readings</p>
              </div>
              <select
                className="text-xs font-bold bg-slate-100 dark:bg-slate-900 border-none rounded-lg p-2 outline-none"
                value={rangeDays}
                onChange={(e) => setRangeDays(Number(e.target.value) === 30 ? 30 : 7)}
              >
                <option value={7}>Last 7 Days</option>
                <option value={30}>Last 30 Days</option>
              </select>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-[280px] w-full">
              {chartData.length > 0 ? (
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
                      interval={rangeDays === 7 ? 0 : "preserveStartEnd"}
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
              <CardTitle className="text-xl font-bold tracking-tight">Meter Alerts</CardTitle>
              <p className="text-xs text-slate-500 font-medium">Anomalies detected in your readings</p>
          </CardHeader>
          <CardContent>
            {recentAlerts.length > 0 ? (
              <div className="space-y-6">
                {recentAlerts.map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`h-2 w-2 shrink-0 rounded-full ${severityStyles[alert.severity]} shadow-[0_0_8px_rgba(0,0,0,0.2)]`} />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold text-slate-700 dark:text-slate-300">{alert.title}</p>
                        <p className="text-[10px] font-medium text-slate-400">
                          {new Date(alert.detected_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                        </p>
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] font-extrabold uppercase tracking-widest text-slate-400">
                      {alert.is_resolved ? "Resolved" : alert.severity}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex h-[200px] flex-col items-center justify-center text-center">
                <p className="text-sm font-bold text-slate-700 dark:text-slate-300">All clear</p>
                <p className="mt-1 text-xs font-medium text-slate-400">
                  No anomalies detected in your meter data.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}
