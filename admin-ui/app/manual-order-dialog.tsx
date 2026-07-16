"use client";

import { useMemo, useState, type Dispatch, type SetStateAction } from "react";
import { Alert, Box, Button, Chip, MenuItem, Stack, TextField, Tooltip, Typography } from "@mui/material";
import { Loader2, Plus, RefreshCw } from "lucide-react";
import type { HiddenGroup, ManualOrderResult } from "@/lib/api";
import { MuiDialogShell } from "./dashboard-components";
import { dateTimePreviewText, isLifetimeText, resolveOrderLabel } from "./dashboard-helpers";

export type ManualOrderFormState = {
  telegram_user_id: string;
  full_name: string;
  plan_key: string;
  plan_name: string;
  plan_mode: string;
  entitlement_type: string;
  entitlement_key: string;
  special_group_id: string;
  special_group_duration: string;
  note: string;
  amount: string;
  expiry_mode: string;
  duration_days: string;
  expire_at: string;
  coupon_code: string;
  payment_currency: string;
  payment_provider: string;
  admin_label?: string;
};

export type ManualOrderDialogProps = {
  open: boolean;
  onClose: () => void;
  saving: boolean;
  onSave: () => void | Promise<void>;
  form: ManualOrderFormState;
  setForm: Dispatch<SetStateAction<ManualOrderFormState>>;
  result: ManualOrderResult | null;
  onGenerateActiveCode: () => void | Promise<void>;
  onGenerateJoinLink: () => void | Promise<void>;
  activeSpecialGroups: HiddenGroup[];
  configuredGroups: number[];
  customDurationEnabled: boolean;
  manualPlanKeyOptions: string[];
  manualPlanNameFromKey: (value: string) => string;
  hiddenGroupManualPrice: (group: HiddenGroup, durationKey: string, currency: string) => number;
  hiddenGroupManualPlanName: (group: HiddenGroup, durationKey: string) => string;
  onChangePlanKey: (value: string) => void;
  onChangeSpecialGroup: (groupId: string, durationKey?: string) => void;
  onCopy: (value: string, label: string) => void | Promise<void>;
};

function isLifetimePlan(value: string) {
  return isLifetimeText(value);
}

