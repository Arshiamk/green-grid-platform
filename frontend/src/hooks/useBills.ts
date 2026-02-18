import { useQuery } from "@tanstack/react-query"
import api from "@/api/axios"

export interface Bill {
  id: string
  customer: string
  period_start: string
  period_end: string
  total_amount: string
  status: "PENDING" | "PAID" | "OVERDUE"
  generated_at: string
}

const fetchBills = async () => {
  const { data } = await api.get<Bill[]>("/billing/bills/")
  return data
}

export function useBills() {
  return useQuery({
    queryKey: ["bills"],
    queryFn: fetchBills,
  })
}
