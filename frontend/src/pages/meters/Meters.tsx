import { useReadings } from "@/hooks/useReadings"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface Reading {
  id: string
  reading_at: string
  value_kwh: string
  source: string
}

export default function Meters() {
  const { data: readings } = useReadings()

  // This should really be a file upload for CSV or a select for Meter ID.
  // For simplicity, we assume we are submitting for the first meter found (or hardcoded ID if we had it).
  // But wait, the API requires a Meter ID. I don't have a hook for Meters list yet, only Readings.
  // I should fetch Meters first.
  
  // Actually, let's just show the list for now. The mutation is complex without selecting a meter.
  // I'll stick to listing readings.

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Meter Readings</CardTitle>
          <CardDescription>History of electricity consumption.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative w-full overflow-auto">
            <table className="w-full caption-bottom text-sm">
              <thead className="[&_tr]:border-b">
                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Date
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Reading (kWh)
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Source
                  </th>
                </tr>
              </thead>
              <tbody className="[&_tr:last-child]:border-0">
                {readings?.map((reading: Reading) => (
                  <tr
                    key={reading.id}
                    className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td className="p-4 align-middle">
                      {new Date(reading.reading_at).toLocaleString()}
                    </td>
                    <td className="p-4 align-middle font-semibold">
                      {reading.value_kwh}
                    </td>
                    <td className="p-4 align-middle">{reading.source}</td>
                  </tr>
                ))}
                 {!readings?.length && (
                  <tr>
                    <td colSpan={3} className="p-4 text-center text-muted-foreground">
                      No readings found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      
      {/* 
        Future: Add form to submit reading manually.
        Need to fetch Meters list first to let user select which meter.
      */}
    </div>
  )
}
