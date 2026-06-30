"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, Chip, MenuItem, Stack, Tab, Tabs, TextField, Typography } from "@mui/material";
import { Download, Plus, Users, BadgeDollarSign, CalendarClock, ShieldCheck, TrendingUp, CreditCard, Coins, Megaphone } from "lucide-react";
import { AppSection, AppToolbar, BreakdownChart, DonutChart, Pagination, OrdersTable, TrendTable } from "./dashboard-components";
import { Metric } from "./metric-card";

export function AnalyticsSection(props: any) {
  const { orders, yearStats, monthStats, paidRevenueByCurrency, paidRevenueByProvider, formatRevenueCurrency, providerRevenueFormat, isWithinPeriod } = props;
  const monthGroups = props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")), "day");
  const yearGroups = props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "year")), "month");
  const monthPeak = Math.max(1, ...monthGroups.map((item: any) => item.stats.revenue));
  const yearPeak = Math.max(1, ...yearGroups.map((item: any) => item.stats.revenue));
  const monthRevenue = monthGroups.map((item: any) => ({ label: item.label, value: Number(item.stats.revenue || 0) }));
  const paymentStatusBreakdown = [
    { label: "PAID", value: monthStats.paid },
    { label: "PENDING", value: monthStats.pending },
    { label: "CANCELLED", value: monthStats.cancelled },
    { label: "EXPIRED", value: monthStats.expired },
  ];
  const currencyBreakdown = [
    { label: "VND", value: (paidRevenueByCurrency.VND || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0) },
    { label: "USD", value: (paidRevenueByCurrency.USD || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0) },
    { label: "CRYPTO", value: (paidRevenueByCurrency.CRYPTO || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0) },
  ].filter((item) => item.value > 0);
  const providerBreakdown = [
    { label: "PayOS", value: paidRevenueByProvider.PAYOS || 0 },
    { label: "PayPal", value: paidRevenueByProvider.PAYPAL || 0 },
    { label: "NOWPayments", value: paidRevenueByProvider.NOWPAYMENTS || 0 },
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
  return (
    <Stack spacing={2}>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
        <Metric label="Hôm nay" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "today")))} accent="blue" icon={<TrendingUp size={16} />} />
        <Metric label="Tháng này" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")))} accent="cyan" icon={<CalendarClock size={16} />} />
        <Metric label="Năm nay" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "year")))} accent="emerald" icon={<ShieldCheck size={16} />} />
        <Metric label="Khách đã trả tiền" value={String(yearStats.customers)} accent="indigo" icon={<Users size={16} />} />
      </Box>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
        <Metric label="PAID" value={String(monthStats.paid)} accent="emerald" icon={<CreditCard size={16} />} />
        <Metric label="PENDING" value={String(monthStats.pending)} accent="amber" icon={<BadgeDollarSign size={16} />} />
        <Metric label="CANCELLED" value={String(monthStats.cancelled)} accent="rose" icon={<ShieldCheck size={16} />} />
        <Metric label="EXPIRED" value={String(monthStats.expired)} accent="blue" icon={<CalendarClock size={16} />} />
      </Box>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
        <Metric label="VNĐ tháng" value={formatRevenueCurrency("VND", (paidRevenueByCurrency.VND || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0))} tone="vnd" accent="blue" icon={<TrendingUp size={16} />} />
        <Metric label="USD tháng" value={formatRevenueCurrency("USD", (paidRevenueByCurrency.USD || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0))} tone="usd" accent="cyan" icon={<CreditCard size={16} />} />
        <Metric label="Crypto tháng" value={formatRevenueCurrency("CRYPTO", (paidRevenueByCurrency.CRYPTO || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0))} tone="crypto" accent="emerald" icon={<Coins size={16} />} />
        <Metric label="PayPal" value={providerRevenueFormat("PAYPAL", paidRevenueByProvider.PAYPAL || 0)} tone="paypal" accent="indigo" icon={<BadgeDollarSign size={16} />} />
      </Box>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
        <Metric label="Đơn PAID tháng" value={String(monthStats.paid)} accent="blue" icon={<CreditCard size={16} />} />
        <Metric label="Đơn chờ tháng" value={String(monthStats.pending)} accent="amber" icon={<BadgeDollarSign size={16} />} />
        <Metric label="AOV tháng" value={props.ordersAverageMoney(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")))} accent="cyan" icon={<TrendingUp size={16} />} />
        <Metric label="Coupon giảm tháng" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")), "coupon_discount_amount")} accent="rose" icon={<Megaphone size={16} />} />
      </Box>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
        <BreakdownChart title="Doanh thu theo ngày" subtitle="Xem mốc ngày nào đang tăng giảm để bám đà bán." accent="blue" items={monthRevenue.slice().reverse()} />
        <Box>
          <DonutChart title="Cơ cấu trạng thái tháng" subtitle="Tỉ trọng đơn để đọc nhanh trạng thái vận hành." accent="emerald" segments={paymentStatusBreakdown} centerLabel={`${monthStats.conversion}%`} />
        </Box>
      </Box>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
        <BreakdownChart title="Doanh thu theo currency" subtitle="Biết ngay dòng tiền chính tháng này nằm ở đâu." accent="cyan" items={currencyBreakdown.length ? currencyBreakdown : [{ label: "Không có", value: 0 }]} />
        <Box>
          <BreakdownChart title="Doanh thu theo phương thức" subtitle="PayOS, PayPal, NOWPayments và USDT TRC20." accent="violet" items={providerBreakdown.length ? providerBreakdown : [{ label: "Không có", value: 0 }]} />
        </Box>
      </Box>
      <TrendTable title="Theo dõi tăng trưởng theo ngày" subtitle="Doanh thu, số đơn, khách trả tiền và tỉ lệ thanh toán trong tháng." rows={trendRows(monthGroups, monthPeak)} />
      <TrendTable title="Theo dõi tăng trưởng theo tháng" subtitle="Biểu đồ phát triển doanh thu trong năm hiện tại." rows={trendRows(yearGroups, yearPeak)} />
    </Stack>
  );
}

