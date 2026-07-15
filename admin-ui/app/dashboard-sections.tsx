"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, Chip, Stack, Tab, Tabs, TextField } from "@mui/material";
import { Download, Plus, Users, BadgeDollarSign, CalendarClock, ShieldCheck, TrendingUp, CreditCard, Settings, Clock3 } from "lucide-react";
import { AppSection, AppToolbar, RevenueBarChart, BreakdownChart, DonutChart, Pagination, OrdersTable, TrendTable } from "./dashboard-components";
import { Metric } from "./metric-card";
import { orderAmountValue } from "./dashboard-helpers";

export function AnalyticsSection(props: any) {
  const { orders, monthStats, paidRevenueByCurrency, paidRevenueByProvider, isWithinPeriod, marketingStats, marketingRange, refreshMarketingStats } = props;
  const stats = marketingStats?.data || marketingStats || null;
  const monthGroups = props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")), "day");
  const yearGroups = props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "year")), "month");
  const monthPeak = Math.max(1, ...monthGroups.map((item: any) => item.stats.revenue));
  const yearPeak = Math.max(1, ...yearGroups.map((item: any) => item.stats.revenue));
  const monthChartData = monthGroups.map((item: any) => ({
    label: item.label,
    revenue: Number(item.stats.revenue || 0),
    customers: item.stats.customers || 0,
    aov: props.ordersAverageMoney(item.items),
  }));
  const rangeChartData = (stats?.time_stats?.by_day || []).map((item: any) => ({
    label: item.day,
    revenue: Number(item.revenue || 0),
    customers: Number(item.customers || 0),
    aov: props.formatRevenueCurrency("VND", item.orders ? Number(item.revenue || 0) / Number(item.orders || 1) : 0),
  }));
  const paymentStatusBreakdown = [
    { label: "PAID", value: monthStats.paid },
    { label: "PENDING", value: monthStats.pending },
    { label: "CANCELLED", value: monthStats.cancelled },
    { label: "EXPIRED", value: monthStats.expired },
  ];
  const currencyBreakdown = [
    { label: "VND", value: (paidRevenueByCurrency.VND || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + orderAmountValue(item), 0) },
    { label: "USD", value: (paidRevenueByCurrency.USD || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + orderAmountValue(item), 0) },
    { label: "CRYPTO", value: (paidRevenueByCurrency.CRYPTO || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + orderAmountValue(item), 0) },
  ].filter((item) => item.value > 0);
  const providerBreakdown = [
    { label: "PayOS", value: paidRevenueByProvider.PAYOS || 0 },
    { label: "PayPal", value: paidRevenueByProvider.PAYPAL || 0 },
    { label: "USDT TRC20", value: paidRevenueByProvider.TRON_USDT || 0 },
  ].filter((item) => item.value > 0);
  const trendRows = (groups: any[], peak: number) => groups.map((item, idx) => {
    const revenue = Number(item.stats.revenue || 0);
    const prevRevenue = Number(groups[idx - 1]?.stats?.revenue || 0);
    const trend = idx === 0 ? 0 : revenue === prevRevenue ? 0 : revenue > prevRevenue ? 1 : -1;
    const conversionColor: "good" | "warn" | "bad" = item.stats.conversion >= 80 ? "good" : item.stats.conversion >= 50 ? "warn" : "bad";
    return {
      label: item.label,
      revenue: props.ordersMoney(item.items.filter((row: any) => row.status === "PAID")),
      paid: item.stats.paid,
      pending: item.stats.pending,
      customers: item.stats.customers,
      aov: props.ordersAverageMoney(item.items),
      coupon: props.ordersMoney(item.items.filter((row: any) => row.status === "PAID"), "coupon_discount_amount"),
      conversion: `${item.stats.conversion}%`,
      conversionColor,
      barWidth: Math.round((revenue / peak) * 100),
      trend,
      sparkline: groups.slice(Math.max(0, idx - 6), idx + 1).map((entry: any) => Number(entry.stats.revenue || 0)),
    };
  }) as {
    label: string;
    revenue: string;
    paid: number;
    pending: number;
    customers: number;
    aov: string;
    coupon: string;
    conversion: string;
    conversionColor: "good" | "warn" | "bad";
    barWidth: number;
    trend: number;
    sparkline: number[];
  }[];
  const monthOrdersPaid = orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "month"));
  const monthCustomers = new Set(monthOrdersPaid.map((item: any) => item.telegram_user_id)).size;
  const compareDelta = Number(stats?.revenue_compare?.delta || 0);
  const compareDeltaPct = stats?.revenue_compare?.delta_percent;
  const compareTone: "good" | "warn" | "bad" = compareDelta >= 0 ? "good" : "bad";
  const topPlans = (stats?.plan_stats || []).slice(0, 6);
  const topActivePlans = [...(stats?.plan_stats || [])].sort((a: any, b: any) => (b.active_customers || 0) - (a.active_customers || 0)).slice(0, 6);
  const timeByHour = (stats?.time_stats?.by_hour || []).slice().sort((a: any, b: any) => String(a.hour).localeCompare(String(b.hour)));
  const timeByDay = (stats?.time_stats?.by_day || []).slice().sort((a: any, b: any) => String(a.day).localeCompare(String(b.day)));
  const topPaymentProviders = (stats?.payment_breakdown?.by_provider || []).slice(0, 6);
  const topCurrencies = (stats?.payment_breakdown?.by_currency || []).slice(0, 6);
  const topByDay = (stats?.top_by_period?.day || []).slice(0, 8);
  const topByHour = (stats?.top_by_period?.hour || []).slice(0, 8);
  const topByWeekday = (stats?.top_by_period?.weekday || []).slice(0, 8);
  const cohortHeatmap = stats?.cohort_heatmap || [];
  const providerCohorts = stats?.provider_cohorts || [];
  const buyerTypePlanRows = stats?.buyer_type_plan_rows || [];
  const opportunityAlerts = stats?.opportunity_alerts || [];
  const timeRangeLabel = stats?.range || marketingRange || "month";
  const chartSubtitle = `Biểu đồ trực quan hóa xu hướng dòng tiền tăng trưởng ${timeRangeLabel === "today" ? "trong ngày" : timeRangeLabel === "7d" ? "trong 7 ngày" : timeRangeLabel === "year" ? "trong năm" : "trong tháng"}.`;
  const formatMoney = (value: number, currency = "VND") => props.formatRevenueCurrency(currency, Number(value || 0));
  const heatFill = (score: number) => {
    const clamped = Math.max(0, Math.min(100, score));
    const alpha = 0.1 + clamped * 0.007;
    if (clamped >= 70) return `rgba(16, 185, 129, ${Math.min(alpha, 0.9)})`;
    if (clamped >= 40) return `rgba(59, 130, 246, ${Math.min(alpha, 0.75)})`;
    return `rgba(244, 63, 94, ${Math.min(alpha, 0.65)})`;
  };

  return (
    <Stack spacing={2.5}>
      <Box sx={{ p: { xs: 2, md: 2.5 }, borderRadius: 4, border: "1px solid", borderColor: "rgba(59,130,246,0.18)", bgcolor: "linear-gradient(135deg, rgba(248,250,252,0.96), rgba(239,246,255,0.92))", boxShadow: "0 18px 40px rgba(15,23,42,0.06)" }}>
        <Box sx={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 2, alignItems: "center" }}>
          <Box sx={{ minWidth: 0 }}>
            <Chip size="small" label="Marketing intelligence" color="primary" variant="outlined" sx={{ mb: 1 }} />
            <Box sx={{ fontSize: { xs: 24, md: 30 }, fontWeight: 900, letterSpacing: "-0.03em", color: "#0f172a", lineHeight: 1.1 }}>
              Dashboard marketing cho quyết định tăng trưởng
            </Box>
            <Box sx={{ mt: 1, color: "text.secondary", maxWidth: 760 }}>
              Theo dõi doanh thu, cohort, nguồn thanh toán, tín hiệu giảm của từng gói và các cơ hội upsell trong một màn hình duy nhất.
            </Box>
          </Box>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            <Chip label={`Kỳ: ${timeRangeLabel}`} color="primary" variant="outlined" />
            <Chip label={`Revenue delta: ${compareDeltaPct === null || compareDeltaPct === undefined ? "N/A" : `${compareDeltaPct > 0 ? "+" : ""}${compareDeltaPct}%`}`} color={compareTone === "good" ? "success" : "error"} variant="outlined" />
            <Chip label={`Alerts: ${opportunityAlerts.length}`} color={opportunityAlerts.length ? "warning" : "default"} variant="outlined" />
          </Box>
        </Box>
      </Box>

      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, alignItems: "center", justifyContent: "space-between", p: 1.5, border: "1px solid", borderColor: "divider", borderRadius: 3, bgcolor: "rgba(248,250,252,0.85)" }}>
        <Tabs
          value={marketingRange}
          onChange={(_, next) => {
            refreshMarketingStats?.(next);
          }}
          variant="scrollable"
          scrollButtons="auto"
          textColor="inherit"
          indicatorColor="primary"
          sx={{ minHeight: 42, "& .MuiTab-root": { minHeight: 42, fontWeight: 800, textTransform: "none" } }}
        >
          <Tab value="today" label="Hôm nay" />
          <Tab value="7d" label="7 ngày" />
          <Tab value="month" label="Tháng này" />
          <Tab value="year" label="Năm nay" />
        </Tabs>
        <Button variant="outlined" size="small" onClick={() => refreshMarketingStats?.()} startIcon={<Settings size={16} />}>
          Tải lại insight
        </Button>
      </Box>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
        {[
          <Metric key="rev" label="Doanh thu tháng này" value={props.ordersMoney(monthOrdersPaid)} accent="blue" icon={<TrendingUp size={16} />} note={compareDeltaPct === null || compareDeltaPct === undefined ? "Chưa có dữ liệu kỳ trước" : `${compareDeltaPct > 0 ? "+" : ""}${compareDeltaPct}% so với kỳ trước`} />,
          <Metric key="cust" label="Khách mua tháng này" value={String(monthCustomers)} accent="cyan" icon={<Users size={16} />} note="Cần tiếp tục nuôi tệp để tăng LTV" />,
          <Metric key="aov" label="AOV tháng này" value={props.ordersAverageMoney(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")))} accent="emerald" icon={<CreditCard size={16} />} note={`${String(stats?.retention_stats?.active_customers ?? 0)} khách active đang mở cơ hội upsell`} />,
          <Metric key="conv" label="Tỉ lệ thanh toán" value={`${monthStats.conversion}%`} accent="indigo" icon={<ShieldCheck size={16} />} note={`Đã trả: ${monthStats.paid} / Tổng: ${monthStats.paid + monthStats.pending + monthStats.cancelled + monthStats.expired} đơn`} />,
        ].map((card, i) => (
          <Box key={i} sx={{ height: "100%", animation: `fadeUp 0.5s ease-out ${i * 0.1}s both` }}>{card}</Box>
        ))}
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" } }}>
        <Metric label="Renewal rate" value={`${Number(stats?.retention_stats?.renewal_rate || 0)}%`} accent="amber" icon={<CalendarClock size={16} />} note={`${Number(stats?.retention_stats?.renewal_orders || 0)} đơn gia hạn • ${Number(stats?.retention_stats?.renewal_customers || 0)} khách`} />
        <Metric label="Lifetime upgrade" value={`${Number(stats?.retention_stats?.lifetime_upgrade_rate || 0)}%`} accent="violet" icon={<BadgeDollarSign size={16} />} note={`${Number(stats?.retention_stats?.lifetime_upgrades || 0)} khách upgrade • ${Number(stats?.retention_stats?.upgrade_from_30d || 0)} từ gói 30 ngày`} />
        <Metric label="Active khách" value={String(stats?.retention_stats?.active_customers ?? 0)} accent="cyan" icon={<Users size={16} />} note={`${String(stats?.retention_stats?.active_orders ?? 0)} đơn còn hạn / active`} />
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" } }}>
        <Box sx={{ p: 2, borderRadius: 4, border: "1px solid", borderColor: "divider", bgcolor: "background.paper" }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1, mb: 1 }}>
            <Box>
              <Box sx={{ fontWeight: 900, fontSize: 18 }}>Insight cards</Box>
              <Box className="muted">Các tín hiệu marketing nổi bật trong kỳ</Box>
            </Box>
            <Chip size="small" label={`${stats?.insights?.length || 0} insight`} color="primary" variant="outlined" />
          </Box>
          <Box sx={{ display: "grid", gap: 1.25, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
            {stats?.insights?.length ? stats.insights.map((item: any) => (
              <Box key={item.title} sx={{ p: 2, borderRadius: 3, border: "1px solid", borderColor: "divider", bgcolor: "rgba(248,250,252,0.9)" }}>
                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}>
                  <strong>{item.title}</strong>
                  <Chip size="small" label={item.tone === "good" ? "Tốt" : item.tone === "warning" ? "Cần xem" : "Rủi ro"} color={item.tone === "good" ? "success" : item.tone === "warning" ? "warning" : "error"} variant="outlined" />
                </Box>
                <div className="muted" style={{ marginTop: 8 }}>{item.detail}</div>
              </Box>
            )) : <Box className="muted" sx={{ p: 1.5 }}>Chưa có insight nổi bật.</Box>}
          </Box>
        </Box>
        <Box sx={{ p: 2, borderRadius: 4, border: "1px solid", borderColor: "divider", bgcolor: "background.paper" }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1, mb: 1 }}>
            <Box>
              <Box sx={{ fontWeight: 900, fontSize: 18 }}>Opportunity alerts</Box>
              <Box className="muted">Score càng cao thì tín hiệu giảm càng đáng ưu tiên</Box>
            </Box>
            <Chip size="small" label={`${opportunityAlerts.length} cảnh báo`} color={opportunityAlerts.length ? "warning" : "default"} variant="outlined" />
          </Box>
          <Box sx={{ display: "grid", gap: 1.25 }}>
            {opportunityAlerts.length ? opportunityAlerts.map((item: any) => (
              <Box key={item.title} sx={{ p: 2, borderRadius: 3, border: "1px solid", borderColor: item.tone === "good" ? "rgba(16,185,129,0.25)" : item.tone === "warning" ? "rgba(245,158,11,0.35)" : "rgba(244,63,94,0.3)", bgcolor: "rgba(248,250,252,0.95)" }}>
                <Box sx={{ display: "flex", justifyContent: "space-between", gap: 1, alignItems: "start" }}>
                  <strong>{item.title}</strong>
                  <Chip size="small" label={item.score ? `${item.score}/100` : item.tone === "good" ? "Cơ hội" : item.tone === "warning" ? "Chậm lại" : "Rủi ro"} color={item.tone === "good" ? "success" : item.tone === "warning" ? "warning" : "error"} variant="outlined" />
                </Box>
                <div className="muted" style={{ marginTop: 8 }}>{item.detail}</div>
                {item.action ? <div style={{ marginTop: 10, fontWeight: 700, color: "#0f172a" }}>{item.action}</div> : null}
              </Box>
            )) : <Box className="muted" sx={{ p: 1.5 }}>Chưa phát hiện alert giảm rõ ràng.</Box>}
          </Box>
        </Box>
      </Box>

      <Box sx={{ width: "100%", animation: "fadeUp 0.6s ease-out 0.4s both" }}>
        <RevenueBarChart title="Doanh thu theo ngày" subtitle={chartSubtitle} accent="blue" items={(rangeChartData.length ? rangeChartData : monthChartData).slice().reverse()} />
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 0.6s both" }}>
        <DonutChart title="Cơ cấu trạng thái tháng" subtitle="Tỉ trọng đơn để đọc nhanh trạng thái." accent="emerald" segments={paymentStatusBreakdown} centerLabel={`${monthStats.conversion}%`} />
        <BreakdownChart title="Doanh thu theo phương thức" subtitle="PayOS, PayPal và USDT." accent="violet" items={(topPaymentProviders.length ? topPaymentProviders : providerBreakdown).map((item: any) => ({ label: item.provider || item.label, value: Number(item.revenue ?? item.value ?? 0), note: formatMoney(Number(item.revenue ?? item.value ?? 0), item.currency || "VND") }))} valueFormatter={(value: number) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value)} />
        <BreakdownChart title="Doanh thu theo currency" subtitle="Biết ngay dòng tiền chính nằm ở đâu." accent="cyan" items={(topCurrencies.length ? topCurrencies : currencyBreakdown).map((item: any) => ({ label: item.currency || item.label, value: Number(item.revenue ?? item.value ?? 0), note: formatMoney(Number(item.revenue ?? item.value ?? 0), item.currency || item.label || "VND") }))} valueFormatter={(value: number, label: string) => props.formatRevenueCurrency(label, value)} />
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 0.7s both" }}>
        <div className="table-wrap summary-wrap">
          <table>
            <thead>
              <tr><th>Gói</th><th>Đơn</th><th>Doanh thu</th><th>Active</th><th>AOV</th><th>Lifetime</th></tr>
            </thead>
            <tbody>
              {topPlans.length ? topPlans.map((item: any) => (
                <tr key={item.plan_name}>
                  <td><strong>{item.plan_name}</strong></td>
                  <td>{item.orders}</td>
                  <td>{formatMoney(Number(item.revenue || 0))}</td>
                  <td>{item.active_customers}</td>
                  <td>{formatMoney(Number(item.average_order || 0))}</td>
                  <td>{item.lifetime_share}%</td>
                </tr>
              )) : <tr><td colSpan={6} className="empty-state">Chưa có dữ liệu gói.</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="table-wrap summary-wrap">
          <table>
            <thead>
              <tr><th>Gói active</th><th>Active</th><th>Đơn</th><th>Doanh thu</th><th>Tỉ lệ</th></tr>
            </thead>
            <tbody>
              {topActivePlans.length ? topActivePlans.map((item: any) => (
                <tr key={`active-${item.plan_name}`}>
                  <td><strong>{item.plan_name}</strong></td>
                  <td>{item.active_customers}</td>
                  <td>{item.orders}</td>
                  <td>{formatMoney(Number(item.revenue || 0))}</td>
                  <td>{item.active_share}%</td>
                </tr>
              )) : <tr><td colSpan={5} className="empty-state">Chưa có dữ liệu active.</td></tr>}
            </tbody>
          </table>
        </div>
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 0.75s both" }}>
        <div className="table-wrap summary-wrap">
          <table>
            <thead><tr><th>Giờ</th><th>Đơn</th><th>Doanh thu</th><th>Khách</th></tr></thead>
            <tbody>
              {timeByHour.length ? timeByHour.slice().reverse().map((item: any) => (
                <tr key={`hour-${item.hour}`}>
                  <td><strong>{item.hour}</strong></td>
                  <td>{item.orders}</td>
                  <td>{formatMoney(Number(item.revenue || 0))}</td>
                  <td>{item.customers}</td>
                </tr>
              )) : <tr><td colSpan={4} className="empty-state">Chưa có dữ liệu theo giờ.</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="table-wrap summary-wrap">
          <table>
            <thead><tr><th>Ngày</th><th>Đơn</th><th>Doanh thu</th><th>Khách</th></tr></thead>
            <tbody>
              {timeByDay.length ? timeByDay.slice().reverse().map((item: any) => (
                <tr key={`day-${item.day}`}>
                  <td><strong>{item.day}</strong></td>
                  <td>{item.orders}</td>
                  <td>{formatMoney(Number(item.revenue || 0))}</td>
                  <td>{item.customers}</td>
                </tr>
              )) : <tr><td colSpan={4} className="empty-state">Chưa có dữ liệu theo ngày.</td></tr>}
            </tbody>
          </table>
        </div>
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 0.78s both" }}>
        <Metric label="Ngày peak" value={String(stats?.top_periods?.day?.label || "-")} accent="blue" icon={<CalendarClock size={16} />} note={`${props.formatRevenueCurrency("VND", Number(stats?.top_periods?.day?.revenue || 0))} • ${Number(stats?.top_periods?.day?.orders || 0)} đơn`} />
        <Metric label="Thứ peak" value={String(stats?.top_periods?.weekday?.label || "-")} accent="amber" icon={<TrendingUp size={16} />} note={`${props.formatRevenueCurrency("VND", Number(stats?.top_periods?.weekday?.revenue || 0))} • ${Number(stats?.top_periods?.weekday?.orders || 0)} đơn`} />
        <Metric label="Giờ peak" value={String(stats?.top_periods?.hour?.label || "-")} accent="violet" icon={<Clock3 size={16} />} note={`${props.formatRevenueCurrency("VND", Number(stats?.top_periods?.hour?.revenue || 0))} • ${Number(stats?.top_periods?.hour?.orders || 0)} đơn`} />
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 0.82s both" }}>
        <Box sx={{ p: 2, borderRadius: 4, border: "1px solid", borderColor: "divider", bgcolor: "background.paper" }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 1, mb: 1.5 }}>
            <Box>
              <Box sx={{ fontSize: 18, fontWeight: 900 }}>Cohort retention heatmap</Box>
              <Box className="muted">7 ngày và 30 ngày, nhìn nhanh retention / renewal / upgrade</Box>
            </Box>
            <Chip size="small" label="Heatmap" color="primary" variant="outlined" />
          </Box>
          <Box sx={{ display: "grid", gap: 1 }}>
            <Box sx={{ display: "grid", gridTemplateColumns: "90px repeat(4, minmax(0, 1fr))", gap: 0.75, fontSize: 12, fontWeight: 800, color: "text.secondary" }}>
              <Box>Window</Box><Box>Base</Box><Box>Retention</Box><Box>Renewal</Box><Box>Upgrade</Box>
            </Box>
            {cohortHeatmap.length ? cohortHeatmap.map((item: any) => (
              <Box key={item.window} sx={{ display: "grid", gridTemplateColumns: "90px repeat(4, minmax(0, 1fr))", gap: 0.75, alignItems: "stretch" }}>
                <Box sx={{ display: "flex", alignItems: "center", fontWeight: 900 }}>{item.window}</Box>
                {item.cells.map((cell: any) => (
                  <Box key={cell.key} sx={{ p: 1.1, borderRadius: 2, border: "1px solid rgba(15,23,42,0.08)", bgcolor: heatFill(cell.score), minHeight: 54 }}>
                    <Box sx={{ fontSize: 11, color: "rgba(15,23,42,0.7)", fontWeight: 800 }}>{cell.label}</Box>
                    <Box sx={{ fontSize: 18, fontWeight: 900, color: "#0f172a" }}>{cell.value}</Box>
                  </Box>
                ))}
              </Box>
            )) : <Box className="empty-state">Chưa có dữ liệu cohort heatmap.</Box>}
          </Box>
        </Box>
        <div className="table-wrap summary-wrap">
          <table>
            <thead><tr><th>Provider</th><th>Base</th><th>Retention</th><th>Renewal</th><th>Upgrade</th></tr></thead>
            <tbody>
              {providerCohorts.length ? providerCohorts.map((item: any) => (
                <tr key={item.provider}>
                  <td><strong>{item.provider}</strong></td>
                  <td>{item.base_users}</td>
                  <td>{item.retention_rate}%</td>
                  <td>{item.renewal_rate}%</td>
                  <td>{item.upgrade_rate}%</td>
                </tr>
              )) : <tr><td colSpan={5} className="empty-state">Chưa có dữ liệu theo provider.</td></tr>}
            </tbody>
          </table>
        </div>
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 0.95s both" }}>
        <TrendTable title="Theo dõi tăng trưởng theo ngày" subtitle="Doanh thu, số đơn, khách trả tiền và tỉ lệ thanh toán trong tháng." rows={trendRows(monthGroups, monthPeak)} />
      </Box>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 1s both" }}>
        <div className="table-wrap summary-wrap">
          <table>
            <thead><tr><th>Ngày</th><th>Gói top</th><th>Đơn</th><th>Doanh thu</th></tr></thead>
            <tbody>
              {topByDay.length ? topByDay.map((item: any) => (
                <tr key={`day-${item.day}-${item.plan_name}`}>
                  <td><strong>{item.day}</strong></td>
                  <td>{item.plan_name}</td>
                  <td>{item.orders}</td>
                  <td>{formatMoney(Number(item.revenue || 0))}</td>
                </tr>
              )) : <tr><td colSpan={4} className="empty-state">Chưa có dữ liệu top gói theo ngày.</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="table-wrap summary-wrap">
          <table>
            <thead><tr><th>Thứ</th><th>Gói top</th><th>Đơn</th><th>Doanh thu</th></tr></thead>
            <tbody>
              {topByWeekday.length ? topByWeekday.map((item: any) => (
                <tr key={`weekday-${item.weekday}-${item.plan_name}`}>
                  <td><strong>{item.weekday}</strong></td>
                  <td>{item.plan_name}</td>
                  <td>{item.orders}</td>
                  <td>{formatMoney(Number(item.revenue || 0))}</td>
                </tr>
              )) : <tr><td colSpan={4} className="empty-state">Chưa có dữ liệu top gói theo thứ.</td></tr>}
            </tbody>
          </table>
        </div>
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 1.08s both" }}>
        <div className="table-wrap summary-wrap">
          <table>
            <thead><tr><th>Giờ</th><th>Gói top</th><th>Đơn</th><th>Doanh thu</th></tr></thead>
            <tbody>
              {topByHour.length ? topByHour.map((item: any) => (
                <tr key={`hour-${item.hour}-${item.plan_name}`}>
                  <td><strong>{item.hour}</strong></td>
                  <td>{item.plan_name}</td>
                  <td>{item.orders}</td>
                  <td>{formatMoney(Number(item.revenue || 0))}</td>
                </tr>
              )) : <tr><td colSpan={4} className="empty-state">Chưa có dữ liệu top gói theo giờ.</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="table-wrap summary-wrap">
          <table>
            <thead><tr><th>Gói</th><th>New buyer</th><th>Returning</th><th>Revenue mix</th></tr></thead>
            <tbody>
              {buyerTypePlanRows.length ? buyerTypePlanRows.slice(0, 8).map((item: any) => (
                <tr key={item.plan_name}>
                  <td><strong>{item.plan_name}</strong></td>
                  <td>{item.first_buyers}</td>
                  <td>{item.returning_buyers}</td>
                  <td>{formatMoney(Number(item.first_buyers_revenue || 0))} / {formatMoney(Number(item.returning_buyers_revenue || 0))}</td>
                </tr>
              )) : <tr><td colSpan={4} className="empty-state">Chưa có dữ liệu buyer split.</td></tr>}
            </tbody>
          </table>
        </div>
      </Box>

      <Box sx={{ animation: "fadeUp 0.5s ease-out 1.05s both" }}>
        <TrendTable title="Theo dõi tăng trưởng theo tháng" subtitle="Biểu đồ phát triển doanh thu trong năm hiện tại." rows={trendRows(yearGroups, yearPeak)} />
      </Box>
    </Stack>
  );
}

export function OrdersSection(props: any) {
  const { filteredOrders, filteredOrdersBase, exportOrdersCsv, query, setQuery, orderTab, setOrderTab, orderPeriod, setOrderPeriod, pagedOrders, changeOrderStatus, removeOrder, openOrderEditor, saving, orderPage, totalOrderPages, setOrderPage, isWithinPeriod } = props;
  const paidCount = filteredOrdersBase.filter((item: any) => item.status === "PAID").length;
  const remainingCount = filteredOrdersBase.length - paidCount;
  const todayCount = filteredOrdersBase.filter((item: any) => isWithinPeriod(item.created_at, "today")).length;
  const monthCount = filteredOrdersBase.filter((item: any) => isWithinPeriod(item.created_at, "month")).length;
  const periodOptions: Array<{ value: "today" | "7d" | "month" | "year" | "all"; label: string }> = [
    { value: "all", label: "Tất cả" },
    { value: "today", label: "Hôm nay" },
    { value: "7d", label: "7 ngày" },
    { value: "month", label: "Tháng này" },
    { value: "year", label: "Năm nay" },
  ];
  return (
    <Stack spacing={2}>
      <AppSection
        title="Đơn hàng"
        subtitle="Quản lý danh sách đơn tổng. Ưu tiên xem theo PAID và phần trạng thái còn lại để bớt dày."
        action={
          <AppToolbar>
            <Button variant="contained" size="small" onClick={props.openManualOrder}><Plus size={16} /> Mở form tạo đơn</Button>
            <Button variant="outlined" size="small" onClick={props.openOrderSettings}><Settings size={16} /> Cài đặt</Button>
            <Button variant="outlined" size="small" onClick={exportOrdersCsv} disabled={!filteredOrders.length}><Download size={16} /> CSV</Button>
          </AppToolbar>
        }
        accent="blue"
      >
        <Box sx={{ display: "grid", gap: 1.25, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" }, mb: 2 }}>
          <Metric label="Đơn hôm nay" value={String(todayCount)} accent="blue" icon={<CalendarClock size={16} />} />
          <Metric label="Đơn tháng này" value={String(monthCount)} accent="cyan" icon={<TrendingUp size={16} />} />
          <Metric label="Đã thanh toán" value={String(paidCount)} accent="emerald" icon={<CreditCard size={16} />} />
          <Metric label="Trạng thái còn lại" value={String(remainingCount)} accent="amber" icon={<BadgeDollarSign size={16} />} />
        </Box>

        {/* Unified Control Bar */}
        <Box sx={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 2, p: 1.5, mb: 1, bgcolor: "rgba(241, 245, 249, 0.4)", borderRadius: "12px", border: "1px solid", borderColor: "divider" }}>
          <TextField 
            value={query} 
            onChange={(event) => setQuery(event.target.value)} 
            placeholder="Tìm mã đơn, tên khách, Telegram ID, tên gói, coupon..." 
            size="small" 
            sx={{ flexGrow: 1, minWidth: { xs: "100%", md: "320px" }, bgcolor: "#fff", borderRadius: 1, "& .MuiOutlinedInput-root": { borderRadius: "8px" } }} 
          />
          
          <Box sx={{ display: "flex", p: 0.5, bgcolor: "rgba(15, 23, 42, 0.04)", borderRadius: "8px", border: "1px solid rgba(15, 23, 42, 0.05)", overflowX: "auto" }}>
            {periodOptions.map((item) => (
              <Box
                key={item.value}
                onClick={() => setOrderPeriod(item.value)}
                sx={{
                  px: 2,
                  py: 0.75,
                  fontSize: 13,
                  fontWeight: 700,
                  cursor: "pointer",
                  borderRadius: "6px",
                  color: orderPeriod === item.value ? "primary.main" : "text.secondary",
                  bgcolor: orderPeriod === item.value ? "#ffffff" : "transparent",
                  boxShadow: orderPeriod === item.value ? "0 1px 3px rgba(15,23,42,0.1)" : "none",
                  transition: "all 200ms ease",
                  whiteSpace: "nowrap"
                }}
              >
                {item.label}
              </Box>
            ))}
          </Box>
        </Box>

        <Tabs
          value={orderTab}
          onChange={(_, value) => setOrderTab(value as "paid" | "other")}
          sx={{ px: 0.5, mb: 1, minHeight: 42, "& .MuiTab-root": { minHeight: 42, fontWeight: 800, textTransform: "none" } }}
        >
          <Tab value="paid" label={<Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}><span>Đã thanh toán</span><Chip size="small" label={String(paidCount)} sx={{ height: 22 }} /></Box>} />
          <Tab value="other" label={<Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}><span>Trạng thái còn lại</span><Chip size="small" label={String(remainingCount)} sx={{ height: 22 }} /></Box>} />
        </Tabs>

        <OrdersTable orders={pagedOrders} onStatusChange={changeOrderStatus} onDeleteOrder={removeOrder} onEditOrder={openOrderEditor} saving={saving} />
        <Pagination page={orderPage} totalPages={totalOrderPages} totalItems={filteredOrders.length} onPage={setOrderPage} />
      </AppSection>
    </Stack>
  );
}
