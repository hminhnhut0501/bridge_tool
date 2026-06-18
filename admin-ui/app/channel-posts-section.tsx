"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { Box, Button, Stack } from "@mui/material";
import { Plus, Send, Trash2 } from "lucide-react";
import { AppSection, AppToolbar, Metric, Pagination, SimpleTable, statusButtonSx } from "./dashboard-components";
import { dateText } from "./dashboard-helpers";

export function ChannelPostsSection(props: any) {
  const { channelPosts, channelPostCounts, channelPostTab, setChannelPostTab, openNewChannelPostModal, pagedChannelPosts, channelPostPage, totalChannelPostPages, visibleChannelPosts, setChannelPostPage, editChannelPost, runChannelPostAction, channelPostStatusClass, channelPostStatusLabel } = props;
  return (
    <Stack spacing={2}>
      <Box sx={{ display: "grid", gap: 1.75, gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
        <Metric label="Tổng bài" value={String(channelPosts.length)} accent="cyan" />
        <Metric label="Chờ gửi" value={String(channelPostCounts.queue + channelPostCounts.scheduled)} accent="violet" />
        <Metric label="Đã đăng" value={String(channelPostCounts.sent)} accent="amber" />
        <Metric label="Có lỗi" value={String(channelPostCounts.failed)} accent="blue" />
      </Box>
      <AppSection title="Đăng channel" subtitle="Soạn bài, gắn nút inline, hẹn giờ đăng hoặc hẹn giờ xóa bài khỏi Telegram. Bot phải là admin của channel/group nhận bài." action={<AppToolbar><Button variant="contained" size="small" onClick={openNewChannelPostModal} startIcon={<Plus size={16} />}>Soạn bài mới</Button></AppToolbar>} accent="cyan">
        <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "repeat(auto-fit, minmax(112px, 1fr))", p: 2 }}>
          {["draft", "queue", "scheduled", "sent", "failed", "deleted"].map((tab) => <Button key={tab} variant={channelPostTab === tab ? "contained" : "outlined"} sx={channelPostTab === tab ? statusButtonSx("success") : statusButtonSx("muted")} onClick={() => setChannelPostTab(tab)}>{tab}</Button>)}
        </Box>
        <SimpleTable
          headers={["Bài đăng", "Channel/Group", "Trạng thái", "Lịch", "Telegram", "Lỗi"]}
          rows={pagedChannelPosts.map((item: any) => [
            <Button
              key={`cp-title-${item.id}`}
              variant="text"
              onClick={() => editChannelPost(item)}
              sx={{ alignItems: "flex-start", justifyContent: "flex-start", textAlign: "left", px: 0, py: 0.5, minWidth: 0, textTransform: "none" }}
            >
              <Box component="span" sx={{ display: "grid", gap: 0.25 }}>
                <strong>{item.title || `Bài #${item.id}`}</strong>
                <span className="muted">{String(item.content || "").slice(0, 90)}</span>
              </Box>
            </Button>,
            item.target_chat_id,
            <span key={`cp-status-${item.id}`} className={channelPostStatusClass(item.status)}>{channelPostStatusLabel(item.status)}</span>,
            <><strong>Đăng: {dateText(item.scheduled_at || item.sent_at)}</strong><div className="muted">Xóa: {dateText(item.delete_at || item.deleted_at)}</div></>,
            <><strong>{item.sent_message_id ? `Message ${item.sent_message_id}` : "-"}</strong><div className="muted">Thử {item.attempt_count || 0}</div></>,
            item.error || "-",
          ])}
          onRow={(idx: number) => editChannelPost(pagedChannelPosts[idx])}
          actions={(idx: number) => {
            const item = pagedChannelPosts[idx];
            const status = String(item.status || "").toLowerCase();
            return (
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1 }}>
                {["draft", "failed", "delete_failed"].includes(status) ? <Button variant="outlined" size="small" onClick={(event) => { event.stopPropagation(); runChannelPostAction(item, "send_now"); }} startIcon={<Send size={15} />}>Gửi</Button> : null}
                {["sent", "delete_scheduled"].includes(status) ? <Button variant="outlined" size="small" sx={statusButtonSx("error")} onClick={(event) => { event.stopPropagation(); runChannelPostAction(item, "delete_now"); }} startIcon={<Trash2 size={15} />}>Xóa</Button> : null}
              </Box>
            );
          }}
        />
        <Pagination page={channelPostPage} totalPages={totalChannelPostPages} totalItems={visibleChannelPosts.length} onPage={setChannelPostPage} label="bài đăng" />
      </AppSection>
    </Stack>
  );
}
