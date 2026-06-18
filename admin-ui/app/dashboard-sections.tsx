"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Button, MenuItem, Stack, TextField } from "@mui/material";
import { Download, Plus } from "lucide-react";
import { Metric, PanelHead, Pagination, OrdersTable, TrendTable } from "./dashboard-components";

export function AnalyticsSection(props: any) {
  const { orders, yearStats, monthStats, paidRevenueByCurrency, paidRevenueByProvider, formatRevenueCurrency, providerRevenueFormat, isWithinPeriod } = props;
  const monthGroups = props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")), "day");
  const yearGroups = props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "year")), "month");
  const monthPeak = Math.max(1, ...monthGroups.map((item: any) => item.stats.revenue));
  const yearPeak = Math.max(1, ...yearGroups.map((item: any) => item.stats.revenue));
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
      <div className="grid">
        <Metric label="Hôm nay" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "today")))} />
        <Metric label="Tháng này" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")))} />
        <Metric label="Năm nay" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "year")))} />
        <Metric label="Khách đã trả tiền" value={String(yearStats.customers)} />
      </div>
      <div className="grid metrics-band">
        <Metric label="VNĐ tháng" value={formatRevenueCurrency("VND", (paidRevenueByCurrency.VND || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0))} tone="vnd" />
        <Metric label="USD tháng" value={formatRevenueCurrency("USD", (paidRevenueByCurrency.USD || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0))} tone="usd" />
        <Metric label="Crypto tháng" value={formatRevenueCurrency("CRYPTO", (paidRevenueByCurrency.CRYPTO || []).filter((item: any) => isWithinPeriod(item.created_at, "month")).reduce((sum: number, item: any) => sum + Number(item.amount || 0), 0))} tone="crypto" />
        <Metric label="PayPal" value={providerRevenueFormat("PAYPAL", paidRevenueByProvider.PAYPAL || 0)} tone="paypal" />
        <Metric label="NOWPayments / USDT" value={providerRevenueFormat("NOWPAYMENTS", (paidRevenueByProvider.NOWPAYMENTS || 0) + (paidRevenueByProvider.TRON_USDT || 0))} tone="crypto" />
      </div>
      <div className="grid">
        <Metric label="Đơn PAID tháng" value={String(monthStats.paid)} />
        <Metric label="Đơn chờ tháng" value={String(monthStats.pending)} />
        <Metric label="AOV tháng" value={props.ordersAverageMoney(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")))} />
        <Metric label="Coupon giảm tháng" value={props.ordersMoney(orders.filter((item: any) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")), "coupon_discount_amount")} />
      </div>
      <TrendTable title="Theo dõi tăng trưởng theo ngày" subtitle="Doanh thu, số đơn, khách trả tiền và tỉ lệ thanh toán trong tháng." rows={trendRows(monthGroups, monthPeak)} />
      <TrendTable title="Theo dõi tăng trưởng theo tháng" subtitle="Biểu đồ phát triển doanh thu trong năm hiện tại." rows={trendRows(yearGroups, yearPeak)} />
    </Stack>
  );
}

export function OrdersSection(props: any) {
  const { filteredOrders, filteredOrderStats, exportOrdersCsv, query, setQuery, orderStatus, setOrderStatus, orderPeriod, setOrderPeriod, orderGroupMode, setOrderGroupMode, groupedFilteredOrders, pagedOrders, changeOrderStatus, removeOrder, saving, orderPage, totalOrderPages, setOrderPage, SummaryTable } = props;
  return (
    <Stack spacing={2}>
      <div className="grid">
        <Metric label="Doanh thu bộ lọc" value={props.ordersMoney(filteredOrders.filter((item: any) => item.status === "PAID"))} />
        <Metric label="Đơn PAID" value={String(filteredOrderStats.paid)} />
        <Metric label="Đang chờ" value={String(filteredOrderStats.pending)} />
        <Metric label="Tỉ lệ thanh toán" value={`${filteredOrderStats.conversion}%`} />
      </div>
      <section className="panel">
        <PanelHead title="Thêm đơn thủ công" subtitle="Dùng khi cần cấp quyền ngoài cổng thanh toán. Mở popup để nhập thông tin, tạo order PAID và gen link." action={<div className="panel-actions"><Button variant="outlined" size="small" onClick={props.openOrderSettings}>Cài đặt</Button><Button variant="contained" size="small" onClick={props.openManualOrder}><Plus size={16} /> Mở form tạo đơn</Button></div>} />
        <div className="hint compact">Form tạo đơn thủ công được đưa vào popup để tab Đơn hàng chỉ tập trung vào danh sách và bộ lọc.</div>
      </section>
      <section className="panel">
        <PanelHead title="Đơn hàng" subtitle="Đơn được giữ lại lâu dài. Dùng bộ lọc, nhóm và phân trang để xem nhẹ hơn." action={<Button variant="outlined" size="small" onClick={exportOrdersCsv} disabled={!filteredOrders.length}><Download size={16} /> CSV</Button>} />
        <div className="toolbar orders-toolbar">
          <TextField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm mã đơn, tên khách, Telegram ID, tên gói, coupon..." size="small" fullWidth />
          <TextField select value={orderStatus} onChange={(event) => setOrderStatus(event.target.value)} size="small" fullWidth>
            <MenuItem value="ALL">Tất cả trạng thái</MenuItem><MenuItem value="PENDING">Đang chờ</MenuItem><MenuItem value="PAID">Đã thanh toán</MenuItem><MenuItem value="CANCELLED">Đã hủy</MenuItem><MenuItem value="EXPIRED">Hết hạn</MenuItem>
          </TextField>
          <TextField select value={orderPeriod} onChange={(event) => setOrderPeriod(event.target.value)} size="small" fullWidth>
            <MenuItem value="today">Hôm nay</MenuItem><MenuItem value="7d">7 ngày gần đây</MenuItem><MenuItem value="month">Tháng này</MenuItem><MenuItem value="year">Năm nay</MenuItem><MenuItem value="all">Tất cả</MenuItem>
          </TextField>
          <TextField select value={orderGroupMode} onChange={(event) => setOrderGroupMode(event.target.value)} size="small" fullWidth>
            <MenuItem value="day">Nhóm theo ngày</MenuItem><MenuItem value="month">Nhóm theo tháng</MenuItem><MenuItem value="none">Không nhóm</MenuItem>
          </TextField>
        </div>
        {orderGroupMode !== "none" ? <SummaryTable groups={groupedFilteredOrders} /> : null}
        <OrdersTable orders={pagedOrders} onStatusChange={changeOrderStatus} onDeleteOrder={removeOrder} saving={saving} />
        <Pagination page={orderPage} totalPages={totalOrderPages} totalItems={filteredOrders.length} onPage={setOrderPage} />
      </section>
    </Stack>
  );
}
