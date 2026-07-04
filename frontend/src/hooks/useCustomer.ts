import { useQuery } from "@tanstack/react-query"
import api from "@/api/axios"

export interface Customer {
  id: string
  account_number: string
  first_name: string
  last_name: string
  email: string
  phone: string
}

const fetchCustomer = async () => {
  // Non-staff users only ever see their own customer record
  const { data } = await api.get<Customer[]>("/customers/")
  return data[0] ?? null
}

export function useCustomer() {
  return useQuery({
    queryKey: ["customer"],
    queryFn: fetchCustomer,
  })
}
