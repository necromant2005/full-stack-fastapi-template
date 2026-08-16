import path from "node:path"
import { fileURLToPath } from "node:url"
import dotenv from "dotenv"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

dotenv.config({ path: path.join(__dirname, "../../.env") })

function getEnvVar(name: string): string {
  const value = process.env[name]
  if (!value) {
    throw new Error(`Environment variable ${name} is undefined`)
  }
  return value
}

export const bootstrapAdminEmail = getEnvVar("BOOTSTRAP_ADMIN_EMAIL")
export const bootstrapAdminTemporaryPassword = getEnvVar(
  "BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD",
)
export const adminPassword =
  process.env.E2E_ADMIN_PASSWORD ?? "Admin-test-password-123!"
