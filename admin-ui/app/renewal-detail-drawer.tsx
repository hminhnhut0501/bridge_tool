import { Box, Button, Chip, Drawer, IconButton, Stack, Typography, type ChipProps } from "@mui/material";
import { RefreshCw, Search, XCircle, Zap } from "lucide-react";

type RenewalDetail = {
  customerName?: string;
  telegramId?: string;
  planName?: string;
  orderId?: string;
  expireAt?: string;
  taskState?: string;
  renewalStatus?: string;
  renewalProgress?: { done?: number; total?: number; kicking?: number; pending?: number; error?: number };
  renewalReason?: string;
  renewalLastError?: string;
  renewalLatestKickAt?: string;
  renewalGroupDetails?: Array<{ status?: string; groupId?: string }>;
};

type ChipTone = NonNullable<ChipProps["color"]>;
type RenewalFocusFilter = "all" | "important" | "new" | "svip" | "unreminded" | "chokick" | "review" | "kicked" | "retained" | "error";

type Props = {
  open: boolean;
  onClose: () => void;
  selectedRenewalDetail: RenewalDetail | null;
  renewalTaskStateLabel: (value: string) => string;
  renewalTaskStateTone: (value: string) => ChipTone | undefined;
  renewalTaskStateHint: (value: string) => string;
  renewalStatusLabel: (value: string) => string;
  renewalStatusTone: (value: string) => ChipTone | undefined;
  dateText: (value: string) => string;
  renewalGroupStateLabel: (value: string) => string;
  renewalFocusFilter: string;
  setRenewalFocusFilter: (value: RenewalFocusFilter) => void;
  setRenewalPage: (value: number) => void;
  renewalTimelineGroupStateFilter: string;
  setRenewalTimelineGroupStateFilter: (value: string) => void;
  renewalTimelineTaskStateFilter: string;
  setRenewalTimelineTaskStateFilter: (value: string) => void;
  selectedRenewalAttempts: Array<{ group_task_id?: string | null; attempt_state?: string | null }>;
  renewalKickV2GroupStateByGroupTaskId: Map<string, string>;
  refreshKickAudit: (live: boolean) => void;
  requeueRenewalKickV2Handler: (telegramId: string, orderId: string, planName: string, customerName: string, groupsToKick: string[]) => Promise<void>;
  kickNowRenewalKickV2Handler: (telegramId: string, orderId: string, planName: string, customerName: string, groupsToKick: string[]) => Promise<void>;
  reviewRenewalTaskHandler: (orderId: string, telegramId: string, action: "requeue" | "close", reason?: string) => Promise<void>;
  openCustomerFromLookup: (telegramId: string) => void;
};

