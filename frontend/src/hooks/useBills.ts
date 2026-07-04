import { useQuery } from "@tanstack/react-query"
import api from "@/api/axios"

export type BillStatus = "draft" | "issued" | "paid" | "void"

export interface Bill {
  id: string
  customer_account: string
  period_start: string
  period_end: string
  status: BillStatus
  total_kwh: string
  total_amount_pence: string
  total_pounds: string
  created_at: string
}

/** Statuses that still count towards the customer's outstanding balance. */
export const isOutstanding = (bill: Bill) =>
  bill.status === "draft" || bill.status === "issued"

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
