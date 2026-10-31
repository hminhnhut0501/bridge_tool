import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

test("Telegram wizard: API, phone, invalid OTP, 2FA, success and mobile", async ({
  page,
}) => {
  let state: any = {
    mode: "real",
    state: "not_configured",
    configured: false,
    step: "credentials",
    can_control: true,
    busy: false,
    retry_after: 0,
    send_after: 0,
  };
  const submitted: string[] = [];
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  // Only simulated auth routes; no Telegram API call or real OTP is sent.
  await page.route("**/api/telegram/**", async (route) => {
    const path = new URL(route.request().url()).pathname.split("/").at(-1);
    if (route.request().method() === "GET") {
      await route.fulfill({ json: state });
      return;
    }
    const body = route.request().postDataJSON();
    submitted.push(path!);
    if (path === "credentials") {
      expect(body.api_id).toBe(12345);
      expect(body.api_hash).toBe("a".repeat(32));
      state = {
        ...state,
        configured: true,
        step: "phone",
        state: "login_required",
      };
    } else if (path === "send-code") {
      expect(body.phone).toBe("+84901234567");
      state = { ...state, step: "code", phone: "••••4567" };
    } else if (path === "verify-code") {
      if (body.code === "00000") {
        await route.fulfill({
          status: 422,
          json: { detail: "Mã OTP chưa đúng" },
        });
        return;
      }
      state = { ...state, step: "password" };
    } else if (path === "verify-password") {
      expect(body.password).toBe("simulated-2fa-only");
      state = { ...state, step: "connected", state: "connected" };
    }
    await route.fulfill({ json: state });
  });
  const password = readFileSync(
    resolve(process.env.VAULT_E2E_ACCESS || "../data/local-access.txt"),
    "utf8",
  ).match(/^Password: (.+)$/m)![1];
  await page.goto("/");
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await page.getByRole("heading", { name: "Tổng quan Vault" }).waitFor();
  await page
    .getByRole("button", { name: "Kết nối Telegram", exact: true })
    .click();
  await page.getByLabel("API ID", { exact: true }).fill("12345");
  await page.getByLabel("API hash", { exact: true }).fill("a".repeat(32));
  await page.getByRole("button", { name: "Lưu API và tiếp tục" }).click();
  await page
    .getByLabel("Số điện thoại Telegram", { exact: true })
    .fill("+84901234567");
  await page
    .getByRole("button", { name: "Gửi mã đăng nhập", exact: true })
    .click();
  await page.getByLabel("Mã OTP", { exact: true }).fill("00000");
  await page.getByRole("button", { name: "Xác nhận mã OTP" }).click();
  await expect(page.getByText("Mã OTP chưa đúng")).toBeVisible();
  await page.getByLabel("Mã OTP", { exact: true }).fill("12345");
  await page.getByRole("button", { name: "Xác nhận mã OTP" }).click();
  await expect(
    page.getByRole("heading", { name: "Xác minh hai bước" }),
  ).toBeVisible();
  const directory = resolve(
    process.env.VAULT_E2E_SCREENSHOTS || "../data/screenshots",
  );
  mkdirSync(directory, { recursive: true });
  await page.screenshot({
    path: resolve(directory, "telegram-2fa-desktop.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: resolve(directory, "telegram-2fa-mobile.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    ),
  ).toBe(false);
  await page
    .getByLabel("Mật khẩu 2FA", { exact: true })
    .fill("simulated-2fa-only");
  await page
    .getByRole("button", { name: "Kết nối tài khoản", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Telegram đã kết nối" }),
  ).toBeVisible();
  expect(submitted).toEqual([
    "credentials",
    "send-code",
    "verify-code",
    "verify-code",
    "verify-password",
  ]);
  expect(errors).toEqual([]);
});
