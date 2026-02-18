import { useState } from "react"
import { useBills } from "@/hooks/useBills"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import PaymentModal from "@/components/billing/PaymentModal"

interface Bill {
  id: string
  period_start: string
  period_end: string
  total_amount: string
  status: string
  generated_at: string
}

export default function Billing() {
  const { data: bills, isLoading, refetch } = useBills()
  const [selectedBill, setSelectedBill] = useState<{ id: string; amount: number } | null>(null)

  if (isLoading) return <div>Loading bills...</div>

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
          <CardDescription>View all your past and current electricity bills.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative w-full overflow-auto">
            <table className="w-full caption-bottom text-sm">
              <thead className="[&_tr]:border-b">
                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Period
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Amount
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Date
                  </th>
                  <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="[&_tr:last-child]:border-0">
                {bills?.map((bill: Bill) => (
                  <tr
                    key={bill.id}
                    className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td className="p-4 align-middle">
                      {bill.period_start} - {bill.period_end}
                    </td>
                    <td className="p-4 align-middle font-semibold">
                      £{bill.total_amount}
                    </td>
                    <td className="p-4 align-middle">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-opacity-10 ${
                          bill.status === "PAID"
                            ? "bg-green-500 text-green-700"
                            : bill.status === "OVERDUE"
                            ? "bg-red-500 text-red-700"
                            : "bg-yellow-500 text-yellow-700"
                        }`}
                      >
                        {bill.status}
                      </span>
                    </td>
                    <td className="p-4 align-middle">
                      {new Date(bill.generated_at).toLocaleDateString()}
                    </td>
                    <td className="p-4 align-middle text-right space-x-2">
                       {/* Download PDF Button */}
                       <a 
                         href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/billing/bills/${bill.id}/pdf/`}
                         target="_blank"
                         rel="noopener noreferrer"
                       >
                         <Button variant="outline" size="sm">PDF</Button>
                       </a>

                       {/* Pay Button */}
                       {bill.status !== "PAID" && (
                         <Button 
                           size="sm" 
                           onClick={() => setSelectedBill({ id: bill.id, amount: parseFloat(bill.total_amount) })}
                         >
                           Pay
                         </Button>
                       )}
                    </td>
                  </tr>
                ))}
                {!bills?.length && (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-muted-foreground">
                      No bills found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Payment Modal */}
      {selectedBill && (
        <PaymentModal
          billId={selectedBill.id}
          amount={selectedBill.amount}
          isOpen={!!selectedBill}
          onClose={() => {
            setSelectedBill(null)
            refetch() // Refresh bills to see updated status (if we implemented webhook handling or optimistic update)
          }}
        />
      )}
    </div>
  )
}
