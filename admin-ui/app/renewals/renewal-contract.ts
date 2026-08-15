export type RenewalTab = "expiring-soon" | "expired";

export type ReminderStatus = "NOT_SENT" | "SENT" | "FAILED";
export type MembershipStatus = "PRESENT" | "ABSENT" | "UNKNOWN";
export type KickStatus =
  | "NOT_DUE"
  | "PENDING"
  | "PROCESSING"
  | "DONE"
  | "RETAINED"
  | "ALREADY_ABSENT"
  | "RETRY"
  | "REVIEW";

export type RenewalRow = {
  customer: {
    name: string | null;
    telegramUserId: string;
  };
  entitlement: {
    orderId: string;
    planName: string;
    planFamily: string;
    groupCode: string;
    groupId: string | null;
    expiresAt: string | null;
    isLifetime: boolean;
  };
  reminder: {
    status: ReminderStatus;
    sentAt: string | null;
    attempts: number;
    lastError: string | null;
  };
  membership: MembershipStatus;
  kick: {
    status: KickStatus;
    attempts: number;
    lastError: string | null;
    updatedAt: string | null;
  };
};

export type RenewalSummary = {
  expiringSoon: number;
  expiring24h: number;
  reminderNotSent: number;
  reminded: number;
  expired: number;
  pendingKick: number;
  kicked: number;
  retained: number;
  alreadyAbsent: number;
  review: number;
  errors: number;
  generatedAt: string | null;
};

export type RenewalViewModel = {
  tab: RenewalTab;
  rows: RenewalRow[];
  summary: RenewalSummary;
  loading: boolean;
  error: string | null;
  source: "API" | "FIXTURE";
};

export const EMPTY_RENEWAL_SUMMARY: RenewalSummary = {
  expiringSoon: 0,
  expiring24h: 0,
  reminderNotSent: 0,
  reminded: 0,
  expired: 0,
  pendingKick: 0,
  kicked: 0,
  retained: 0,
  alreadyAbsent: 0,
  review: 0,
  errors: 0,
  generatedAt: null,
};

export const EMPTY_RENEWAL_VIEW: RenewalViewModel = {
  tab: "expiring-soon",
  rows: [],
  summary: EMPTY_RENEWAL_SUMMARY,
  loading: false,
  error: null,
  source: "API",
};

export const RENEWAL_STATUS_LABELS: Record<KickStatus, string> = {
  NOT_DUE: "Chưa đến hạn",
  PENDING: "Chờ xử lý",
  PROCESSING: "Đang xử lý",
  DONE: "Đã kick",
  RETAINED: "Đã gia hạn, không kick",
  ALREADY_ABSENT: "Đã rời group",
  RETRY: "Sẽ thử lại",
  REVIEW: "Cần kiểm tra",
};

export function reminderStatusLabel(status: ReminderStatus): string {
  return { NOT_SENT: "Chưa gửi", SENT: "Đã gửi", FAILED: "Gửi lỗi" }[status];
}

export function membershipStatusLabel(status: MembershipStatus): string {
  return { PRESENT: "Còn trong group", ABSENT: "Đã rời group", UNKNOWN: "Chưa xác định" }[status];
}

export function renewalFixture(tab: RenewalTab): RenewalViewModel {
  return {
    ...EMPTY_RENEWAL_VIEW,
    tab,
    source: "FIXTURE",
    error: "API renewal chưa trả contract mới; đang hiển thị trạng thái mẫu để tránh màn hình trắng.",
  };
}
