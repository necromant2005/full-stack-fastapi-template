import { type APIRequestContext, expect, test } from "@playwright/test"

import { adminPassword, bootstrapAdminEmail } from "./config"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

async function createManager(request: APIRequestContext) {
  const email = randomEmail()
  const temporaryPassword = randomPassword()
  const password = randomPassword()
  const adminLogin = await request.post("/api/v1/login/access-token", {
    form: { username: bootstrapAdminEmail, password: adminPassword },
  })
  expect(adminLogin.ok()).toBeTruthy()
  const { access_token: adminToken } = await adminLogin.json()

  const createResponse = await request.post("/api/v1/users/", {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: { email, password: temporaryPassword, role: "manager" },
  })
  expect(createResponse.ok()).toBeTruthy()

  const managerLogin = await request.post("/api/v1/login/access-token", {
    form: { username: email, password: temporaryPassword },
  })
  expect(managerLogin.ok()).toBeTruthy()
  const { access_token: managerToken } = await managerLogin.json()
  const passwordResponse = await request.patch("/api/v1/users/me/password", {
    headers: { Authorization: `Bearer ${managerToken}` },
    data: {
      current_password: temporaryPassword,
      new_password: password,
    },
  })
  expect(passwordResponse.ok()).toBeTruthy()

  return { email, password }
}

test.describe("Role-aware navigation", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("member sees no privileged navigation and gets access denied", async ({
    page,
    request,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    const signup = await request.post("/api/v1/users/signup", {
      data: { email, password, full_name: "Test Member" },
    })
    expect(signup.ok()).toBeTruthy()
    await logInUser(page, email, password)

    await expect(page.getByRole("link", { name: "Users" })).toHaveCount(0)
    await expect(page.getByRole("link", { name: "Metrics" })).toHaveCount(0)

    await page.goto("/users")
    await expect(
      page.getByRole("heading", { name: "Access denied" }),
    ).toBeVisible()
    await page.goto("/metrics")
    await expect(
      page.getByRole("heading", { name: "Access denied" }),
    ).toBeVisible()
  })

  test("manager can read users and metrics without mutation controls", async ({
    page,
    request,
  }) => {
    const manager = await createManager(request)
    await logInUser(page, manager.email, manager.password)

    await expect(page.getByRole("link", { name: "Users" })).toBeVisible()
    await expect(page.getByRole("link", { name: "Metrics" })).toBeVisible()

    await page.goto("/users")
    await expect(page.getByText("View user accounts")).toBeVisible()
    await expect(page.getByRole("button", { name: "Add User" })).toHaveCount(0)

    await page.goto("/metrics")
    await expect(page.getByRole("heading", { name: "Metrics" })).toBeVisible()
    await expect(page.getByText("Total users")).toBeVisible()
  })
})

test("administrator can open metrics", async ({ page }) => {
  await page.goto("/metrics")
  await expect(page.getByRole("heading", { name: "Metrics" })).toBeVisible()
  await expect(page.getByText("Active users")).toBeVisible()
})
