import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import { MetricsService } from "@/client"
import AccessDenied from "@/components/Common/AccessDenied"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/metrics")({
  component: MetricsRoute,
  head: () => ({
    meta: [{ title: "Metrics - FastAPI Template" }],
  }),
})

function MetricsPage() {
  const { data: insights } = useQuery({
    queryKey: ["metrics", "insights"],
    queryFn: async () => (await MetricsService.readMetricsInsights()).data,
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Metrics</h1>
        <p className="text-muted-foreground">Current user insights</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total users</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">
            {insights?.total_users ?? "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Active users</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">
            {insights?.active_users ?? "—"}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function MetricsRoute() {
  const { user, can } = useAuth()
  if (!user) return null
  if (!can("metrics:view")) return <AccessDenied />
  return <MetricsPage />
}
