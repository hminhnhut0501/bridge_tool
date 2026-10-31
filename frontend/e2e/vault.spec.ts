import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

test("local UI: login, discovery, real crypt jobs, topics, settings, mobile", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const password = readFileSync(
    resolve(process.env.VAULT_E2E_ACCESS || "../data/local-access.txt"),
    "utf8",
  ).match(/^Password: (.+)$/m)![1];
  await page.goto("/");
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Tổng quan Vault" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Nguồn Telegram", exact: true })
    .click();
  await page.getByRole("button", { name: "Thêm nguồn", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  const discoveryRequests: string[] = [];
  const recordDiscovery = (request: any) => {
    if (request.url().includes("/api/discovery"))
      discoveryRequests.push(request.url());
  };
  page.on("request", recordDiscovery);
  await page.getByLabel("Link nguồn Telegram").fill("-1001002");
  await page
    .getByRole("checkbox", {
      name: "Tôi sở hữu nội dung hoặc có quyền sao chép nội dung của nguồn này.",
    })
    .check();
  await page.getByRole("button", { name: "Thêm và bắt đầu backup" }).click();
  await expect(
    page.getByRole("heading", { name: "Field Notes", exact: true }),
  ).toBeVisible();
  expect(discoveryRequests).toHaveLength(0);
  page.off("request", recordDiscovery);
  await page.getByRole("button", { name: "Thêm nguồn", exact: true }).click();
  await page
    .getByRole("button", { name: "Xem danh sách group/channel" })
    .click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("button", { name: "Local Video Archive" }),
  ).toBeDisabled();
  await page
    .getByRole("checkbox", {
      name: "Tôi sở hữu nội dung hoặc có quyền sao chép nội dung của nguồn này.",
    })
    .check();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Local Video Archive" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Local Video Archive", exact: true }),
  ).toBeVisible();
  const sourceScreenshotFolder =
    process.env.VAULT_E2E_SCREENSHOTS || "../data/reports/audit-web";
  mkdirSync(resolve(sourceScreenshotFolder), { recursive: true });
  await page.screenshot({
    path: resolve(sourceScreenshotFolder, "source-flow-desktop.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: resolve(sourceScreenshotFolder, "source-flow-mobile.png"),
    fullPage: true,
    animations: "disabled",
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.setViewportSize({ width: 1360, height: 900 });
  await page
    .getByRole("button", { name: "Topics", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Telegram Topics" }),
  ).toBeVisible();
  await page.getByRole("checkbox", { name: "Backup tất cả topics" }).uncheck();
  await expect(page.getByText("Studio clips", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Lưu lựa chọn" }).click();
  await expect(page.getByRole("status")).toContainText("Đã lưu topics");
  await page
    .getByRole("button", { name: "Nguồn Telegram", exact: true })
    .click();
  await page
    .getByRole("button", { name: /^(Tiếp tục|Bắt đầu backup)$/ })
    .first()
    .click();
  await page.getByRole("button", { name: "Cài đặt", exact: true }).click();
  await page.getByRole("checkbox", { name: "Bật nghỉ giữa các file" }).check();
  await page.getByRole("spinbutton", { name: "Nghỉ tối thiểu" }).fill("7");
  await page.getByRole("spinbutton", { name: "Nghỉ tối đa" }).fill("23");
  await page
    .getByRole("spinbutton", { name: "Số lần thử lại tối đa" })
    .fill("7");
  await page.getByRole("button", { name: "Lưu cài đặt" }).click();
  await expect(page.getByRole("status")).toContainText("Cài đặt đã lưu");
  await page.reload();
  await expect(
    page.getByRole("spinbutton", { name: "Số lần thử lại tối đa" }),
  ).toHaveValue("7");
  await expect(
    page.getByRole("spinbutton", { name: "Nghỉ tối thiểu" }),
  ).toHaveValue("7");
  await expect(
    page.getByRole("spinbutton", { name: "Nghỉ tối đa" }),
  ).toHaveValue("23");
  await page
    .getByRole("checkbox", { name: "Bật nghỉ giữa các file" })
    .uncheck();
  await page.getByRole("button", { name: "Lưu cài đặt" }).click();
  await expect
    .poll(
      async () =>
        (await (await page.request.get("/api/settings")).json())
          .file_pause_enabled,
    )
    .toBe(false);
  await page.getByRole("button", { name: "Lưu trữ", exact: true }).click();
  await expect(page.getByText("Mã hóa bật", { exact: true })).toHaveCount(3);
  await page
    .getByRole("button", { name: "Đối chiếu backup", exact: true })
    .click();
  await page.getByRole("button", { name: "Tổng quan", exact: true }).click();
  await expect
    .poll(
      async () => {
        const response = await page.request.get("/api/status");
        return (await response.json()).counts.COMPLETED?.count || 0;
      },
      { timeout: 45000 },
    )
    .toBeGreaterThan(0);
  await expect
    .poll(
      async () =>
        Number(
          await page.locator(".dashboard-metric.success > strong").innerText(),
        ),
      { timeout: 10000 },
    )
    .toBeGreaterThan(0);
  const closeToast = page.getByRole("button", { name: "Đóng thông báo" });
  if (await closeToast.isVisible()) await closeToast.click();
  const screenshotFolder =
    process.env.VAULT_E2E_SCREENSHOTS || "../data/screenshots";
  mkdirSync(resolve(screenshotFolder), { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1040 });
  await page.screenshot({
    path: resolve(screenshotFolder, "dashboard-desktop.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page
    .getByRole("button", { name: "Nguồn Telegram", exact: true })
    .click();
  await page.locator(".source-details > summary").first().click();
  await page
    .getByRole("button", { name: "Test video mới", exact: false })
    .first()
    .click();
  await expect(page.getByRole("status")).toContainText("event video mới");
  await page
    .getByRole("button", { name: "Thư viện backup", exact: true })
    .click();
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page
    .getByRole("button", { name: "Chi tiết job", exact: false })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toContainText("SHA-256");
  await page.getByRole("button", { name: "Đóng", exact: true }).click();
  await expect(page.locator("tbody .badge")).toHaveText(
    await page
      .locator("tbody .badge")
      .allTextContents()
      .then((labels) => labels.map(() => "Hoàn tất")),
  );
  await page
    .getByRole("button", { name: "Truyền & hàng đợi", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Tạm dừng tất cả", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Xác nhận", exact: true })
    .click();
  await expect
    .poll(
      async () =>
        (await (await page.request.get("/api/status")).json()).scheduler_paused,
    )
    .toBe(true);
  await page.screenshot({
    path: resolve(screenshotFolder, "queue-controls-desktop.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page
    .getByRole("button", { name: "Tiếp tục tất cả", exact: true })
    .click();
  await expect
    .poll(
      async () =>
        (await (await page.request.get("/api/status")).json()).scheduler_paused,
    )
    .toBe(false);
  const backupsBefore = (
    await (
      await page.request.get("/api/jobs?status=COMPLETED&limit=100")
    ).json()
  ).items.length;
  await page
    .getByRole("button", { name: "Quản lý phạm vi", exact: true })
    .click();
  await page
    .getByLabel("Phạm vi group", { exact: true })
    .selectOption({ label: "Local Video Archive" });
  await page
    .getByLabel("Phạm vi topic", { exact: true })
    .selectOption({ label: "General" });
  await page.getByRole("button", { name: "Hủy topic", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Xác nhận", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Hủy:");
  await page
    .getByRole("button", { name: "Xóa lịch topic", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Xác nhận", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Xóa lịch:");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Đóng", exact: true })
    .click();
  expect(
    (
      await (
        await page.request.get("/api/jobs?status=COMPLETED&limit=100")
      ).json()
    ).items.length,
  ).toBeGreaterThanOrEqual(backupsBefore);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: resolve(screenshotFolder, "queue-controls-mobile.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Mở menu" }).click();
  await page.getByRole("button", { name: "Tổng quan", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Tổng quan Vault" }),
  ).toBeVisible();
  await expect(page.locator(".sidebar")).not.toHaveClass(/open/);
  if (await closeToast.isVisible()) await closeToast.click();
  await page.screenshot({
    path: resolve(screenshotFolder, "dashboard-mobile.png"),
    fullPage: true,
    animations: "disabled",
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
});
