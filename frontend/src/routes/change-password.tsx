import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"

import { UsersService } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import ChangePassword from "@/components/UserSettings/ChangePassword"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/change-password")({
  component: InitialPasswordChange,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({ to: "/login" })
    }
    const { data: user } = await UsersService.readUserMe()
    if (!user.must_change_password) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Set Your Password - FastAPI Template" }],
  }),
})

function InitialPasswordChange() {
  const navigate = useNavigate()

  return (
    <AuthLayout>
      <div className="flex flex-col gap-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Choose a new password</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Replace your temporary password before continuing.
          </p>
        </div>
        <ChangePassword onSuccess={() => navigate({ to: "/" })} />
      </div>
    </AuthLayout>
  )
}
