import re

with open("app/page.tsx", "r") as f:
    content = f.read()

# Define the start and end of the block to replace
start_marker = "        {customerModalOpen && selectedCustomer ? ("
end_marker = "          </MuiDialogShell>\n        ) : null}"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx) + len(end_marker)

if start_idx == -1 or end_idx < len(end_marker):
    print("Error: Could not find block to replace")
    exit(1)

new_block = """        {customerModalOpen && selectedCustomer ? (
          <Dialog open={true} onClose={() => setCustomerModalOpen(false)} fullWidth maxWidth="xl" scroll="paper" PaperProps={{ sx: { borderRadius: 4, overflow: "hidden" } }}>
            {/* Custom Profile Header */}
            <Box sx={{ position: "relative", p: 3, borderBottom: 1, borderColor: "divider", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 2, bgcolor: "#0f172a", color: "#f8fafc" }}>
              <IconButton onClick={() => setCustomerModalOpen(false)} sx={{ position: "absolute", right: 16, top: 16, color: "rgba(255,255,255,0.7)", '&:hover': { bgcolor: "rgba(255,255,255,0.1)", color: "#fff" } }}>
                <X size={20} />
              </IconButton>
              
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Box sx={{ width: 56, height: 56, borderRadius: "50%", bgcolor: "rgba(255,255,255,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, fontWeight: 800 }}>
                  {selectedCustomer.name.charAt(0).toUpperCase()}
                </Box>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 800, pr: 4 }}>{selectedCustomer.name}</Typography>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.25 }}>
                    <Typography variant="body2" sx={{ color: "#94a3b8" }}>Telegram ID: {selectedCustomer.id}</Typography>
                    <Chip size="small" label={selectedCustomer.statusLabel} sx={{ ...statusChipSx(selectedCustomer.statusColor === "default" ? "muted" : (selectedCustomer.statusColor as any)), fontWeight: 800, height: 20, fontSize: 11 }} />
                  </Box>
                </Box>
              </Box>
              
              <Box sx={{ display: "flex", alignItems: "center", gap: 3, flexWrap: "wrap" }}>
                <Box sx={{ textAlign: "right" }}>
                  <Typography variant="caption" sx={{ color: "#94a3b8" }}>Tổng doanh thu</Typography>
                  <Typography sx={{ fontWeight: 800, fontSize: 18, color: "#fff", lineHeight: 1.2 }}>{money(selectedCustomer.revenue)}</Typography>
                </Box>
                <Box sx={{ textAlign: "right" }}>
                  <Typography variant="caption" sx={{ color: "#94a3b8" }}>Đơn PAID</Typography>
                  <Typography sx={{ fontWeight: 800, fontSize: 18, color: "#fff", lineHeight: 1.2 }}>{selectedCustomer.paidOrders.length}</Typography>
                </Box>
                <Box sx={{ textAlign: "right" }}>
                  <Typography variant="caption" sx={{ color: "#94a3b8" }}>Hạn gần nhất</Typography>
                  <Typography sx={{ fontWeight: 800, fontSize: 18, color: "#fff", lineHeight: 1.2 }}>{dateTextShort(selectedCustomer.latestExpire)}</Typography>
                </Box>
                <Box sx={{ width: 1, height: 40, bgcolor: "rgba(255,255,255,0.1)", display: { xs: "none", md: "block" } }} />
                <Stack direction="row" spacing={1}>
                  <Button variant="outlined" onClick={openCustomerRenewModal} sx={{ borderRadius: 999, px: 2, color: "#fff", borderColor: "rgba(255,255,255,0.2)", '&:hover': { borderColor: "rgba(255,255,255,0.4)" } }}>
                    Gia hạn
                  </Button>
                  <Button variant="contained" startIcon={<Plus size={16} />} onClick={openCustomerCreateOrderModal} sx={{ borderRadius: 999, px: 2 }}>
                    Tạo đơn mới
                  </Button>
                </Stack>
              </Box>
            </Box>

            <DialogContent sx={{ p: 3, display: "flex", gap: 4, alignItems: "stretch", minHeight: "60vh", flexDirection: { xs: "column", md: "row" } }}>
              {/* Sidebar Navigation */}
              <Box component="aside" sx={{ width: { xs: "100%", md: 240 }, flexShrink: 0 }}>
                <Typography variant="overline" sx={{ px: 1, color: "text.secondary", fontWeight: 800, letterSpacing: 1.2 }}>
                  Chi tiết
                </Typography>
                <Tabs
                  orientation="vertical"
                  value={(!customerDetailTab || customerDetailTab === "overview") ? "overview" : customerDetailTab}
                  onChange={(_, next) => setCustomerDetailTab(next)}
                  textColor="inherit"
                  sx={sidebarTabSx}
                >
                  <Tab value="overview" icon={<Activity size={16} />} iconPosition="start" label="Tổng quan" />
                  <Tab value="orders" icon={<ShoppingCart size={16} />} iconPosition="start" label="Đơn hàng" />
                  <Tab value="groups" icon={<ShieldCheck size={16} />} iconPosition="start" label="Nhóm active" />
                  <Tab value="timeline" icon={<ClipboardList size={16} />} iconPosition="start" label="Dấu vết" />
                </Tabs>
              </Box>

              {/* Main Content Area */}
              <Box component="section" sx={{ flex: 1, minWidth: 0 }}>
                {(!customerDetailTab || customerDetailTab === "overview") ? (
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <Box sx={{ p: 2.5, borderRadius: 3, bgcolor: "background.paper", border: 1, borderColor: "divider", boxShadow: "0 4px 12px rgba(0,0,0,0.02)" }}>
                      <Typography variant="h6" sx={{ fontWeight: 800, mb: 1 }}>Tình trạng khách hàng</Typography>
                      <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                        {selectedCustomerIsBlacklisted
                          ? "Khách đang blacklist, ưu tiên xem lý do và lịch sử gần nhất."
                          : selectedCustomer.activeOrders.length
                            ? "Khách đang còn quyền active, có thể gia hạn hoặc tạo đơn mới."
                            : selectedCustomer.paidOrders.length
                              ? "Khách đã có lịch sử thanh toán, nhưng hiện chưa active."
                              : "Khách chưa có lịch sử thanh toán, ưu tiên tạo đơn mới nếu cần."}
                      </Typography>
                    </Box>

                    {selectedCustomerRenewTargetOrder ? (
                      <Box sx={{ p: 2.5, borderRadius: 3, bgcolor: "#f0f9ff", border: 1, borderColor: "#bae6fd", display: "flex", alignItems: "center", gap: 2 }}>
                        <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: "#e0f2fe", color: "#0284c7", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <RefreshCw size={20} />
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 800, color: "#0369a1", mb: 0.25 }}>Điểm cần chú ý: Đơn gợi ý</Typography>
                          <Typography variant="body2" sx={{ color: "#0c4a6e" }}>
                            Hệ thống gợi ý gia hạn đơn: <strong>{selectedCustomerRenewTargetOrder.order_id}</strong> ({selectedCustomerRenewTargetOrder.plan_name})
                          </Typography>
                        </Box>
                      </Box>
                    ) : null}

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6" sx={{ fontWeight: 800, mb: 1.5 }}>Các gói và Coupon đang có</Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                        {selectedCustomer.groups.length ? selectedCustomer.groups.map(g => <Chip key={g} label={g} variant="outlined" sx={{ fontWeight: 600, bgcolor: "background.paper" }} />) : null}
                        {selectedCustomer.coupons.length ? selectedCustomer.coupons.map(c => <Chip key={c} label={`Coupon: ${c}`} variant="outlined" color="primary" sx={{ fontWeight: 600 }} />) : null}
                        {(!selectedCustomer.groups.length && !selectedCustomer.coupons.length) ? <Typography color="text.secondary" variant="body2">Chưa có dữ liệu gói hay coupon</Typography> : null}
                      </Box>
                    </Box>
                  </Box>
                ) : null}

                {customerDetailTab === "orders" ? (
                  <>
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr 1fr", lg: "repeat(4, minmax(0, 1fr))" }, mb: 2 }}>
                      <Metric label="Đơn hôm nay" value={String(selectedCustomerOrders.filter((item) => isWithinPeriod(item.created_at, "today")).length)} icon={<CalendarClock size={16} />} />
                      <Metric label="Đơn tháng này" value={String(selectedCustomerOrders.filter((item) => isWithinPeriod(item.created_at, "month")).length)} icon={<BarChart3 size={16} />} />
                      <Metric label="Đã thanh toán" value={String(selectedCustomerOrders.filter((item) => item.status === "PAID").length)} icon={<CheckCircle2 size={16} />} />
                      <Metric label="Trạng thái còn lại" value={String(selectedCustomerOrders.filter((item) => item.status !== "PAID").length)} icon={<Activity size={16} />} />
                    </Box>
                    <Tabs
                      value={customerOrderTab}
                      onChange={(_, next) => setCustomerOrderTab(next)}
                      variant="scrollable"
                      scrollButtons="auto"
                      textColor="inherit"
                      indicatorColor="primary"
                      sx={{ ...customerPopupTabSx, mb: 2 }}
                    >
                      <Tab value="paid" label={`Đã thanh toán (${selectedCustomerOrders.filter((item) => item.status === "PAID").length})`} />
                      <Tab value="other" label={`Trạng thái còn lại (${selectedCustomerOrders.filter((item) => item.status !== "PAID").length})`} />
                    </Tabs>
                    <Box sx={{ display: "grid", gap: 2 }}>
                      {selectedCustomerOrders.filter((item) => {
                        if (customerOrderTab === "paid") return item.status === "PAID";
                        if (customerOrderTab === "other") return item.status !== "PAID";
                        return item.status === "PAID";
                      }).map(order => (
                        <Box key={order.order_id} className={order.status === "PAID" && isOrderActive(order) ? "claude-glow-hover" : ""} sx={{ p: 2, borderRadius: 3, bgcolor: "background.paper", border: 1, borderColor: "divider", boxShadow: "0 4px 12px rgba(15,23,42,0.03)", transition: "transform 0.2s", '&:hover': { transform: "translateY(-2px)" } }}>
                          <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between", mb: 1.5, pb: 1.5, borderBottom: "1px dashed", borderColor: "divider" }}>
                            <Box>
                              <Typography sx={{ fontWeight: 800 }}>{order.order_id}</Typography>
                              <Typography variant="caption" color="text.secondary">{dateText(order.created_at)}</Typography>
                            </Box>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Chip size="small" label={order.status} sx={{ ...statusChipSx(order.status === "PAID" ? "success" : "muted"), fontWeight: 800, height: 22 }} />
                              {isOrderActive(order) ? <Chip size="small" label="Active" color="success" variant="outlined" sx={{ height: 22, fontWeight: 800 }} /> : null}
                              <Button variant="outlined" size="small" sx={{ borderRadius: 999, height: 28, minWidth: 0, px: 1.5 }}>Chi tiết</Button>
                            </Stack>
                          </Stack>
                          
                          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr" }, gap: 2 }}>
                            <Box>
                              <Typography variant="caption" color="text.secondary">Gói / Group</Typography>
                              <Typography variant="body2" sx={{ fontWeight: 700, mt: 0.25 }}>{order.plan_name}</Typography>
                              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.25 }}>{order.bot_config?.channel_post_group_name || "—"}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="text.secondary">Coupon / Note</Typography>
                              <Box sx={{ mt: 0.25 }}>
                                {order.coupon ? <Chip size="small" label={order.coupon} variant="outlined" sx={{ height: 20, fontSize: 11 }} /> : <Typography variant="caption" sx={{ bgcolor: "action.hover", px: 0.75, py: 0.25, borderRadius: 1 }}>Không coupon</Typography>}
                              </Box>
                              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.25 }}>{order.note || "Không có ghi chú"}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="text.secondary">Hạn dùng</Typography>
                              <Typography variant="body2" sx={{ fontWeight: 700, mt: 0.25 }}>{order.expire_at ? dateText(order.expire_at) : "Vĩnh viễn"}</Typography>
                            </Box>
                          </Box>
                        </Box>
                      ))}
                      {selectedCustomerOrders.filter((item) => (customerOrderTab === "paid" ? item.status === "PAID" : item.status !== "PAID")).length === 0 && (
                        <Typography color="text.secondary" sx={{ textAlign: "center", py: 4 }}>Không có đơn hàng nào.</Typography>
                      )}
                    </Box>
                  </>
                ) : null}

                {customerDetailTab === "groups" ? (
                    <>
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr 1fr", lg: "repeat(4, minmax(0, 1fr))" }, mb: 1.5 }}>
                      <Metric label="Group active" value={String(selectedCustomer.activeOrders.length)} icon={<Users size={16} />} />
                      <Metric label="Còn trong hệ thống" value={selectedCustomerActiveGroups.length ? String(selectedCustomerActiveGroups.length) : "0"} icon={<ShieldCheck size={16} />} />
                      <Metric label="Audit group" value={String(selectedCustomerGroupAuditSummary.total)} icon={<ClipboardList size={16} />} />
                      <Metric label="Có live check" value={String(selectedCustomerGroupAuditSummary.liveChecked)} icon={<Eye size={16} />} />
                    </Box>
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr 1fr", lg: "repeat(4, minmax(0, 1fr))" }, mb: 1.5 }}>
                      <Metric label="Giữ quyền" value={String(selectedCustomerGroupAuditSummary.retained)} icon={<CheckCircle2 size={16} />} />
                      <Metric label="Đã kick" value={String(selectedCustomerGroupAuditSummary.kicked)} icon={<XCircle size={16} />} />
                      <Metric label="Nhóm hiện tại" value={String(selectedCustomerGroupAuditSummary.currentGroups)} icon={<Users size={16} />} />
                      <Metric label="Có dữ liệu lịch sử" value={String(selectedCustomerGroupAuditSummary.total > 0 ? 1 : 0)} icon={<Activity size={16} />} />
                    </Box>
                    <section className="panel nested-panel" style={{ borderTopWidth: 3, borderTopStyle: "solid", borderTopColor: "var(--mui-palette-primary-main)" }}>
                      <PanelHead title="Nhóm còn active" subtitle="Danh sách group user vẫn còn quyền, ưu tiên nhìn nhanh khi rà soát." />
                      {selectedCustomerActiveGroups.length ? (
                        <div
                          className="tag-list"
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "10px",
                            padding: "6px 0 2px",
                          }}
                        >
                          {selectedCustomerActiveGroups.map((group) => (
                            <span
                              key={group}
                              style={{
                                fontSize: "14px",
                                fontWeight: 800,
                                padding: "10px 14px",
                                borderRadius: "999px",
                                background: "linear-gradient(135deg, rgba(37,99,235,0.12), rgba(14,165,233,0.08))",
                                border: "1px solid rgba(37,99,235,0.18)",
                                color: "#1e3a8a",
                                boxShadow: "0 8px 18px rgba(37,99,235,0.08)",
                              }}
                            >
                              {group}
                            </span>
                          ))}
                        </div>
                      ) : <div className="empty-card">Chưa có nhóm active nào.</div>}
                    </section>
                    <section className="panel nested-panel">
                      <PanelHead title="Dấu vết group" subtitle="Audit mà bot ghi nhận được từ quyền hiện tại, live check và trạng thái kick/giữ quyền." />
                      {selectedCustomerGroupAuditRows.length ? (
                        <SimpleTable
                          headers={["Trạng thái", "Group", "Gói / Đơn", "Hạn dùng", "Live", "Chi tiết"]}
                          rows={selectedCustomerGroupAuditRows}
                        />
                      ) : (
                        <div className="empty-card">Chưa có audit group nào cho khách này.</div>
                      )}
                    </section>
                  </>
                ) : null}
                {customerDetailTab === "timeline" ? (
                  <>
                    <Tabs
                      value={customerTimelineSubTab}
                      onChange={(_, next) => setCustomerTimelineSubTab(next)}
                      variant="scrollable"
                      scrollButtons="auto"
                      textColor="inherit"
                      indicatorColor="primary"
                      sx={{ ...customerPopupTabSx, mb: 2 }}
                    >
                      <Tab value="all" label="Tất cả" />
                      <Tab value="joinLeft" label="Join/Left" />
                      <Tab value="role" label="Quyền" />
                      <Tab value="restricted" label="Hạn chế" />
                      <Tab value="kickMute" label="Kick/Mute" />
                      <Tab value="orders" label="Order timeline" />
                    </Tabs>
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr 1fr", lg: "repeat(4, minmax(0, 1fr))" }, mb: 1.5 }}>
                      <Metric label="Tổng sự kiện" value={String(selectedCustomerTimelineCounts.total)} icon={<Activity size={16} />} />
                      <Metric label="Join" value={String(selectedCustomerTimelineCounts.joined)} icon={<Plus size={16} />} />
                      <Metric label="Left" value={String(selectedCustomerTimelineCounts.left)} icon={<TrendingUp size={16} />} />
                      <Metric label="Kick / mute" value={`${selectedCustomerTimelineCounts.kicked} / ${selectedCustomerTimelineCounts.muted}`} icon={<XCircle size={16} />} />
                    </Box>
                    <section className="panel nested-panel">
                      <PanelHead title="Timeline group" subtitle="Lịch sử join / out / mute / kick / nhắc gia hạn của khách theo dữ liệu bot theo dõi được." />
                      <SimpleTable
                        headers={["Sự kiện", "Group", "Đơn", "Giờ", "Chi tiết"]}
                        rows={selectedCustomerTimelineRows.slice(0, 12)}
                      />
                    </section>
                  </>
                  ) : null}
              </Box>
            </DialogContent>
          </Dialog>
        ) : null}"""

content = content[:start_idx] + new_block + content[end_idx:]

with open("app/page.tsx", "w") as f:
    f.write(content)

print("Updated customer modal in page.tsx successfully.")
