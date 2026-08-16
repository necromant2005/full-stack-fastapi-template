import { Link } from "@tanstack/react-router"
import { ShieldX } from "lucide-react"

import { Button } from "@/components/ui/button"

const AccessDenied = () => (
  <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
    <ShieldX className="size-14 text-destructive" aria-hidden="true" />
    <div>
      <h1 className="text-2xl font-bold">Access denied</h1>
      <p className="mt-2 text-muted-foreground">
        Your account does not have permission to view this page.
      </p>
    </div>
    <Button asChild>
      <Link to="/">Return to dashboard</Link>
    </Button>
  </div>
)

export default AccessDenied
