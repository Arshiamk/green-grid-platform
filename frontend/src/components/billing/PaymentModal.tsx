import { useState, useEffect } from "react"
import { loadStripe } from "@stripe/stripe-js"
import { Elements, PaymentElement, useStripe, useElements } from "@stripe/react-stripe-js"
import api from "@/api/axios"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Replace with your publishable key (should be env var)
const stripePromise = loadStripe("pk_test_placeholder") 

interface CheckoutFormProps {
  billId: string
  onSuccess: () => void
  onCancel: () => void
}

function CheckoutForm({ onSuccess, onCancel }: CheckoutFormProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [message, setMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!stripe || !elements) return

    setIsLoading(true)

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/billing`,
      },
      redirect: "if_required", 
    })

    if (error) {
       setMessage(error.message ?? "An unexpected error occurred.")
    } else {
       // Payment succeeded!
       onSuccess()
    }

    setIsLoading(false)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <PaymentElement />
      {message && <div className="text-red-500 text-sm">{message}</div>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading || !stripe || !elements}>
          {isLoading ? "Processing..." : "Pay Now"}
        </Button>
      </div>
    </form>
  )
}

interface PaymentModalProps {
  billId: string
  amount: number
  isOpen: boolean
  onClose: () => void
}

export default function PaymentModal({ billId, amount, isOpen, onClose }: PaymentModalProps) {
  const [clientSecret, setClientSecret] = useState("")

  useEffect(() => {
    if (isOpen && billId) {
      // Create PaymentIntent
      api.post(`/billing/payments/create-intent/${billId}/`)
        .then((res: { data: { clientSecret: string } }) => setClientSecret(res.data.clientSecret))
        .catch((err: unknown) => console.error("Failed to init payment", err))
    }
  }, [isOpen, billId])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-md bg-background">
        <CardHeader>
          <CardTitle>Pay Bill</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 text-sm text-muted-foreground">
            Total to pay: <span className="font-bold text-foreground">£{amount.toFixed(2)}</span>
          </div>
          {clientSecret ? (
            <Elements stripe={stripePromise} options={{ clientSecret }}>
              <CheckoutForm 
                billId={billId} 
                onSuccess={() => {
                  alert("Payment Successful!");
                  onClose();
                  // TODO: Refresh bill list
                }} 
                onCancel={onClose} 
              />
            </Elements>
          ) : (
            <div>Loading payment details...</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
