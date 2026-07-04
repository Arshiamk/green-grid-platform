import { useCustomer } from "@/hooks/useCustomer"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default function Profile() {
  const { data: customer, isLoading } = useCustomer()

  if (isLoading) return <div>Loading profile...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Profile</h2>
      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
          <CardDescription>Your customer account information.</CardDescription>
        </CardHeader>
        <CardContent>
          {customer ? (
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Account Number</dt>
                <dd className="mt-1 font-medium">{customer.account_number}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Name</dt>
                <dd className="mt-1 font-medium">{customer.first_name} {customer.last_name}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Email</dt>
                <dd className="mt-1 font-medium">{customer.email}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Phone</dt>
                <dd className="mt-1 font-medium">{customer.phone || "—"}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-muted-foreground">
              No customer record is linked to this login yet.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
