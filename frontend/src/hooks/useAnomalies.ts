import { useQuery } from "@tanstack/react-query"
import api from "@/api/axios"

export type AnomalySeverity = "info" | "warning" | "critical"

export interface Anomaly {
  id: string
  meter: string
  meter_mpan: string
  anomaly_type: "spike" | "drop" | "gap" | "negative" | "flatline"
  severity: AnomalySeverity
  title: string
  description: string
  detected_at: string
  value_kwh: string | null
  expected_kwh: string | null
  is_resolved: boolean
  created_at: string
}

const fetchAnomalies = async () => {
  // Ordered newest-first by the API (default ordering: -detected_at)
  const { data } = await api.get<Anomaly[]>("/anomalies/")
  return data
}

export function useAnomalies() {
  return useQuery({
    queryKey: ["anomalies"],
    queryFn: fetchAnomalies,
  })
}
