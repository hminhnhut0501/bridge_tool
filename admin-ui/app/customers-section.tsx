"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, Chip, MenuItem, Select, Stack, TextField, Typography } from "@mui/material";
import { Metric, Pagination, PanelHead, SimpleTable } from "./dashboard-components";
import { dateTextShort } from "./dashboard-helpers";

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
            <Box key={`customer-${customer.id}`} sx={{ display: "grid", gap: 0.25 }}>
              <Typography sx={{ fontWeight: 800, lineHeight: 1.2 }}>{customer.name}{customer.hasLifetimeSvip ? " 👑" : ""}</Typography>
              <Typography variant="body2" color="text.secondary">{customer.id}</Typography>
            </Box>,
            <Chip
              key={`status-${customer.id}`}
              size="small"
              label={customer.statusLabel}
              color={customer.statusColor}
              sx={{ fontWeight: 700, width: "fit-content" }}
            />,
            <Typography key={`paid-${customer.id}`} sx={{ fontWeight: 700 }}>{customer.paidOrders.length}</Typography>,
            <Box key={`plans-${customer.id}`} sx={{ display: "grid", gap: 0.25 }}>
              <Typography sx={{ fontWeight: 800, lineHeight: 1.2 }}>{customer.plans[0] || "-"}</Typography>
              <Typography variant="body2" color="text.secondary">{customer.groups.slice(0, 2).join(", ") || "Chưa rõ group"}</Typography>
            </Box>,
            <Typography key={`expire-${customer.id}`} sx={{ fontWeight: 600 }}>{dateTextShort(customer.latestExpire)}</Typography>,
            <Typography key={`money-${customer.id}`} sx={{ fontWeight: 700 }}>{ordersMoney(customer.paidOrders)}</Typography>,
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
