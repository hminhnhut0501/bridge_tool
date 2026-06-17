"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, MenuItem, Select, Stack, TextField } from "@mui/material";
import { Metric, Pagination, PanelHead, SimpleTable } from "./dashboard-components";

export function CustomersSection(props: any) {
  const {
    filteredCustomers,
    customerSummaries,
    ordersMoney,
    exportCustomersCsv,
    query,
    setQuery,
    customerStatus,
    setCustomerStatus,
    customerGroup,
    setCustomerGroup,
    customerGroupOptions,
    customerPlanKind,
    setCustomerPlanKind,
    pagedCustomers,
    setSelectedCustomerId,
    setCustomerOrderTab,
    setCustomerDetailTab,
    setCustomerTimelineSubTab,
    setCustomerModalOpen,
    customerPage,
    totalCustomerPages,
    setCustomerPage,
  } = props;

  return (
    <Stack spacing={2}>
      <Box sx={{ display: "grid", gap: 1.75, gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
        <Metric label="Khách trong bộ lọc" value={String(filteredCustomers.length)} />
        <Metric label="Đang còn hạn" value={String(customerSummaries.filter((item: any) => item.activeOrders.length).length)} />
        <Metric label="Có dùng coupon" value={String(customerSummaries.filter((item: any) => item.coupons.length).length)} />
        <Metric label="Doanh thu khách lọc" value={ordersMoney(filteredCustomers.flatMap((item: any) => item.paidOrders))} />
      </Box>
      <section className="panel">
        <PanelHead
          title="Khách hàng"
          subtitle="Danh sách ưu tiên khách mới nhất. Bấm Xem chi tiết để mở popup quản lý đơn, hạn dùng và trạng thái."
          action={<Box sx={{ display: "flex", gap: 1 }}><Button variant="outlined" size="small" onClick={exportCustomersCsv} disabled={!filteredCustomers.length}>CSV</Button></Box>}
        />
        <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: "minmax(0, 1fr) repeat(3, 180px)", p: 1.75 }}>
          <TextField size="small" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm tên khách, Telegram ID, gói, group, coupon..." />
          <Select size="small" value={customerStatus} onChange={(event) => setCustomerStatus(event.target.value)}>{["all","active","expiring","lifetime","expired","paid","coupon"].map((item) => <MenuItem key={item} value={item}>{item === "all" ? "Tất cả khách" : item}</MenuItem>)}</Select>
          <Select size="small" value={customerGroup} onChange={(event) => setCustomerGroup(event.target.value)}>{["ALL", ...customerGroupOptions].map((item: any) => <MenuItem key={item} value={item}>{item === "ALL" ? "Tất cả group" : item}</MenuItem>)}</Select>
          <Select size="small" value={customerPlanKind} onChange={(event) => setCustomerPlanKind(event.target.value)}>{["ALL", "1 ngày", "30 ngày", "Trọn đời", "Khác"].map((item) => <MenuItem key={item} value={item}>{item === "ALL" ? "Tất cả gói" : item}</MenuItem>)}</Select>
        </Box>
        <SimpleTable
          headers={["Khách", "Trạng thái", "PAID", "Gói / Group", "Hạn gần nhất", "Tổng tiền"]}
          rows={pagedCustomers.map((customer: any) => [
            <><strong>{customer.name}{customer.hasLifetimeSvip ? " 👑" : ""}</strong><div className="muted">{customer.id}</div></>,
            <span key="status" className={customer.activeOrders.length ? "status paid" : customer.expiringWithinWindow ? "status warning" : customer.hasLifetimeOrder ? "status badge-lifetime" : customer.paidOrders.length ? "status expired" : "status pending"}>{customer.activeOrders.length ? "Đang còn hạn" : customer.expiringWithinWindow ? "Sắp hết hạn" : customer.hasLifetimeOrder ? "Trọn đời" : customer.paidOrders.length ? "Hết hạn / chờ kick" : "Chưa PAID"}</span>,
            String(customer.paidOrders.length),
            <><strong>{customer.plans[0] || "-"}</strong><div className="muted">{customer.groups.slice(0, 2).join(", ") || "Chưa rõ group"}</div></>,
            customer.latestExpire,
            ordersMoney(customer.paidOrders),
          ])}
          actions={(idx: number) => (
            <Button variant="outlined" size="small" onClick={() => {
              const customer = pagedCustomers[idx];
              setSelectedCustomerId(customer.id);
              setCustomerOrderTab("all");
              setCustomerDetailTab("orders");
              setCustomerTimelineSubTab("all");
              setCustomerModalOpen(true);
            }}>Chi tiết</Button>
          )}
        />
        <Pagination page={customerPage} totalPages={totalCustomerPages} totalItems={filteredCustomers.length} onPage={setCustomerPage} label="khách" />
      </section>
    </Stack>
  );
}
