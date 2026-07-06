"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, Chip, Stack, Tab, Tabs, TextField, Typography } from "@mui/material";
import { Download, Plus, Users, BadgeDollarSign, CalendarClock, ShieldCheck, TrendingUp, CreditCard, Settings } from "lucide-react";
import { AppSection, AppToolbar, RevenueBarChart, BreakdownChart, DonutChart, Pagination, OrdersTable, TrendTable } from "./dashboard-components";
import { Metric } from "./metric-card";
import { orderAmountValue } from "./dashboard-helpers";

export function AnalyticsSection(props: any) {
  const { orders, monthStats, paidRevenueByCurrency, paidRevenueByProvider, isWithinPeriod } = props;
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

  return (
    <Stack spacing={2.5}>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
        {[
          <Metric key="rev" label="Doanh thu tháng này" value={props.ordersMoney(monthOrdersPaid)} accent="blue" icon={<TrendingUp size={16} />} />,
          <Metric key="cust" label="Khách mua tháng này" value={String(monthCustomers)} accent="cyan" icon={<Users size={16} />} />,
          <Metric key="aov" label="AOV tháng này" value={props.ordersAverageMoney(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")))} accent="emerald" icon={<CreditCard size={16} />} />,
          <Metric key="conv" label="Tỉ lệ thanh toán" value={`${monthStats.conversion}%`} accent="indigo" icon={<ShieldCheck size={16} />} note={`Đã trả: ${monthStats.paid} / Tổng: ${monthStats.paid + monthStats.pending + monthStats.cancelled + monthStats.expired} đơn`} />,
        ].map((card, i) => (
          <Box key={i} sx={{ height: "100%", animation: `fadeUp 0.5s ease-out ${i * 0.1}s both` }}>{card}</Box>
        ))}
      </Box>

      <Box sx={{ width: "100%", animation: "fadeUp 0.6s ease-out 0.4s both" }}>
        <RevenueBarChart title="Doanh thu theo ngày" subtitle="Biểu đồ trực quan hóa xu hướng dòng tiền tăng trưởng hàng ngày." accent="blue" items={monthChartData.slice().reverse()} />
      </Box>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, animation: "fadeUp 0.5s ease-out 0.6s both" }}>
        <DonutChart title="Cơ cấu trạng thái tháng" subtitle="Tỉ trọng đơn để đọc nhanh trạng thái." accent="emerald" segments={paymentStatusBreakdown} centerLabel={`${monthStats.conversion}%`} />
        <BreakdownChart title="Doanh thu theo phương thức" subtitle="PayOS, PayPal và USDT." accent="violet" items={providerBreakdown.length ? providerBreakdown : [{ label: "Không có", value: 0 }]} />
        <BreakdownChart title="Doanh thu theo currency" subtitle="Biết ngay dòng tiền chính nằm ở đâu." accent="cyan" items={currencyBreakdown.length ? currencyBreakdown : [{ label: "Không có", value: 0 }]} />
      </Box>

      <Box sx={{ animation: "fadeUp 0.5s ease-out 0.8s both" }}>
        <TrendTable title="Theo dõi tăng trưởng theo ngày" subtitle="Doanh thu, số đơn, khách trả tiền và tỉ lệ thanh toán trong tháng." rows={trendRows(monthGroups, monthPeak)} />
      </Box>
      <Box sx={{ animation: "fadeUp 0.5s ease-out 0.9s both" }}>
        <TrendTable title="Theo dõi tăng trưởng theo tháng" subtitle="Biểu đồ phát triển doanh thu trong năm hiện tại." rows={trendRows(yearGroups, yearPeak)} />
      </Box>
    </Stack>
  );
}

export function OrdersSection(props: any) {
  const { filteredOrders, filteredOrdersBase, exportOrdersCsv, query, setQuery, orderTab, setOrderTab, orderPeriod, setOrderPeriod, pagedOrders, changeOrderStatus, removeOrder, saving, orderPage, totalOrderPages, setOrderPage, isWithinPeriod } = props;
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

        <OrdersTable orders={pagedOrders} onStatusChange={changeOrderStatus} onDeleteOrder={removeOrder} saving={saving} />
        <Pagination page={orderPage} totalPages={totalOrderPages} totalItems={filteredOrders.length} onPage={setOrderPage} />
      </AppSection>
    </Stack>
  );
}
