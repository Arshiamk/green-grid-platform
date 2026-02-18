import { useQuery } from "@tanstack/react-query"
import api from "@/api/axios"

export interface MeterReading {
  id: string
  meter: string
  value_kwh: string
  reading_at: string
  source: string
}

const fetchReadings = async () => {
  const { data } = await api.get<MeterReading[]>("/metering/readings/")
  return data
}

export function useReadings() {
  return useQuery({
    queryKey: ["readings"],
    queryFn: fetchReadings,
  })
}
