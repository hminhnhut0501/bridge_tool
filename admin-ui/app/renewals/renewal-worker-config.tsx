"use client";
import { Alert, Button, Paper, Stack, TextField, Typography } from "@mui/material";

export function RenewalWorkerConfig({ config, onSave }: { config: Record<string, unknown>; onSave: (payload: Record<string, unknown>) => void }) {
  const enabled = Boolean(config.enabled) && !Boolean(config.halted);
  const batch = Number(config.batch_limit || 5);
  const last = (config.last_batch || {}) as Record<string, unknown>;
  return <Paper variant="outlined" sx={{ p: 2, borderRadius: 3 }}><Stack spacing={1.5}>
    <Typography variant="h6" sx={{ fontWeight: 900 }}>Cấu hình worker gia hạn</Typography>
    {config.halt_reason ? <Alert severity="warning">Worker bị halt: {String(config.halt_reason)}</Alert> : null}
    <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
      <TextField label="Chu kỳ (giây)" type="number" defaultValue={Number(config.interval_seconds || 300)} slotProps={{ htmlInput: { min: 300 } }} id="renewal-worker-interval" />
      <TextField label="Batch (tối đa 5)" type="number" defaultValue={batch} slotProps={{ htmlInput: { min: 1, max: 5 } }} id="renewal-worker-batch" />
      <Button variant="contained" onClick={() => onSave({ enabled: !enabled, interval_seconds: Number((document.getElementById("renewal-worker-interval") as HTMLInputElement)?.value || 300), batch_limit: Math.min(5, Number((document.getElementById("renewal-worker-batch") as HTMLInputElement)?.value || 5)), confirm: true })}>{enabled ? "Tắt worker" : "Bật worker"}</Button>
      <Button color="error" variant="outlined" onClick={() => onSave({ enabled: false, emergency_stop: true, halt_reason: "admin_emergency_stop", confirm: true })}>Tạm dừng khẩn cấp</Button>
    </Stack>
    <Typography variant="body2" color="text.secondary">Lần chạy gần nhất: {String(config.last_run_at || "Chưa chạy")}</Typography>
    <Typography variant="body2" color="text.secondary">Batch gần nhất: {JSON.stringify(last)}</Typography>
    <Typography variant="caption" color="text.secondary">DONE {String(last.done || 0)} · RETAINED {String(last.retained || 0)} · RETRY {String(last.retry || 0)} · REVIEW {String(last.review || 0)}</Typography>
  </Stack></Paper>;
}
