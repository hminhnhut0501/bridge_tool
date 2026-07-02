import sys

with open("app/page.tsx", "r") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i in range(len(lines)):
    if '        {tab === "overview" ? (' in lines[i]:
        start_idx = i
    if '        {tab === "analytics" ? (' in lines[i]:
        end_idx = i - 1
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find blocks")
    sys.exit(1)

new_content = """        {tab === "overview" ? (
          <Stack spacing={2.5} sx={{ animation: "fadeUp 0.6s ease-out both" }}>
            {/* Top Status Widgets */}
            <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
              <Metric label="Đơn chờ xử lý" value={String(overviewPriorityAlerts.filter(a => a.tone === "bad").length)} accent="rose" icon={<ShieldCheck size={16} />} note="Cần xử lý khẩn cấp" />
              <Metric label="Cấu hình hệ thống" value={overviewHealthAlerts.find(a => a.title === "Thiếu cấu hình") ? "Yêu cầu cấu hình" : "Đầy đủ"} accent="amber" icon={<CreditCard size={16} />} note={overviewHealthAlerts.find(a => a.title === "Thiếu cấu hình")?.detail || "Hoạt động bình thường"} />
              <Metric label="Khách sắp hết hạn" value={String(overviewExpiringCustomers.length)} accent="cyan" icon={<CalendarClock size={16} />} note="Trong 3 ngày tới" />
              <Metric label="Trạng thái Webhook" value={webhook?.url ? "Hoạt động" : "Chưa cấu hình"} accent={webhook?.url ? "emerald" : "rose"} icon={<TrendingUp size={16} />} note={webhook?.url ? "Đang nhận tín hiệu" : "Cần thiết lập ngay"} />
            </Box>

            <Box sx={{ display: "grid", gap: 2.5, gridTemplateColumns: { xs: "1fr", lg: "280px 1fr" } }}>
              {/* Left Column: System Status Sidebar */}
              <Card variant="outlined" sx={{ ...sectionCardSx, height: "fit-content", animation: "fadeUp 0.5s ease-out 0.1s both" }}>
                <PanelHead title="Trạng thái hệ thống" subtitle="Giám sát thời gian thực" />
                <Stack spacing={1.5} sx={{ p: 2 }}>
                  <HealthItem ok={Boolean(webhook?.url) && !webhookMeta?.maintenance_override?.active && !webhookMeta?.problem_reason} title="Webhook" detail={webhookMeta?.maintenance_override?.active ? (webhookMeta.maintenance_override.reason || "Bot đang bảo trì") : webhookMeta?.problem_reason ? `Lỗi: ${webhookMeta.problem_reason}` : webhook?.url || "Chưa set webhook"} />
                  <HealthItem ok={botScheduleStatus?.active ?? true} title="Bot runtime" detail={botScheduleStatus?.title || "Bot runtime"} />
                  <HealthItem ok={configuredGroups.length > 0} title="Nhóm nhận link" detail={configuredGroups.length ? `Đã có ${configuredGroups.length} nhóm` : "Vào Nhóm & giá để cấu hình"} />
                  <HealthItem ok={metrics.menu > 0} title="Menu bot" detail={`${metrics.menu} trang menu`} />
                  <Button variant="outlined" size="small" fullWidth onClick={() => loadAll(savedSecret, { silent: false, resetPages: false, scope: "overview" })} sx={{ mt: 1, fontWeight: 700, borderRadius: "10px" }}>Tải lại trạng thái</Button>
                </Stack>
              </Card>

              {/* Right Column: iOS-style Notification Center */}
              <Card variant="outlined" sx={{ ...sectionCardSx, animation: "fadeUp 0.5s ease-out 0.2s both" }}>
                <PanelHead
                  title="Trung tâm thông báo"
                  subtitle="Tất cả biến động, đơn hàng, và sự kiện mới nhất"
                  action={
                    <Button variant="outlined" size="small" onClick={() => selectTab("analytics")}>Xem thống kê chi tiết</Button>
                  }
                />
                <Box sx={{ p: 2 }}>
                  {(() => {
                    const combinedNotifications: any[] = [];

                    // 1. Priority alerts
                    overviewPriorityAlerts.forEach((alert, i) => {
                      combinedNotifications.push({
                        id: `alert-${i}`,
                        type: "alert",
                        title: alert.title,
                        body: alert.detail,
                        dateObj: new Date(),
                        tone: alert.tone === "bad" ? "rose" : "amber",
                        icon: <ShieldCheck size={18} />,
                        actionLabel: "Cấu hình",
                        onAction: () => selectTab("setup")
                      });
                    });

                    // 2. Recent orders
                    overviewRecentOrders.forEach((order) => {
                      combinedNotifications.push({
                        id: `order-${order.order_id}`,
                        type: "order",
                        title: `Đơn hàng mới #${order.order_id}`,
                        body: `${order.full_name || "Khách"} đã tạo đơn gói "${order.plan_name}". Trạng thái: ${orderLifecycleLabel(order)}`,
                        dateObj: new Date(order.created_at),
                        tone: order.status === "PAID" ? "emerald" : order.status === "PENDING" ? "amber" : "rose",
                        icon: <CreditCard size={18} />,
                        actionLabel: "Xem đơn",
                        onAction: () => selectTab("orders")
                      });
                    });

                    // 3. User Activity
                    overviewRecentUserActivity.forEach((act) => {
                      const userLabel = customerNameById.get(act.telegram_user_id || payloadText(act.payload || {}, "user_id")) || payloadText(act.payload || {}, "full_name") || payloadText(act.payload || {}, "username") || act.telegram_user_id || "-";
                      const eventLabel = activityEventLabel(payloadText(act.payload || {}, "event_type") || act.event_name || "event");
                      const detail = payloadText(act.payload || {}, "message_text") || payloadText(act.payload || {}, "source_ref") || payloadText(act.payload || {}, "activation_code") || "-";
                      combinedNotifications.push({
                        id: `activity-${act.id}`,
                        type: "activity",
                        title: `Tương tác: ${userLabel}`,
                        body: `Sự kiện: ${eventLabel} • ${detail}`,
                        dateObj: new Date(act.created_at),
                        tone: "blue",
                        icon: <Users size={18} />,
                        actionLabel: "Nhật ký",
                        onAction: () => selectTab("activityLog")
                      });
                    });

                    // 4. New Customers
                    overviewNewCustomers.forEach((cust) => {
                      combinedNotifications.push({
                        id: `customer-${cust.id}`,
                        type: "customer",
                        title: `Khách hàng mới: ${cust.name || cust.id}`,
                        body: `Gói: ${cust.plans[0] || "Chưa rõ"} • Tổng thanh toán: ${money(cust.revenue)}`,
                        dateObj: new Date(cust.lastOrderAt),
                        tone: "indigo",
                        icon: <Users size={18} />,
                        actionLabel: "Khách hàng",
                        onAction: () => selectTab("customers")
                      });
                    });

                    // 5. Expiring Customers
                    overviewExpiringCustomers.forEach((cust) => {
                      const targetOrder = cust.activeOrders[0] || cust.paidOrders[0] || null;
                      const expireAt = targetOrder?.expire_at || cust.latestExpire;
                      combinedNotifications.push({
                        id: `expiring-${cust.id}`,
                        type: "expiring",
                        title: `Hết hạn sắp tới: ${cust.name || cust.id}`,
                        body: `Gói: ${targetOrder?.plan_name || cust.plans[0]} • Còn lại: ${daysUntil(expireAt)} ngày (Hạn: ${dateText(expireAt)})`,
                        dateObj: new Date(expireAt),
                        tone: "rose",
                        icon: <CalendarClock size={18} />,
                        actionLabel: "Gia hạn",
                        onAction: () => selectTab("renewals")
                      });
                    });

                    // Sort descending
                    combinedNotifications.sort((a, b) => b.dateObj.getTime() - a.dateObj.getTime());

                    if (combinedNotifications.length === 0) {
                      return (
                        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: 200, color: "text.secondary" }}>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>Không có thông báo mới.</Typography>
                        </Box>
                      );
                    }

                    return (
                      <Box className="notif-container">
                        {combinedNotifications.slice(0, 15).map((notif, i) => {
                          const toneData = tonePalette[notif.tone as keyof typeof tonePalette] || tonePalette.neutral;
                          const accentColor = toneData.main;
                          return (
                            <Box
                              key={notif.id}
                              className="notif-card"
                              sx={{
                                animation: `slideInRight 0.4s ease-out ${i * 0.05}s both`
                              }}
                            >
                              <Box className="notif-icon-wrapper" sx={{ bgcolor: toneData.bg, color: accentColor }}>
                                {notif.icon}
                              </Box>
                              <Box className="notif-content">
                                <Box className="notif-header">
                                  <span className="notif-title">{notif.title}</span>
                                  <span className="notif-time">{getRelativeTime(notif.dateObj)}</span>
                                </Box>
                                <span className="notif-body">{notif.body}</span>
                                {notif.onAction && (
                                  <Box className="notif-footer">
                                    <Button
                                      size="small"
                                      variant="text"
                                      onClick={notif.onAction}
                                      className="notif-action-btn"
                                      sx={{ color: accentColor, "&:hover": { bgcolor: toneData.bg } }}
                                    >
                                      {notif.actionLabel}
                                    </Button>
                                  </Box>
                                )}
                              </Box>
                            </Box>
                          );
                        })}
                      </Box>
                    );
                  })()}
                </Box>
              </Card>
            </Box>
          </Stack>
        ) : null}
"""

with open("app/page.tsx", "w") as f:
    f.writelines(lines[:start_idx])
    f.write(new_content)
    f.writelines(lines[end_idx:])

print(f"Replaced {end_idx - start_idx} lines with {len(new_content.splitlines())} lines")
