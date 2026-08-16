import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { type CurrentUserPublic, UsersService } from "@/client"
import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
    let user: CurrentUserPublic
    try {
      ;({ data: user } = await UsersService.readUserMe())
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 401) {
        localStorage.removeItem("access_token")
        throw redirect({ to: "/login" })
      }
      throw error
    }
    if (user.must_change_password) {
      throw redirect({ to: "/change-password" })
    }
  },
})

function Layout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b bg-background px-4">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
        </header>
        <main className="flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
