"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, Chip, Stack } from "@mui/material";
import { PauseCircle, PlayCircle, Plus } from "lucide-react";
import { AppSection, AppToolbar, Metric, Pagination, SimpleTable, statusChipSx, statusButtonSx } from "./dashboard-components";
import { dateText } from "./dashboard-helpers";

export function CampaignsSection(props: any) {
  const { campaigns, campaignPreview, selectedCampaign, campaignRecipientCounts, pagedCampaignRecipients, campaignRecipients, totalCampaignRecipientPages, campaignRecipientPage, setCampaignRecipientPage, changeCampaignStatus, setSelectedCampaignId, setCampaignModalOpen, setCampaignForm, EMPTY_CAMPAIGN_FORM } = props;
  return (
    <Stack spacing={2}>
      <Box sx={{ display: "grid", gap: 1.75, gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
        <Metric label="Campaign" value={String(campaigns.length)} accent="cyan" />
        <Metric label="Đang chạy" value={String(campaigns.filter((item: any) => item.status === "RUNNING").length)} accent="violet" />
        <Metric label="Đã gửi" value={String(campaigns.reduce((sum: number, item: any) => sum + (item.sent_count || 0), 0))} accent="amber" />
        <Metric label="Preview nhận" value={String(campaignPreview?.total || 0)} accent="blue" />
      </Box>
      <AppSection title="Tạo campaign" subtitle="Tạo campaign trong popup để tránh trang chính quá nhiều trường. Worker sẽ gửi từng user theo delay để tránh spam." action={<AppToolbar><Button variant="contained" size="small" onClick={() => { setCampaignForm({ ...EMPTY_CAMPAIGN_FORM }); setCampaignModalOpen(true); }} startIcon={<Plus size={16} />}>Tạo campaign</Button></AppToolbar>} accent="cyan">
        <Box sx={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 1.5, px: 2, py: 1.5, borderTop: 1, borderColor: "divider", color: "text.secondary" }}>
          <strong>Preview: {campaignPreview?.total || 0} người</strong>
          <Chip size="small" label={`Active: ${campaignPreview?.counts?.VIP_ACTIVE || 0}`} variant="outlined" sx={statusChipSx("success")} />
          <Chip size="small" label={`Hết hạn: ${campaignPreview?.counts?.VIP_EXPIRED || 0}`} variant="outlined" sx={statusChipSx("warning")} />
          <Chip size="small" label={`Chưa mua: ${campaignPreview?.counts?.NO_PURCHASE || 0}`} variant="outlined" sx={statusChipSx("muted")} />
        </Box>
      </AppSection>
      <AppSection title="Danh sách campaign" subtitle="Bấm tên campaign để xem danh sách người nhận và trạng thái từng người." accent="violet">
        <SimpleTable
          headers={["Campaign", "Tệp", "Trạng thái", "Tiến trình", "Delay", "Thao tác"]}
          rows={campaigns.map((item: any) => [
            <Button
              key={`select-${item.id}`}
              variant="text"
              onClick={() => { setSelectedCampaignId(item.id); setCampaignRecipientPage(1); }}
              sx={{ alignItems: "flex-start", justifyContent: "flex-start", textAlign: "left", px: 0, py: 0.5, minWidth: 0, textTransform: "none" }}
            >
              <Box component="span" sx={{ display: "grid", gap: 0.25 }}>
                <strong>{item.title}</strong>
                <span className="muted">{dateText(item.created_at)}</span>
              </Box>
            </Button>,
            <><strong>{item.target_segment}</strong><div className="muted">{String(item.raw_data?.plan_filter || "ALL")} • {String(item.raw_data?.plan_match_scope || "ANY_PAID")}</div></>,
            <span key={`status-${item.id}`} className={item.status}>{item.status}</span>,
            <><strong>{item.sent_count}/{item.total_recipients}</strong><div className="muted">Fail {item.failed_count} • Skip {item.skipped_count}</div></>,
            `${item.delay_seconds}s`,
            <Box key={`actions-${item.id}`} sx={{ display: "flex", gap: 1, justifyContent: "flex-end" }}>
              {item.status !== "RUNNING" && item.status !== "DONE" && item.status !== "CANCELLED" ? <Button variant="outlined" size="small" sx={statusButtonSx("success")} onClick={() => changeCampaignStatus(item.id, "start")} startIcon={<PlayCircle size={15} />}>Gửi</Button> : null}
              {item.status === "RUNNING" ? <Button variant="outlined" size="small" sx={statusButtonSx("warning")} onClick={() => changeCampaignStatus(item.id, "pause")} startIcon={<PauseCircle size={15} />}>Tạm dừng</Button> : null}
              {item.status !== "DONE" && item.status !== "CANCELLED" ? <Button variant="outlined" size="small" sx={statusButtonSx("error")} onClick={() => changeCampaignStatus(item.id, "cancel")}>Huỷ</Button> : null}
            </Box>,
          ])}
        />
      </AppSection>
      <AppSection title={selectedCampaign ? `Người nhận: ${selectedCampaign.title}` : "Người nhận"} subtitle="Danh sách được snapshot lúc tạo campaign. Người đã SENT sẽ không bị gửi lại khi worker restart." accent="amber">
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
            dateText(item.sent_at || item.last_attempt_at),
            item.error || "-",
          ])}
        />
        <Pagination page={campaignRecipientPage} totalPages={totalCampaignRecipientPages} totalItems={campaignRecipients.length} onPage={setCampaignRecipientPage} label="người nhận" />
      </AppSection>
    </Stack>
  );
}