export function ManualOrderDialog({
  open,
  onClose,
  saving,
  onSave,
  form,
  setForm,
  result,
  onGenerateActiveCode,
  onGenerateJoinLink,
  activeSpecialGroups,
  configuredGroups,
  customDurationEnabled,
  manualPlanKeyOptions,
  manualPlanNameFromKey,
  hiddenGroupManualPrice,
  hiddenGroupManualPlanName,
  onChangePlanKey,
  onChangeSpecialGroup,
  onCopy,
}: ManualOrderDialogProps) {
  const planOptions = useMemo(
    () => [...manualPlanKeyOptions, ...(customDurationEnabled ? ["CUSTOM_DURATION"] : [])],
    [customDurationEnabled, manualPlanKeyOptions],
  );
  const selectedSpecialGroup = form.special_group_id ? activeSpecialGroups.find((item) => item.id === form.special_group_id) || null : null;
  const planName = useMemo(() => {
    const specialPlanName = selectedSpecialGroup ? hiddenGroupManualPlanName(selectedSpecialGroup, form.special_group_duration || "1M") : "";
    if (specialPlanName) return specialPlanName;
    if (form.plan_mode === "CUSTOM_DURATION") return "Tùy chỉnh";
    if (form.plan_key === "CUSTOM") return form.plan_name.trim() || manualPlanNameFromKey("FULL_1M");
    return manualPlanNameFromKey(form.plan_key);
  }, [form.plan_key, form.plan_mode, form.plan_name, form.special_group_duration, manualPlanNameFromKey, hiddenGroupManualPlanName, selectedSpecialGroup]);
  const manualExpiryPreview = useMemo(() => {
    if (form.expiry_mode === "date") return `Sẽ áp dụng: ${dateTimePreviewText(form.expire_at, "Chưa chọn ngày hết hạn")}`;
    if (isLifetimePlan(planName)) return `Sẽ áp dụng: ${form.duration_days || "3650"} ngày (lifetime)`;
    return `Sẽ áp dụng: ${form.duration_days || "30"} ngày`;
  }, [form.duration_days, form.expire_at, form.expiry_mode, planName]);
  const orderLabel = result ? resolveOrderLabel(result) : null;
  const [resultDetailsOpen, setResultDetailsOpen] = useState(false);

  return (
    <MuiDialogShell
      open={open}
      title="Tạo đơn thủ công"
      subtitle="Nhập thông tin khách, tạo order PAID và gen link join group."
      onClose={onClose}
      maxWidth="lg"
      fullScreenOnMobile
      actions={
        <>
          <Button variant="outlined" onClick={onClose}>Đóng</Button>
          <Button variant="contained" onClick={() => void onSave()} disabled={saving} startIcon={saving ? <Loader2 size={18} className="spin" /> : <Plus size={18} />}>Tạo đơn</Button>
        </>
      }
    >
      <Box sx={{ maxHeight: { xs: "100dvh", md: "78vh" }, overflowY: "auto", pr: 0.5 }}>
        <Box sx={{ display: "grid", gap: 2.5, gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, mb: 2 }}>
          <Stack spacing={2}>
            <TextField label="Telegram ID" value={form.telegram_user_id} onChange={(event) => setForm((current) => ({ ...current, telegram_user_id: event.target.value }))} placeholder="VD: 7344961485" size="small" helperText="ID số của khách. Không dùng username @." />
            <TextField label="Tên khách" value={form.full_name} onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))} placeholder="Tên hiển thị để dễ quản lý" size="small" />
            <TextField select label="Gói lưu vào đơn" value={form.plan_key} onChange={(event) => onChangePlanKey(event.target.value)} size="small" helperText="Chọn gói thường hoặc Tùy chỉnh thời hạn.">
              {planOptions.map((item) => (
                <MenuItem key={item} value={item}>
                  {item === "CUSTOM" ? "Tự nhập tên gói" : item === "CUSTOM_DURATION" ? "Tùy chỉnh thời hạn" : manualPlanKeyOptions.includes(item) ? manualPlanNameFromKey(item) : item}
                </MenuItem>
              ))}
            </TextField>
            {form.plan_mode === "CUSTOM_DURATION" ? (
              <>
                <TextField select label="Phạm vi cấp quyền" value={form.entitlement_type} onChange={(event) => setForm((current) => ({ ...current, entitlement_type: event.target.value, entitlement_key: "" }))} size="small">
                  <MenuItem value="ALL_ACCESS">All Access</MenuItem>
                  <MenuItem value="GROUP_COLLECTION">Group / Collection</MenuItem>
                </TextField>
                {form.entitlement_type === "GROUP_COLLECTION" ? (
                  <TextField select label="Group / Collection" value={form.entitlement_key} onChange={(event) => setForm((current) => ({ ...current, entitlement_key: event.target.value }))} size="small" required>
                    <MenuItem value="">
                      <em>Chọn group</em>
                    </MenuItem>
                    {configuredGroups.map((item) => <MenuItem key={item} value={`G${item}`}>Group {item}</MenuItem>)}
                  </TextField>
                ) : null}
              </>
            ) : null}
            <TextField select label="Special Group" value={form.special_group_id} onChange={(event) => onChangeSpecialGroup(event.target.value, form.special_group_duration)} size="small" helperText={activeSpecialGroups.length ? "Chọn Special Group riêng. Khi chọn, ô gói thường sẽ tự chuyển sang Special." : "Chưa có Special Group đang hoạt động."}>
              <MenuItem value="">
                <em>Không dùng Special Group</em>
              </MenuItem>
              {activeSpecialGroups.map((group) => (
                <MenuItem key={group.id} value={group.id}>{group.name} ({group.chat_id})</MenuItem>
              ))}
            </TextField>
            {form.special_group_id ? (
              <TextField select label="Hạn Special Group" value={form.special_group_duration} onChange={(event) => onChangeSpecialGroup(form.special_group_id, event.target.value)} size="small" helperText="Dùng để khớp đúng token plan và giá của special group.">
                <MenuItem value="1M">30 ngày</MenuItem>
                <MenuItem value="LIFE">Trọn đời</MenuItem>
              </TextField>
            ) : null}
            <TextField label="Mã / ghi chú" value={form.coupon_code} onChange={(event) => setForm((current) => ({ ...current, coupon_code: event.target.value.toUpperCase() }))} placeholder="VD: MANUAL_ADMIN" size="small" />
          </Stack>

          <Stack spacing={2}>
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 100px", gap: 1 }}>
              <TextField label="Số tiền" value={form.amount} onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))} placeholder="0" inputMode="numeric" size="small" helperText="VNĐ tự làm tròn số nguyên." />
              <TextField select label="Tiền tệ" value={form.payment_currency} onChange={(event) => {
                const nextCurrency = event.target.value;
                const selectedGroup = form.special_group_id ? activeSpecialGroups.find((item) => item.id === form.special_group_id) || null : null;
                setForm((current) => ({
                  ...current,
                  payment_currency: nextCurrency,
                  amount: selectedGroup ? String(hiddenGroupManualPrice(selectedGroup, form.special_group_duration || "1M", nextCurrency) || "0") : current.amount,
                }));
              }} size="small">
                <MenuItem value="VND">VNĐ</MenuItem>
                <MenuItem value="USD">USD</MenuItem>
                <MenuItem value="USDT">USDT</MenuItem>
              </TextField>
            </Box>
            <TextField select label="Phương thức thanh toán" value={form.payment_provider} onChange={(event) => setForm((current) => ({ ...current, payment_provider: event.target.value }))} size="small" helperText="Chỉ để ghi nhận báo cáo và đối soát, không đổi flow cấp quyền chính.">
              <MenuItem value="MANUAL">Thủ công</MenuItem>
              <MenuItem value="PAYOS">PayOS / VietQR</MenuItem>
              <MenuItem value="PAYPAL">PayPal</MenuItem>
              <MenuItem value="TRON_USDT">USDT TRC20</MenuItem>
            </TextField>
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1 }}>
              <TextField select label="Kiểu hết hạn" value={form.expiry_mode} onChange={(event) => setForm((current) => ({ ...current, expiry_mode: event.target.value, expire_at: event.target.value === "days" ? "" : current.expire_at }))} size="small">
                <MenuItem value="days">Theo số ngày</MenuItem>
                <MenuItem value="date">Ngày cụ thể</MenuItem>
              </TextField>
              {form.expiry_mode === "days" ? (
                <TextField label="Số ngày sử dụng" value={form.duration_days} onChange={(event) => setForm((current) => ({ ...current, duration_days: event.target.value }))} placeholder={form.plan_mode === "CUSTOM_DURATION" ? "1" : "30"} inputMode="numeric" size="small" helperText={manualExpiryPreview} />
              ) : (
                <TextField label="Ngày hết hạn cụ thể" type="datetime-local" value={form.expire_at} onChange={(event) => setForm((current) => ({ ...current, expire_at: event.target.value }))} size="small" slotProps={{ inputLabel: { shrink: true } }} helperText={manualExpiryPreview} />
              )}
            </Box>
            <TextField label="Ghi chú nội bộ cho đơn" value={form.note} onChange={(event) => setForm((current) => ({ ...current, note: event.target.value }))} placeholder="Ví dụ: khách VIP cũ, gia hạn thủ công..." size="small" multiline minRows={2} />
          </Stack>
        </Box>

        {result ? (
          <Box sx={{ mt: 3, pt: 3, borderTop: "2px solid", borderColor: "primary.main", display: "grid", gap: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>Kết quả tạo đơn</Typography>
            <Alert severity="info" variant="outlined">
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, flexWrap: "wrap" }}>
                <strong>Hiển thị:</strong>
                <Typography component="span" sx={{ fontWeight: 700 }}>{orderLabel?.displayLabel || result.plan_name}</Typography>
                {orderLabel?.showTechLabel ? (
                  <Tooltip title={`Kỹ thuật: ${orderLabel.techLabel}`} arrow>
                    <Chip size="small" label="i" variant="outlined" sx={{ height: 20, minWidth: 20, fontWeight: 800 }} />
                  </Tooltip>
                ) : null}
              </Box>
            </Alert>

            <Box sx={{ display: "grid", gap: 1.25 }}>
              <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "text.secondary" }}>{result.manual_order_message_title || "Tin active code"}</Typography>
                {result.manual_order_text ? (
                  <Button size="small" variant="outlined" sx={{ borderRadius: 4, height: 28 }} onClick={() => onCopy(result.manual_order_text || "", "manual_order_text")}>
                    {result.manual_order_message_button_label || "Copy"}
                  </Button>
                ) : null}
              </Stack>
              {!result.manual_order_text ? (
                <Box sx={{ p: 3, border: "1px dashed", borderColor: "divider", borderRadius: 3, textAlign: "center", bgcolor: "background.default" }}>
                  <Typography variant="body2" sx={{ color: "text.secondary", mb: 1.5 }}>Chưa có active code cho đơn này.</Typography>
                  <Button variant="contained" onClick={() => void onGenerateActiveCode()} disabled={saving} startIcon={saving ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
                    Gen active code
                  </Button>
                </Box>
              ) : (
                <TextField value={result.manual_order_text || ""} slotProps={{ input: { readOnly: true } }} fullWidth multiline minRows={4} />
              )}
            </Box>

            <Box sx={{ display: "flex", gap: 1, position: "sticky", bottom: 8, zIndex: 2, bgcolor: "background.paper", py: 0.5 }}>
              <Button fullWidth variant="contained" onClick={() => void onGenerateActiveCode()} disabled={saving} startIcon={saving ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
                {result.manual_order_text ? "Gen lại active" : "Gen active code"}
              </Button>
              <Button fullWidth variant="outlined" onClick={() => void onGenerateJoinLink()} disabled={saving} startIcon={saving ? <Loader2 size={16} className="spin" /> : <Plus size={16} />}>
                {result.manual_order_join_text ? "Gen lại join" : "Gen join"}
              </Button>
            </Box>

            <Button variant="text" onClick={() => setResultDetailsOpen((current) => !current)} sx={{ justifyContent: "flex-start", px: 0 }}>
              {resultDetailsOpen ? "Ẩn chi tiết" : "Xem thêm chi tiết"}
            </Button>

            {resultDetailsOpen ? (
              <Box sx={{ display: "grid", gap: 1.25 }}>
                {result.activation_url ? <TextField value={result.activation_url} slotProps={{ input: { readOnly: true } }} fullWidth size="small" label="Link active" /> : null}
                {result.links_text ? <TextField value={result.links_text} slotProps={{ input: { readOnly: true } }} fullWidth multiline minRows={3} label="Join text" /> : null}
                {result.support_text ? <TextField value={result.support_text} slotProps={{ input: { readOnly: true } }} fullWidth multiline minRows={3} label="Support" /> : null}
              </Box>
            ) : null}
          </Box>
        ) : null}
      </Box>
    </MuiDialogShell>
  );
}
