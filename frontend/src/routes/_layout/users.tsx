import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { type UserPublic, UsersService } from "@/client"
import AccessDenied from "@/components/Common/AccessDenied"
import { DataTable } from "@/components/Common/DataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import AddUser from "@/components/Users/AddUser"
import { columns, type UserTableData } from "@/components/Users/columns"
import useAuth from "@/hooks/useAuth"

function getUsersQueryOptions() {
  return {
    queryFn: async () =>
      (await UsersService.readUsers({ query: { skip: 0, limit: 100 } })).data,
    queryKey: ["users"],
  }
}

export const Route = createFileRoute("/_layout/users")({
  component: UsersRoute,
  head: () => ({
    meta: [{ title: "Users - FastAPI Template" }],
  }),
})

function UsersTableContent() {
  const { user: currentUser, can } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())
  const canManageUsers = can("users:update_any")
  const visibleColumns = canManageUsers
    ? columns
    : columns.filter((column) => column.id !== "actions")

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return <DataTable columns={visibleColumns} data={tableData} />
}

function UsersPage() {
  const { can } = useAuth()

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">
            {can("users:create")
              ? "Manage user accounts and permissions"
              : "View user accounts"}
          </p>
        </div>
        {can("users:create") && <AddUser />}
      </div>
      <Suspense fallback={<PendingUsers />}>
        <UsersTableContent />
      </Suspense>
    </div>
  )
}

function UsersRoute() {
  const { user, can } = useAuth()
  if (!user) return null
  if (!can("users:list")) return <AccessDenied />
  return <UsersPage />
}