export function OrdersSection(props: any) {
  const { filteredOrders, filteredOrdersBase, exportOrdersCsv, query, setQuery, orderTab, setOrderTab, orderPeriod, setOrderPeriod, pagedOrders, changeOrderStatus, removeOrder, saving, orderPage, totalOrderPages, setOrderPage, isWithinPeriod } = props;
  const paidCount = filteredOrdersBase.filter((item: any) => item.status === "PAID").length;
  const remainingCount = filteredOrdersBase.length - paidCount;
  const todayCount = filteredOrdersBase.filter((item: any) => isWithinPeriod(item.created_at, "today")).length;
  const monthCount = filteredOrdersBase.filter((item: any) => isWithinPeriod(item.created_at, "month")).length;
  return (
    <Stack spacing={2}>
      <AppSection title="Thêm đơn thủ công" subtitle="Dùng khi cần cấp quyền ngoài cổng thanh toán. Mở popup để nhập thông tin, tạo order PAID và gen link." action={<AppToolbar><Button variant="outlined" size="small" onClick={props.openOrderSettings}>Cài đặt</Button><Button variant="contained" size="small" onClick={props.openManualOrder}><Plus size={16} /> Mở form tạo đơn</Button></AppToolbar>} compact accent="amber">
        <Typography variant="body2" color="text.secondary">Form tạo đơn thủ công được đưa vào popup để tab Đơn hàng chỉ tập trung vào danh sách và bộ lọc.</Typography>
      </AppSection>
      <AppSection
        title="Đơn hàng"
        subtitle="Quản lý danh sách đơn tổng. Ưu tiên xem theo PAID và phần trạng thái còn lại để bớt dày."
        action={<AppToolbar><Button variant="outlined" size="small" onClick={exportOrdersCsv} disabled={!filteredOrders.length}><Download size={16} /> CSV</Button></AppToolbar>}
        accent="blue"
      >
        <Box sx={{ display: "grid", gap: 1.25, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" }, mb: 1.5 }}>
          <Metric label="Đơn hôm nay" value={String(todayCount)} accent="blue" icon={<CalendarClock size={16} />} />
          <Metric label="Đơn tháng này" value={String(monthCount)} accent="cyan" icon={<TrendingUp size={16} />} />
          <Metric label="Đã thanh toán" value={String(paidCount)} accent="emerald" icon={<CreditCard size={16} />} />
          <Metric label="Trạng thái còn lại" value={String(remainingCount)} accent="amber" icon={<BadgeDollarSign size={16} />} />
        </Box>
        <Tabs
          value={orderTab}
          onChange={(_, value) => setOrderTab(value as "paid" | "other")}
          sx={{ px: 0.5, minHeight: 42, "& .MuiTab-root": { minHeight: 42, fontWeight: 800, textTransform: "none" } }}
        >
          <Tab value="paid" label={<Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}><span>Đã thanh toán</span><Chip size="small" label={String(paidCount)} sx={{ height: 22 }} /></Box>} />
          <Tab value="other" label={<Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}><span>Trạng thái còn lại</span><Chip size="small" label={String(remainingCount)} sx={{ height: 22 }} /></Box>} />
        </Tabs>
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.25} sx={{ py: 1.5 }}>
          <TextField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm mã đơn, tên khách, Telegram ID, tên gói, coupon..." size="small" fullWidth />
          <TextField select value={orderPeriod} onChange={(event) => setOrderPeriod(event.target.value)} size="small" fullWidth>
            <MenuItem value="today">Hôm nay</MenuItem><MenuItem value="7d">7 ngày gần đây</MenuItem><MenuItem value="month">Tháng này</MenuItem><MenuItem value="year">Năm nay</MenuItem><MenuItem value="all">Tất cả</MenuItem>
          </TextField>
        </Stack>
        <OrdersTable orders={pagedOrders} onStatusChange={changeOrderStatus} onDeleteOrder={removeOrder} saving={saving} />
        <Pagination page={orderPage} totalPages={totalOrderPages} totalItems={filteredOrders.length} onPage={setOrderPage} />
      </AppSection>
    </Stack>
  );
}
