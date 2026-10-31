import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

test("V2: queue/library separation, search, confirmations, focus, responsive and themes", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  const password = readFileSync(
    resolve(process.env.VAULT_E2E_ACCESS || "../data/local-access.txt"),
    "utf8",
  ).match(/^Password: (.+)$/m)![1];
  await page.goto("/");
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  const requests: string[] = [];
  const fixtures = [
    {
      id: 9991,
      message_id: 4821,
      original_filename: "Video.mp4",
      remote_path:
        "Root/Telegram/Demo/251004_G4821-01_TenFileGoc_Caption_ngắn_và_tên_rất_dài_để_kiểm_tra_bố_cục_khi_tải_song_song.mp4",
      size: 100000000,
      downloaded: 32000000,
      download_speed: 7000000,
      source_name: "Demo Channel",
      topic_id: 0,
      topic_name: "All media",
      status: "TRANSFERRING",
      attempts: 1,
    },
    {
      id: 9992,
      message_id: 4822,
      original_filename: "Video.mp4",
      remote_path: "Root/Telegram/Demo/251004_G4821-02_Video_Caption.mp4",
      size: 70000000,
      downloaded: 0,
      download_speed: 0,
      source_name: "Demo Channel",
      topic_id: 0,
      topic_name: "All media",
      status: "VERIFYING",
      attempts: 1,
    },
    {
      id: 9993,
      message_id: 4823,
      original_filename: "Report.pdf",
      remote_path: "Root/Telegram/Demo/251004_M4823_Report.pdf",
      size: 2200000,
      downloaded: 2200000,
      source_name: "Demo Channel",
      topic_id: 0,
      topic_name: "All media",
      status: "COMPLETED",
      attempts: 1,
    },
    {
      id: 9994,
      message_id: 4824,
      original_filename: "Next.mp4",
      remote_path: "Root/Telegram/Demo/251004_M4824_Next.mp4",
      size: 90000000,
      downloaded: 0,
      source_name: "Demo Channel",
      topic_id: 0,
      topic_name: "All media",
      status: "QUEUED",
      attempts: 0,
    },
  ];
  await page.route("**/api/jobs?**", async (route) => {
    requests.push(route.request().url());
    const params = new URL(route.request().url()).searchParams;
    const items = fixtures.filter(
      (job) =>
        params.get("status")!.split(",").includes(job.status) &&
        (!params.get("q") || job.remote_path.includes(params.get("q")!)),
    );
    await route.fulfill({ json: { items, next_cursor: null } });
  });
  const folder = resolve(
    process.env.VAULT_E2E_SCREENSHOTS || "../data/reports/audit-web",
  );
  mkdirSync(folder, { recursive: true });
  await page.route("**/api/transfers", (route) =>
    route.fulfill({ json: { items: fixtures.slice(0, 2) } }),
  );
  await page.route("**/api/status", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({
      json: {
        ...data,
        telegram: "connected",
        active: 2,
        counts: {
          COMPLETED: { count: 42, bytes: 7900000000 },
          QUEUED: { count: 1390, bytes: 0 },
          FAILED: { count: 0, bytes: 0 },
        },
        transfer_pause_until: Date.now() / 1000 + 299,
      },
    });
  });
  await page.getByRole("button", { name: "Tổng quan", exact: true }).click();
  await expect(page.locator(".dashboard-metric")).toHaveCount(3);
  await expect(page.locator(".dashboard-job")).toHaveCount(2);
  await expect(page.locator(".dashboard-status")).toContainText(
    "File tiếp theo sau 04:",
  );
  await expect(page.locator(".dashboard-job").last()).toContainText(
    "Đang xác minh",
  );
  await expect(page.locator(".dashboard-job").last()).not.toContainText("0%");
  expect(await page.locator(".dashboard-event").count()).toBeLessThanOrEqual(5);
  await expect(
    page.locator(".protection-panel,.throughput-row,.system-panel"),
  ).toHaveCount(0);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: resolve(folder, "dashboard-compact-desktop.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    )
    .toBe(true);
  await page.screenshot({
    path: resolve(folder, "dashboard-compact-mobile.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 1440, height: 1000 });

  await page
    .getByRole("button", { name: "Truyền & hàng đợi", exact: true })
    .click();
  await expect(page.locator(".transfer-card")).toHaveCount(2);
  const rows = await page
    .locator(".compact-transfer")
    .evaluateAll((elements) =>
      elements.map((e) => e.getBoundingClientRect().toJSON()),
    );
  expect(rows[1].top).toBeGreaterThanOrEqual(rows[0].bottom);
  expect(rows[0].height).toBeLessThanOrEqual(130);
  const menuBox = await page
    .getByRole("button", { name: "Thao tác file 9991", exact: true })
    .boundingBox();
  expect(menuBox!.x).toBeGreaterThan(rows[0].right - 70);

  await expect(page.locator(".queue-controls")).not.toHaveAttribute("open", "");
  await page.screenshot({
    path: resolve(folder, "luminous-transfers-desktop.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    )
    .toBe(true);
  await page.screenshot({
    path: resolve(folder, "luminous-transfers-mobile.png"),
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 1440, height: 1000 });

  await expect(page.locator(".is-verifying")).not.toContainText("0%");
  await expect(page.locator(".is-verifying")).not.toContainText("0 B /");
  await expect(page.locator(".is-verifying")).toContainText("Đã truyền xong");
  await page
    .getByRole("button", { name: "Thao tác file 9991", exact: true })
    .click();
  await page.getByRole("button", { name: "Hủy transfer" }).first().click();
  await expect(page.getByRole("dialog")).toContainText("251004_G4821-01");
  await page.keyboard.press("Shift+Tab");
  expect(
    await page.evaluate(
      () => !!document.activeElement?.closest('[role="dialog"]'),
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("tab", { name: /Hàng đợi/ }).click();
  await expect(page.locator("tbody td:nth-child(2) .badge")).toHaveText([
    "Đang chờ",
  ]);
  await page
    .getByRole("button", { name: "Thư viện backup", exact: true })
    .click();
  await expect(page.locator("tbody td:nth-child(2) .badge")).toHaveText([
    "Hoàn tất",
  ]);
  expect(new URL(requests.at(-1)!).searchParams.get("status")).toBe(
    "COMPLETED",
  );
  await expect(page.locator(".queue-controls")).toHaveCount(0);
  await page.getByLabel("Tìm file", { exact: true }).fill("Report");
  await page.getByRole("button", { name: "Tìm kiếm", exact: true }).click();
  await expect
    .poll(() => new URL(requests.at(-1)!).searchParams.get("q"))
    .toBe("Report");
  await page.screenshot({
    path: resolve(folder, "v2-library-desktop.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Chi tiết job 9993", exact: true })
    .click();
  await expect(
    page.getByRole("dialog").getByRole("button", { name: "Xóa lịch" }),
  ).toHaveCount(0);
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".mobile-file-meta")).toBeVisible();
  await page.screenshot({
    path: resolve(folder, "v2-library-mobile.png"),
    fullPage: true,
  });
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    )
    .toBe(true);
  await page.getByRole("button", { name: "Đổi giao diện sáng tối" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.locator("html")).toHaveCSS(
    "background-color",
    "rgb(246, 245, 252)",
  );
  await page.evaluate(
    () =>
      new Promise<void>((done) =>
        requestAnimationFrame(() => requestAnimationFrame(() => done())),
      ),
  );
  await page.screenshot({
    path: resolve(folder, "v2-library-light-mobile.png"),
    fullPage: true,
  });
  const contrast: Record<string, number> = {};
  for (const theme of ["dark", "light"]) {
    await page.evaluate((theme) => {
      document.documentElement.dataset.theme = theme;
    }, theme);
    const measured = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = 1;
      const ctx = canvas.getContext("2d")!;
      const lum = (color: string) => {
        ctx.clearRect(0, 0, 1, 1);
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, 1, 1);
        const rgb = Array.from(ctx.getImageData(0, 0, 1, 1).data)
          .slice(0, 3)
          .map((v) => {
            const x = v / 255;
            return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
          });
        return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
      };
      const ratio = (a: string, b: string) => {
        const x = lum(a),
          y = lum(b);
        return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
      };
      const value = (key: string) => style.getPropertyValue(key).trim();
      return {
        text: ratio(value("--text"), value("--panel")),
        muted: ratio(value("--muted"), value("--panel")),
        primary: ratio("#ffffff", value("--accent")),
      };
    });
    for (const [key, value] of Object.entries(measured)) {
      contrast[`${theme}.${key}`] = value;
      expect(value).toBeGreaterThanOrEqual(4.5);
    }
  }
  writeFileSync(
    resolve(folder, "v2-contrast.json"),
    JSON.stringify(contrast, null, 2),
  );
  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const [name, slug] of [
    ["Cài đặt", "settings"],
    ["Lưu trữ", "storage"],
    ["Kết nối Telegram", "telegram"],
    ["Nguồn Telegram", "sources"],
    ["Cần xử lý", "failed"],
  ]) {
    await page.getByRole("button", { name, exact: true }).click();
    await expect(
      page.getByRole("heading", { name, exact: true }).first(),
    ).toBeVisible();
    if (slug === "settings")
      await expect(page.locator(".preferences")).toBeVisible();
    if (slug === "storage")
      await expect(page.locator(".storage-hero")).toBeVisible();
    if (slug === "sources")
      await expect(page.locator(".source-card").first()).toBeVisible();
    await page.screenshot({
      animations: "disabled",
      path: resolve(folder, `v2-${slug}-light.png`),
      fullPage: true,
    });
  }
});
