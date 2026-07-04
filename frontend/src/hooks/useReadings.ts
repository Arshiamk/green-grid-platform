import { useQuery } from "@tanstack/react-query"
import api from "@/api/axios"

export interface MeterReading {
  id: number
  meter: string
  meter_mpan: string
  reading_at: string
  value_kwh: string
  reading_type: "actual" | "estimated"
  created_at: string
}

const fetchReadings = async () => {
  // Ordered newest-first by the API (default ordering: -reading_at)
  const { data } = await api.get<MeterReading[]>("/metering/readings/")
  return data
}

export function useReadings() {
  return useQuery({
    queryKey: ["readings"],
    queryFn: fetchReadings,
  })
}
