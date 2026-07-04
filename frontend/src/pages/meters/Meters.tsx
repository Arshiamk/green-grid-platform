import { useReadings, MeterReading } from "@/hooks/useReadings"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default function Meters() {
  const { data: readings } = useReadings()

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
                    Meter
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Reading (kWh)
                  </th>
                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                    Type
                  </th>
                </tr>
              </thead>
              <tbody className="[&_tr:last-child]:border-0">
                {readings?.map((reading: MeterReading) => (
                  <tr
                    key={reading.id}
                    className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td className="p-4 align-middle">
                      {new Date(reading.reading_at).toLocaleString()}
                    </td>
                    <td className="p-4 align-middle">{reading.meter_mpan}</td>
                    <td className="p-4 align-middle font-semibold">
                      {reading.value_kwh}
                    </td>
                    <td className="p-4 align-middle capitalize">{reading.reading_type}</td>
                  </tr>
                ))}
                 {!readings?.length && (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-muted-foreground">
                      No readings found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