export function RenewalDetailDrawer(props: Props) {
  const {
    open,
    onClose,
    selectedRenewalDetail,
    renewalTaskStateLabel,
    renewalTaskStateTone,
    renewalTaskStateHint,
    renewalStatusLabel,
    renewalStatusTone,
    dateText,
    renewalGroupStateLabel,
    renewalFocusFilter,
    setRenewalFocusFilter,
    setRenewalPage,
    renewalTimelineGroupStateFilter,
    setRenewalTimelineGroupStateFilter,
    renewalTimelineTaskStateFilter,
    setRenewalTimelineTaskStateFilter,
    selectedRenewalAttempts,
    renewalKickV2GroupStateByGroupTaskId,
    refreshKickAudit,
    requeueRenewalKickV2Handler,
    kickNowRenewalKickV2Handler,
    reviewRenewalTaskHandler,
    openCustomerFromLookup,
  } = props;
  const detail = selectedRenewalDetail;
  const detailOrderId = detail?.orderId || "";
  const detailTelegramId = detail?.telegramId || "";
  const detailPlanName = detail?.planName || "";
  const detailCustomerName = detail?.customerName || "";

  return (
    <Drawer anchor="right" open={open} onClose={onClose} sx={{ "& .MuiDrawer-paper": { width: { xs: "100%", sm: 440 }, maxWidth: "100vw", borderTopLeftRadius: 20, borderBottomLeftRadius: 20 } }}>
      <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
        <Box sx={{ px: 2, py: 1.5, borderBottom: "1px solid", borderColor: "divider", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 900, lineHeight: 1.2 }}>Chi tiết renewal</Typography>
            <Typography variant="body2" color="text.secondary">Tóm tắt task, tiến độ và timeline retry.</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <XCircle size={18} />
          </IconButton>
        </Box>
        <Box sx={{ p: 2, overflow: "auto" }}>
          <Stack spacing={1.25}>
            {detail ? (
              <>
                <Box sx={{ p: 1.25, borderRadius: 2.5, bgcolor: "rgba(59,130,246,0.04)", border: "1px solid rgba(59,130,246,0.14)" }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 800 }}>1. Tổng quan</Typography>
                  <Box sx={{ mt: 0.75, display: "flex", justifyContent: "space-between", gap: 1, alignItems: "flex-start", flexWrap: "wrap" }}>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography sx={{ fontWeight: 900, fontSize: 17, lineHeight: 1.15 }}>{detailCustomerName || "-"}</Typography>
                      <Typography variant="body2" color="text.secondary">Telegram: <strong>{detailTelegramId || "-"}</strong></Typography>
                      <Typography variant="body2" color="text.secondary">{detailPlanName || "-" } · Đơn {detailOrderId || "-"}</Typography>
                      <Typography variant="body2" color="text.secondary">{detail?.expireAt ? `Hạn ${dateText(detail.expireAt)}` : "-"}</Typography>
                    </Box>
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, alignItems: "flex-end" }}>
                      <Chip size="small" label={renewalTaskStateLabel(selectedRenewalDetail.taskState || "")} color={renewalTaskStateTone(selectedRenewalDetail.taskState || "")} variant="filled" />
                      <Chip size="small" label={renewalStatusLabel(selectedRenewalDetail.renewalStatus || "")} color={renewalStatusTone(selectedRenewalDetail.renewalStatus || "")} variant="outlined" />
                    </Box>
                  </Box>
                </Box>
                <Box sx={{ p: 1.25, borderRadius: 2.5, bgcolor: "rgba(16,185,129,0.04)", border: "1px solid rgba(16,185,129,0.14)" }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 800 }}>2. Trạng thái</Typography>
                  <Box sx={{ mt: 0.75, display: "grid", gap: 0.85 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Tiến độ</Typography>
                      <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mt: 0.5 }}>
                        {selectedRenewalDetail.renewalProgress?.done || 0}/{selectedRenewalDetail.renewalProgress?.total || 0} xong · {selectedRenewalDetail.renewalProgress?.kicking || 0} đang chờ worker · {selectedRenewalDetail.renewalProgress?.pending || 0} chờ xử lý · {selectedRenewalDetail.renewalProgress?.error || 0} lỗi
                      </Typography>
                    </Box>
                    <Box sx={{ display: "grid", gap: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">Task state</Typography>
                      <Chip size="small" label={renewalTaskStateLabel(selectedRenewalDetail.taskState || "")} color={renewalTaskStateTone(selectedRenewalDetail.taskState || "")} variant="outlined" sx={{ height: 24, width: "fit-content", fontWeight: 800 }} />
                      <Typography variant="caption" color="text.secondary">{renewalTaskStateHint(selectedRenewalDetail.taskState || "")}</Typography>
                    </Box>
                    <Box sx={{ display: "grid", gap: 0.25 }}>
                      <Typography variant="caption" color="text.secondary">Lý do / last_error</Typography>
                      <Typography sx={{ whiteSpace: "pre-wrap", lineHeight: 1.4, fontSize: 13, fontWeight: 700 }}>{selectedRenewalDetail.renewalReason || selectedRenewalDetail.renewalLastError || "Không có reason"}</Typography>
                    </Box>
                  </Box>
                </Box>
                <Box sx={{ p: 1.25, borderRadius: 2.5, bgcolor: "rgba(245,158,11,0.04)", border: "1px solid rgba(245,158,11,0.16)" }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 800 }}>3. Timeline & hành động</Typography>
                  <Box sx={{ mt: 0.75, display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                    {([
                      { key: "all", label: "Tất cả" },
                      { key: "review", label: "Cần review" },
                      { key: "chokick", label: "Đã xếp hàng" },
                      { key: "kicked", label: "Đã xong" },
                      { key: "error", label: "Lỗi / thiếu map" },
                    ] as Array<{ key: RenewalFocusFilter; label: string }>).map((item) => (
                      <Chip key={item.key} size="small" label={item.label} clickable color={renewalFocusFilter === item.key ? "primary" : "default"} variant={renewalFocusFilter === item.key ? "filled" : "outlined"} onClick={() => { setRenewalFocusFilter(item.key); setRenewalPage(1); }} sx={{ height: 24, fontWeight: 800 }} />
                    ))}
                  </Box>
                  <Box sx={{ mt: 1, display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                    {[{ key: "ALL", label: "Tất cả group_state" }, ...Array.from(new Set((selectedRenewalAttempts.map((attempt) => renewalKickV2GroupStateByGroupTaskId.get(String(attempt.group_task_id || "")) || "").filter(Boolean)))).sort().map((state) => ({ key: state, label: renewalGroupStateLabel(state) }))].map((item) => (
                      <Chip key={item.key} size="small" label={item.label} clickable color={renewalTimelineGroupStateFilter === item.key ? "primary" : "default"} variant={renewalTimelineGroupStateFilter === item.key ? "filled" : "outlined"} onClick={() => setRenewalTimelineGroupStateFilter(item.key)} sx={{ height: 24, fontWeight: 800 }} />
                    ))}
                  </Box>
                  <Box sx={{ mt: 1, display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                    {[{ key: "ALL", label: "Tất cả task_state" }, ...Array.from(new Set(selectedRenewalAttempts.map((attempt) => String(attempt.attempt_state || "").trim().toUpperCase()).filter(Boolean))).sort().map((state) => ({ key: state, label: state.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase()) }))].map((item) => (
                      <Chip key={item.key} size="small" label={item.label} clickable color={renewalTimelineTaskStateFilter === item.key ? "primary" : "default"} variant={renewalTimelineTaskStateFilter === item.key ? "filled" : "outlined"} onClick={() => setRenewalTimelineTaskStateFilter(item.key)} sx={{ height: 24, fontWeight: 800 }} />
                    ))}
                  </Box>
                  <Box sx={{ mt: 1, display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                    <Button variant="contained" size="small" startIcon={<RefreshCw size={14} />} onClick={() => refreshKickAudit(true)}>Live refresh</Button>
                    {detailOrderId ? <Button variant="outlined" size="small" startIcon={<Zap size={14} />} onClick={() => void requeueRenewalKickV2Handler(detailTelegramId, detailOrderId, detailPlanName, detailCustomerName, [])}>Xếp hàng</Button> : null}
                    {detail.renewalStatus === "Cần review" ? (
                      <>
                        <Button variant="outlined" size="small" startIcon={<Zap size={14} />} onClick={() => void kickNowRenewalKickV2Handler(detailTelegramId, detailOrderId, detailPlanName, detailCustomerName, [])}>Kick ngay</Button>
                        <Button variant="outlined" size="small" color="error" startIcon={<XCircle size={14} />} onClick={() => void reviewRenewalTaskHandler(detailOrderId, detailTelegramId, "close", String(detail.renewalReason || detail.renewalLastError || "review_closed"))}>Đóng review</Button>
                      </>
                    ) : null}
                    <Button variant="text" size="small" startIcon={<Search size={14} />} onClick={() => openCustomerFromLookup(detailTelegramId)}>Mở khách</Button>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.75 }}>
                    {detail.renewalLatestKickAt ? `Cập nhật gần nhất: ${dateText(detail.renewalLatestKickAt)}` : "Chưa có update gần nhất"}
                  </Typography>
                </Box>
              </>
            ) : null}
          </Stack>
        </Box>
      </Box>
    </Drawer>
  );
}
