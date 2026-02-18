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
  const { data } = await api.get<{ results: Customer[] }>("/customers/")
  // Assuming the user has only one customer profile linked
  return data.results[0]
}

export function useCustomer() {
  return useQuery({
    queryKey: ["customer"],
    queryFn: fetchCustomer,
  })
}
