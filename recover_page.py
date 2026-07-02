with open("admin-ui/app/page.tsx", "r") as f:
    content = f.read()

start_marker = "        {manualOrderModalOpen ? ("
end_marker = "          </MuiDialogShell>\n        ) : null}"

# The first occurrence of start_marker is where the top_part ends
idx_top_end = content.find(start_marker)
top_part = content[:idx_top_end]

# The second occurrence of start_marker is in the duplicated original content!
idx_second_start = content.find(start_marker, idx_top_end + 1)
# Find the end of manualOrderModalOpen in the second occurrence
idx_second_end = content.find(end_marker, idx_second_start) + len(end_marker)

# The bottom part is everything after the second occurrence's end
bottom_part = content[idx_second_end:]

new_modal_ui = """        {manualOrderModalOpen ? (
          <MuiDialogShell open title="Tạo đơn thủ công" subtitle="Nhập thông tin khách, tạo order PAID và gen link join group." onClose={() => setManualOrderModalOpen(false)} maxWidth="lg">
              <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" } }}>
                  {/* Cột trái: Thông tin khách & gói */}
                  <Box sx={{ display: "grid", gap: 2, alignContent: "start" }}>
                    <TextField label="Telegram ID" value={manualOrderForm.telegram_user_id} onChange={(event) => setManualOrderForm({ ...manualOrderForm, telegram_user_id: event.target.value })} placeholder="VD: 7344961485" size="small" helperText="ID số của khách. Không dùng username @." />
                    <TextField label="Tên khách" value={manualOrderForm.full_name} onChange={(event) => setManualOrderForm({ ...manualOrderForm, full_name: event.target.value })} placeholder="Tên hiển thị để dễ quản lý" size="small" />
                    <TextField select label="Gói cấp cho khách" value={manualOrderForm.plan_key} onChange={(event) => changeManualPlanKey(event.target.value)} size="small">
                      {manualPlanKeyOptions.map((item) => <MenuItem key={item} value={item}>{item === "CUSTOM" ? "Tự nhập tên gói" : planOptionLabel(item)}</MenuItem>)}
                    </TextField>
                    <TextField label="Tên gói lưu vào đơn" value={manualOrderForm.plan_key === "CUSTOM" ? manualOrderForm.plan_name : manualPlanNameFromKey(manualOrderForm.plan_key)} onChange={(event) => setManualOrderForm({ ...manualOrderForm, plan_name: event.target.value, plan_key: "CUSTOM" })} placeholder="VD: Collection 30 Ngày - Hang Cú Prime" size="small" helperText="Với gói tự nhập, nên chứa đúng tên collection đang cấu hình trong Nhóm & giá." />
                    <TextField label="Coupon / ghi chú mã" value={manualOrderForm.coupon_code} onChange={(event) => setManualOrderForm({ ...manualOrderForm, coupon_code: event.target.value.toUpperCase() })} placeholder="VD: MANUAL_ADMIN" size="small" />
                  </Box>

                  {/* Cột phải: Thanh toán & hạn dùng */}
                  <Box sx={{ display: "grid", gap: 2, alignContent: "start" }}>
                    <Box sx={{ display: "grid", gridTemplateColumns: "1fr 100px", gap: 1 }}>
                      <TextField label="Số tiền" value={manualOrderForm.amount} onChange={(event) => setManualOrderForm({ ...manualOrderForm, amount: event.target.value })} placeholder="0" inputMode="decimal" size="small" helperText="Nhập số thực. VNĐ thường không có thập phân." />
                      <TextField select label="Tiền tệ" value={manualOrderForm.payment_currency} onChange={(event) => setManualOrderForm({ ...manualOrderForm, payment_currency: event.target.value })} size="small">
                        <MenuItem value="VND">VNĐ</MenuItem>
                        <MenuItem value="USD">USD</MenuItem>
                        <MenuItem value="USDT">USDT</MenuItem>
                      </TextField>
                    </Box>
                    <TextField select label="Phương thức thanh toán" value={manualOrderForm.payment_provider} onChange={(event) => setManualOrderForm({ ...manualOrderForm, payment_provider: event.target.value })} size="small" helperText="Chỉ để ghi nhận báo cáo và đối soát, không đổi flow cấp quyền chính.">
                      <MenuItem value="MANUAL">Thủ công</MenuItem>
                      <MenuItem value="PAYOS">PayOS / VietQR</MenuItem>
                      <MenuItem value="PAYPAL">PayPal</MenuItem>
                      <MenuItem value="NOWPAYMENTS">NOWPayments</MenuItem>
                      <MenuItem value="TRON_USDT">USDT TRC20</MenuItem>
                    </TextField>
                    <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1 }}>
                      <TextField select label="Kiểu hết hạn" value={manualOrderForm.expiry_mode} onChange={(event) => setManualOrderForm({ ...manualOrderForm, expiry_mode: event.target.value, expire_at: event.target.value === "days" ? "" : manualOrderForm.expire_at })} size="small">
                        <MenuItem value="days">Theo số ngày</MenuItem>
                        <MenuItem value="date">Ngày cụ thể</MenuItem>
                      </TextField>
                      {manualOrderForm.expiry_mode === "days" ? (
                        <TextField label="Số ngày sử dụng" value={manualOrderForm.duration_days} onChange={(event) => setManualOrderForm({ ...manualOrderForm, duration_days: event.target.value })} placeholder="30" inputMode="numeric" size="small" helperText={manualExpiryPreview()} />
                      ) : (
                        <TextField label="Ngày hết hạn cụ thể" type="datetime-local" value={manualOrderForm.expire_at} onChange={(event) => setManualOrderForm({ ...manualOrderForm, expire_at: event.target.value })} size="small" slotProps={{ inputLabel: { shrink: true } }} helperText={manualExpiryPreview()} />
                      )}
                    </Box>
                    <TextField label="Ghi chú nội bộ cho đơn" value={manualOrderForm.note} onChange={(event) => setManualOrderForm({ ...manualOrderForm, note: event.target.value })} placeholder="Ví dụ: khách VIP cũ, gia hạn thủ công..." size="small" multiline minRows={2} />
                  </Box>
                </Box>
                
                <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider", bgcolor: "background.paper", borderRadius: 2 }}>
                  <Button variant="outlined" onClick={() => setManualOrderModalOpen(false)}>Đóng</Button>
                  <Button variant="contained" onClick={saveManualOrder} disabled={saving === "manual-order"} startIcon={saving === "manual-order" ? <Loader2 size={18} className="spin" /> : <Plus size={18} />}>Tạo đơn & Lấy Active Code</Button>
                </Stack>
                
                {manualOrderResult ? (
                  <Box sx={{ display: "grid", gap: 3, pt: 2, borderTop: 2, borderColor: "primary.main" }}>
                    <Typography variant="h6" sx={{ fontWeight: 800 }}>Kết quả tạo đơn</Typography>
                    
                    {/* Active Code Box */}
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "text.secondary" }}>{manualOrderResult.manual_order_message_title || "Tin active code"}</Typography>
                        <Button size="small" variant="outlined" sx={{ borderRadius: 4, height: 28 }} onClick={() => navigator.clipboard.writeText(stripHtml(manualOrderResult.manual_order_text || ""))}>
                          {manualOrderResult.manual_order_message_button_label || "Copy tin active code"}
                        </Button>
                      </Stack>
                      <TextField
                        value={stripHtml(manualOrderResult.manual_order_text || "")}
                        slotProps={{ input: { readOnly: true } }}
                        fullWidth
                        multiline
                        minRows={6}
                        sx={{ ...popupFieldSx, "& .MuiInputBase-root": { bgcolor: "#f8fafc" } }}
                      />
                    </Box>

                    {/* Join Link Generation / Display Box */}
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "text.secondary" }}>{manualOrderResult.manual_order_join_title || "Tin join group"}</Typography>
                        {manualOrderResult.manual_order_join_text ? (
                          <Button size="small" variant="outlined" sx={{ borderRadius: 4, height: 28 }} onClick={() => navigator.clipboard.writeText(stripHtml(manualOrderResult.manual_order_join_text || ""))}>
                            {manualOrderResult.manual_order_join_button_label || "Copy tin tham gia"}
                          </Button>
                        ) : null}
                      </Stack>
                      
                      {!manualOrderResult.manual_order_join_text ? (
                        <Box sx={{ p: 4, border: "1px dashed", borderColor: "divider", borderRadius: 3, textAlign: "center", bgcolor: "#f8fafc" }}>
                          <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>Bạn chưa tạo link tham gia nhóm cho đơn hàng này.</Typography>
                          <Button variant="contained" onClick={generateManualJoinLinkHandler} disabled={saving === "generate-join-link"} startIcon={saving === "generate-join-link" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
                            Tạo link tham gia nhóm
                          </Button>
                        </Box>
                      ) : (
                        <TextField
                          value={stripHtml(manualOrderResult.manual_order_join_text || "")}
                          slotProps={{ input: { readOnly: true } }}
                          fullWidth
                          multiline
                          minRows={6}
                          sx={{ ...popupFieldSx, "& .MuiInputBase-root": { bgcolor: "#f8fafc" } }}
                        />
                      )}
                    </Box>
                    
                  </Box>
                ) : null}
              </Box>
          </MuiDialogShell>
        ) : null}"""

# Assemble
final_content = top_part + new_modal_ui + bottom_part

with open("admin-ui/app/page.tsx", "w") as f:
    f.write(final_content)

print(f"File recovered! Top part length: {len(top_part)}, Bottom part length: {len(bottom_part)}")
