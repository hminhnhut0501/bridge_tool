import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: process.env.VAULT_E2E_URL || "http://127.0.0.1:8787",
    screenshot: "off",
    trace: "off",
  },
});
