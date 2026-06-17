"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Button, Stack } from "@mui/material";
import { Download, Plus } from "lucide-react";
import { Metric, PanelHead, Pagination, OrdersTable } from "./dashboard-components";

export function AnalyticsSection(props: any) {
  const { orders, yearStats, monthStats, paidRevenueByCurrency, paidRevenueByProvider, formatRevenueCurrency, providerRevenueFormat, isWithinPeriod, SummaryTable } = props;
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
      <section className="panel">
        <PanelHead title="Theo dõi tăng trưởng" subtitle="Doanh thu, tỉ lệ thanh toán, khách trả tiền và giảm giá coupon theo từng ngày trong tháng." />
        <SummaryTable groups={props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "month")), "day")} />
      </section>
      <section className="panel">
        <PanelHead title="Tổng hợp theo tháng" subtitle="Dữ liệu năm hiện tại, không xoá đơn cũ." />
        <SummaryTable groups={props.groupOrders(orders.filter((item: any) => isWithinPeriod(item.created_at, "year")), "month")} />
      </section>
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
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm mã đơn, tên khách, Telegram ID, tên gói, coupon..." />
          <select value={orderStatus} onChange={(event) => setOrderStatus(event.target.value)}>
            <option value="ALL">Tất cả trạng thái</option><option value="PENDING">Đang chờ</option><option value="PAID">Đã thanh toán</option><option value="CANCELLED">Đã hủy</option><option value="EXPIRED">Hết hạn</option>
          </select>
          <select value={orderPeriod} onChange={(event) => setOrderPeriod(event.target.value)}>
            <option value="today">Hôm nay</option><option value="7d">7 ngày gần đây</option><option value="month">Tháng này</option><option value="year">Năm nay</option><option value="all">Tất cả</option>
          </select>
          <select value={orderGroupMode} onChange={(event) => setOrderGroupMode(event.target.value)}>
            <option value="day">Nhóm theo ngày</option><option value="month">Nhóm theo tháng</option><option value="none">Không nhóm</option>
          </select>
        </div>
        {orderGroupMode !== "none" ? <SummaryTable groups={groupedFilteredOrders} /> : null}
        <OrdersTable orders={pagedOrders} onStatusChange={changeOrderStatus} onDeleteOrder={removeOrder} saving={saving} />
        <Pagination page={orderPage} totalPages={totalOrderPages} totalItems={filteredOrders.length} onPage={setOrderPage} />
      </section>
    </Stack>
  );
}
