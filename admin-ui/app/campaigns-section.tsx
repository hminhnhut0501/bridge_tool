"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, Chip, Stack } from "@mui/material";
import { PauseCircle, PlayCircle, Plus } from "lucide-react";
import { Metric, PanelHead, Pagination, SimpleTable } from "./dashboard-components";

export function CampaignsSection(props: any) {
  const { campaigns, campaignPreview, selectedCampaign, campaignRecipientCounts, pagedCampaignRecipients, campaignRecipients, totalCampaignRecipientPages, campaignRecipientPage, setCampaignRecipientPage, changeCampaignStatus, setSelectedCampaignId, setCampaignModalOpen, setCampaignForm, EMPTY_CAMPAIGN_FORM } = props;
  return (
    <Stack spacing={2}>
      <Box sx={{ display: "grid", gap: 1.75, gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
        <Metric label="Campaign" value={String(campaigns.length)} />
        <Metric label="Đang chạy" value={String(campaigns.filter((item: any) => item.status === "RUNNING").length)} />
        <Metric label="Đã gửi" value={String(campaigns.reduce((sum: number, item: any) => sum + (item.sent_count || 0), 0))} />
        <Metric label="Preview nhận" value={String(campaignPreview?.total || 0)} />
      </Box>
      <section className="panel">
        <PanelHead title="Tạo campaign" subtitle="Tạo campaign trong popup để tránh trang chính quá nhiều trường. Worker sẽ gửi từng user theo delay để tránh spam." action={<Button variant="contained" size="small" onClick={() => { setCampaignForm({ ...EMPTY_CAMPAIGN_FORM }); setCampaignModalOpen(true); }} startIcon={<Plus size={16} />}>Tạo campaign</Button>} />
        <Box sx={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 1.5, px: 2, py: 1.5, borderTop: 1, borderColor: "divider", color: "text.secondary" }}>
          <strong>Preview: {campaignPreview?.total || 0} người</strong>
          <Chip size="small" label={`Active: ${campaignPreview?.counts?.VIP_ACTIVE || 0}`} />
          <Chip size="small" label={`Hết hạn: ${campaignPreview?.counts?.VIP_EXPIRED || 0}`} />
          <Chip size="small" label={`Chưa mua: ${campaignPreview?.counts?.NO_PURCHASE || 0}`} />
        </Box>
      </section>
      <section className="panel">
        <PanelHead title="Danh sách campaign" subtitle="Bấm tên campaign để xem danh sách người nhận và trạng thái từng người." />
        <SimpleTable
          headers={["Campaign", "Tệp", "Trạng thái", "Tiến trình", "Delay", "Thao tác"]}
          rows={campaigns.map((item: any) => [
            <button key={`select-${item.id}`} className="link-button" onClick={() => { setSelectedCampaignId(item.id); setCampaignRecipientPage(1); }}><strong>{item.title}</strong><div className="muted">{item.created_at}</div></button>,
            <><strong>{item.target_segment}</strong><div className="muted">{String(item.raw_data?.plan_filter || "ALL")} • {String(item.raw_data?.plan_match_scope || "ANY_PAID")}</div></>,
            <span key={`status-${item.id}`} className={item.status}>{item.status}</span>,
            <><strong>{item.sent_count}/{item.total_recipients}</strong><div className="muted">Fail {item.failed_count} • Skip {item.skipped_count}</div></>,
            `${item.delay_seconds}s`,
            <Box key={`actions-${item.id}`} sx={{ display: "flex", gap: 1, justifyContent: "flex-end" }}>
              {item.status !== "RUNNING" && item.status !== "DONE" && item.status !== "CANCELLED" ? <Button variant="outlined" size="small" onClick={() => changeCampaignStatus(item.id, "start")} startIcon={<PlayCircle size={15} />}>Gửi</Button> : null}
              {item.status === "RUNNING" ? <Button variant="outlined" size="small" onClick={() => changeCampaignStatus(item.id, "pause")} startIcon={<PauseCircle size={15} />}>Tạm dừng</Button> : null}
              {item.status !== "DONE" && item.status !== "CANCELLED" ? <Button color="error" variant="outlined" size="small" onClick={() => changeCampaignStatus(item.id, "cancel")}>Huỷ</Button> : null}
            </Box>,
          ])}
        />
      </section>
      <section className="panel">
        <PanelHead title={selectedCampaign ? `Người nhận: ${selectedCampaign.title}` : "Người nhận"} subtitle="Danh sách được snapshot lúc tạo campaign. Người đã SENT sẽ không bị gửi lại khi worker restart." />
        <div className="campaign-preview">
          <span>Pending: {campaignRecipientCounts.PENDING || 0}</span>
          <span>Sent: {campaignRecipientCounts.SENT || 0}</span>
          <span>Failed: {campaignRecipientCounts.FAILED || 0}</span>
          <span>Skipped: {campaignRecipientCounts.SKIPPED || 0}</span>
        </div>
        <SimpleTable
          headers={["Khách", "Telegram ID", "Nhóm", "Gói liên quan", "Trạng thái", "Gửi lúc", "Lỗi"]}
          rows={pagedCampaignRecipients.map((item: any) => [
            <><strong>{item.full_name || item.username || "-"}</strong><div className="muted">{item.username ? `@${item.username}` : ""}</div></>,
            item.telegram_user_id,
            item.segment,
            <><strong>{String(item.raw_data?.latest_plan_name || "-")}</strong><div className="muted">{Array.isArray(item.raw_data?.paid_plan_names) ? item.raw_data.paid_plan_names.join(", ") : ""}</div></>,
            <span key={`r-${item.id}`} className={item.status}>{item.status}</span>,
            item.sent_at || item.last_attempt_at,
            item.error || "-",
          ])}
        />
        <Pagination page={campaignRecipientPage} totalPages={totalCampaignRecipientPages} totalItems={campaignRecipients.length} onPage={setCampaignRecipientPage} label="người nhận" />
      </section>
    </Stack>
  );
}
