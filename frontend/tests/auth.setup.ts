import { expect, test as setup } from "@playwright/test"
import {
  adminPassword,
  bootstrapAdminEmail,
  bootstrapAdminTemporaryPassword,
} from "./config.ts"

const authFile = "playwright/.auth/user.json"

setup("authenticate", async ({ page, request }) => {
  let currentPassword = adminPassword
  let loginResponse = await request.post("/api/v1/login/access-token", {
    form: { username: bootstrapAdminEmail, password: currentPassword },
  })

  if (!loginResponse.ok()) {
    currentPassword = bootstrapAdminTemporaryPassword
    loginResponse = await request.post("/api/v1/login/access-token", {
      form: { username: bootstrapAdminEmail, password: currentPassword },
    })
  }

  expect(loginResponse.ok()).toBeTruthy()
  const { access_token: accessToken } = await loginResponse.json()

  if (currentPassword !== adminPassword) {
    const passwordResponse = await request.patch("/api/v1/users/me/password", {
      headers: { Authorization: `Bearer ${accessToken}` },
      data: {
        current_password: currentPassword,
        new_password: adminPassword,
      },
    })
    expect(passwordResponse.ok()).toBeTruthy()
  }

  await page.goto("/login")
  await page.evaluate(
    (token) => localStorage.setItem("access_token", token),
    accessToken,
  )
  await page.goto("/")
  await page.waitForURL("/")
  await page.context().storageState({ path: authFile })
})
