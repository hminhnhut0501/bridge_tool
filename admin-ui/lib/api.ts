export type Order = {
  order_id: string;
  telegram_user_id: string;
  full_name: string | null;
  plan_name: string;
  note?: string | null;
  amount: number;
  status: string;
  paid_at: string | null;
  expire_at: string | null;
  sale_id?: string | null;
  original_amount?: number | null;
  coupon_code?: string | null;
  coupon_discount_percent?: number | null;
  coupon_discount_amount?: number | null;
  payment_provider?: string | null;
  payment_provider_order_id?: string | null;
  payment_approval_url?: string | null;
  payment_currency?: string | null;
  plan_token?: string | null;
  plan_category?: string | null;
  source_type?: string | null;
  source_ref?: string | null;
  metadata?: Record<string, unknown> | null;
  last_reminder_date?: string | null;
  expired_notice_at?: string | null;
  created_at: string;
};

export type UserRow = {
  telegram_user_id: string;
  full_name: string | null;
  status: string;
  plan_name: string;
  expire_at: string | null;
  created_at: string;
};

export type ConfigRow = {
  key: string;
  value: string;
  updated_at: string;
};

export type MenuPage = {
  page_id: string;
  image_url: string | null;
  body: string;
  layout: string;
  updated_at: string;
};

export type SaleRule = {
  sale_id: string;
  price_key: string;
  discount_percent: number | null;
  sale_price: number | null;
  slot_limit: number | null;
  used_count: number;
  enabled: boolean;
  starts_at: string | null;
  ends_at: string | null;
};

export type Coupon = {
  code: string;
  plan_name: string | null;
  status: string;
  max_uses: number | null;
  used_count: number;
  expires_at: string | null;
  created_at?: string;
  updated_at?: string;
  redemption_count?: number;
  last_redeemed_at?: string | null;
  last_redeemed_by?: string | null;
  last_redeemed_order_id?: string | null;
  last_redeemed_full_name?: string | null;
  last_redeemed_username?: string | null;
  raw_data: Record<string, unknown>;
};

export type BlacklistEntry = {
  telegram_user_id: string;
  username: string | null;
  full_name: string | null;
  reason: string;
  source: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CustomerSearchResult = {
  id: string;
  name: string;
  orders: Order[];
  paidOrders: Order[];
  activeOrders: Order[];
  latestExpire: string;
  blacklistEntry: BlacklistEntry | null;
  isBlacklisted: boolean;
  hasPaidOrder: boolean;
  hasActiveOrder: boolean;
  activeOrderCount: number;
  paidOrderCount: number;
  latestExpireText: string;
  latestExpireOrder: Order | null;
  status: string;
  statusText: string;
};

export type SupportEvent = {
  id: string;
  event_type: string;
  telegram_user_id: string | null;
  username: string | null;
  full_name: string | null;
  chat_id: string | null;
  chat_title: string | null;
  order_id: string | null;
  plan_name: string | null;
  raw_data: Record<string, unknown>;
  created_at: string;
};

export type ActivityEvent = {
  id: string;
  event_name: string;
  telegram_user_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export type SupportGroupCheck = {
  enabled: boolean;
  group_id: string;
  group_name: string;
  get_chat: { ok: boolean; message: string };
  bot_member: { ok: boolean; message: string };
  invite_link: { ok: boolean; message: string };
};

export type WebhookInfo = {
  url: string;
  has_custom_certificate: boolean;
  pending_update_count: number;
  last_error_date?: number;
  last_error_message?: string;
  max_connections?: number;
  allowed_updates?: string[];
};

export type BotScheduleStatus = {
  source: "channel" | "fixed" | "maintenance" | "always";
  active: boolean;
  title: string;
  window: string;
  detail: string;
  timezone: string;
  linkedCount: number;
  maintenanceMode: boolean;
  maintenanceOverride: boolean;
  fixedScheduleEnabled: boolean;
  activeHours: string;
};

export type KickAuditRow = {
  audit_id: string;
  customer_name: string;
  telegram_user_id: string;
  order_id: string;
  plan_name: string;
  expire_at: string | null;
  group_id: string;
  group_name: string;
  status: string;
  status_label: string;
  needs_action: boolean;
  latest_kick_at: string | null;
  latest_error: string | null;
  live_checked: boolean;
  live_status: string;
  live_present: boolean | null;
  retained_reason?: string | null;
  retained_orders?: string[] | null;
};

export type VipGroupAuditRow = {
  audit_id: string;
  customer_name: string;
  telegram_user_id: string;
  order_id: string;
  plan_name: string;
  expire_at: string | null;
  group_id: string;
  group_name: string;
  status: string;
  status_label: string;
  needs_action: boolean;
  latest_kick_at: string | null;
  latest_error: string | null;
  live_checked: boolean;
  live_status: string;
  live_present: boolean | null;
  order_active_group_ids?: string[] | null;
  current_group_ids?: string[] | null;
};

export type KickAuditPayload = {
  telegram_user_id: string;
  order_id: string;
  group_id: string;
  plan_name?: string;
  customer_name?: string;
};

export type BroadcastCampaign = {
  id: string;
  title: string;
  message: string;
  parse_mode: string;
  target_segment: string;
  status: string;
  delay_seconds: number;
  batch_size: number;
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  skipped_count: number;
  started_at: string | null;
  finished_at: string | null;
  raw_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type BroadcastRecipient = {
  id: string;
  campaign_id: string;
  telegram_user_id: string;
  username: string | null;
  full_name: string | null;
  segment: string;
  status: string;
  attempt_count: number;
  last_attempt_at: string | null;
  sent_at: string | null;
  error: string | null;
  raw_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ChannelPost = {
  id: number;
  bot_key: string;
  target_chat_id: string;
  title: string | null;
  image_ref: string | null;
  content: string;
  buttons_text: string | null;
  parse_mode: string;
  disable_web_page_preview: boolean;
  status: string;
  sent_message_id: string | null;
  sent_at: string | null;
  scheduled_at: string | null;
  delete_at: string | null;
  deleted_at: string | null;
  error: string | null;
  error_code: string | null;
  enabled: boolean;
  repeat_daily?: boolean;
  notes: string | null;
  attempt_count: number;
  last_attempt_at: string | null;
  created_by: string | null;
  deleted_by: string | null;
  created_at: string;
  updated_at: string;
};

export type ChannelPostEvent = {
  id: number;
  bot_key: string;
  channel_post_id: number;
  event_type: string;
  message: string | null;
  details: Record<string, unknown>;
  created_at: string;
};

export type CampaignPreview = {
  total: number;
  counts: Record<string, number>;
  sample: BroadcastRecipient[];
};

export type ManualOrderPayload = {
  telegram_user_id: string;
  full_name?: string;
  plan_name: string;
  note?: string;
  amount?: string;
  duration_days?: string;
  expire_at?: string;
  coupon_code?: string;
  sale_id?: string;
  payment_currency?: string;
  payment_provider?: string;
};

export type ManualOrderResult = {
  order_id: string;
  telegram_user_id: string;
  full_name: string;
  plan_name: string;
  note?: string;
  amount: number;
  payment_currency?: string;
  payment_provider?: string;
  paid_at: string;
  expire_at: string;
  activation_code: string;
  activation_url: string;
  group_names: string;
  links_text: string;
  support_link: string | null;
  support_error: string;
  support_text: string;
  bot_link_title?: string;
  bot_link_subtitle?: string;
  bot_link_button_label?: string;
  bot_link_success_text?: string;
  bot_link_processing_text?: string;
  manual_order_text: string;
};

export type HiddenGroup = {
  id: string;
  name: string;
  description: string;
  chat_id: string;
  price_1m_vnd: number;
  price_life_vnd: number;
  price_1m_usd: number;
  price_life_usd: number;
  duration_1m_days: number;
  lifetime_days: number;
  image_url: string | null;
  requirement_type: string;
  requirement_value: string | null;
  sort_order: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};

export type HiddenCode = {
  code: string;
  name: string;
  description: string;
  scope_type: string;
  group_ids: string[];
  requirement_type: string | null;
  requirement_value: string | null;
  max_uses: number;
  used_count: number;
  valid_from: string | null;
  valid_until: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};

export type HiddenRedemption = {
  id?: string;
  code: string;
  telegram_user_id: string;
  full_name: string;
  username: string;
  revealed_group_ids: string[];
  created_at: string;
};

export type ActivationCode = {
  id: string;
  code: string;
  order_id: string;
  telegram_user_id: string;
  full_name: string | null;
  plan_name: string;
  expire_at: string | null;
  activation_status: string;
  activated_at: string | null;
  activated_by_user_id: string | null;
  used_at: string | null;
  used_by_user_id: string | null;
  activation_url: string | null;
  raw_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

const baseUrl = process.env.NEXT_PUBLIC_ADMIN_API_URL || "http://localhost:8000";

async function request<T>(path: string, secret: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Secret": secret,
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Request failed: ${res.status}`);
  }

  return res.json();
}

export async function getOrders(secret: string, limit = 5000) {
  return request<{ data: Order[] }>(`/admin-api/orders?limit=${limit}`, secret);
}

export async function getUsers(secret: string) {
  return request<{ data: UserRow[] }>("/admin-api/users", secret);
}

export async function searchCustomers(secret: string, query: string, limit = 20) {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return request<{ data: CustomerSearchResult[] }>(`/admin-api/customers/search?${params.toString()}`, secret);
}

export async function getConfig(secret: string) {
  return request<{ data: ConfigRow[] }>("/admin-api/config", secret);
}

export async function updateConfig(secret: string, key: string, value: string) {
  return request<{ data: ConfigRow[] }>(`/admin-api/config/${encodeURIComponent(key)}`, secret, {
    method: "PATCH",
    body: JSON.stringify({ value }),
  });
}

export async function updateConfigs(secret: string, items: { key: string; value: string }[]) {
  return request<{ data: ConfigRow[] }>("/admin-api/config", secret, {
    method: "POST",
    body: JSON.stringify({ items }),
  });
}

export async function deleteConfig(secret: string, key: string) {
  return request<{ data: ConfigRow[] }>(`/admin-api/config/${encodeURIComponent(key)}`, secret, {
    method: "DELETE",
  });
}

export async function updateOrderStatus(secret: string, orderId: string, status: string) {
  return request<{ data: Order[] }>(`/admin-api/orders/${encodeURIComponent(orderId)}`, secret, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function updateOrder(secret: string, orderId: string, payload: Partial<Pick<Order, "status" | "expire_at" | "paid_at" | "expired_notice_at" | "plan_name" | "coupon_code" | "note">>) {
  return request<{ data: Order[] }>(`/admin-api/orders/${encodeURIComponent(orderId)}`, secret, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteOrder(secret: string, orderId: string) {
  return request<{ data: Order[] }>(`/admin-api/orders/${encodeURIComponent(orderId)}`, secret, {
    method: "DELETE",
  });
}

export async function createManualOrder(secret: string, payload: ManualOrderPayload) {
  return request<{ data: ManualOrderResult }>("/admin-api/manual-orders", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMenuPages(secret: string) {
  return request<{ data: MenuPage[] }>("/admin-api/menu-pages", secret);
}

export async function updateMenuPage(secret: string, pageId: string, payload: Partial<MenuPage>) {
  return request<{ data: MenuPage[] }>(`/admin-api/menu-pages/${encodeURIComponent(pageId)}`, secret, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteMenuPage(secret: string, pageId: string) {
  return request<{ data: MenuPage[] }>(`/admin-api/menu-pages/${encodeURIComponent(pageId)}`, secret, {
    method: "DELETE",
  });
}

export async function getSaleRules(secret: string) {
  return request<{ data: SaleRule[] }>("/admin-api/sale-rules", secret);
}

export async function upsertSaleRule(secret: string, payload: Record<string, string>) {
  return request<{ data: SaleRule[] }>("/admin-api/sale-rules", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteSaleRule(secret: string, saleId: string) {
  return request<{ data: SaleRule[] }>(`/admin-api/sale-rules/${encodeURIComponent(saleId)}`, secret, {
    method: "DELETE",
  });
}

export async function getCoupons(secret: string) {
  return request<{ data: Coupon[] }>("/admin-api/coupons", secret);
}

export async function createCoupon(secret: string, payload: Record<string, unknown>) {
  return request<{ data: Coupon[] }>("/admin-api/coupons", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createCoupons(secret: string, items: Record<string, unknown>[]) {
  return request<{ data: Coupon[] }>("/admin-api/coupons/bulk", secret, {
    method: "POST",
    body: JSON.stringify({ items }),
  });
}

export async function deleteCoupon(secret: string, code: string) {
  return request<{ data: Coupon[] }>(`/admin-api/coupons/${encodeURIComponent(code)}`, secret, {
    method: "DELETE",
  });
}

export async function getHiddenGroups(secret: string) {
  return request<{ data: HiddenGroup[] }>("/admin-api/hidden-groups", secret);
}

export async function upsertHiddenGroup(secret: string, payload: Record<string, unknown>) {
  return request<{ data: HiddenGroup[] }>("/admin-api/hidden-groups", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteHiddenGroup(secret: string, hiddenGroupId: string) {
  return request<{ data: HiddenGroup[] }>(`/admin-api/hidden-groups/${encodeURIComponent(hiddenGroupId)}`, secret, {
    method: "DELETE",
  });
}

export async function getHiddenCodes(secret: string) {
  return request<{ data: HiddenCode[] }>("/admin-api/hidden-codes", secret);
}

export async function upsertHiddenCode(secret: string, payload: Record<string, unknown>) {
  return request<{ data: HiddenCode[] }>("/admin-api/hidden-codes", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteHiddenCode(secret: string, code: string) {
  return request<{ data: HiddenCode[] }>(`/admin-api/hidden-codes/${encodeURIComponent(code)}`, secret, {
    method: "DELETE",
  });
}

export async function getHiddenRedemptions(secret: string, limit = 500) {
  return request<{ data: HiddenRedemption[] }>(`/admin-api/hidden-redemptions?limit=${limit}`, secret);
}

export async function getActivationCodes(secret: string, limit = 500) {
  return request<{ data: ActivationCode[] }>(`/admin-api/activation-codes?limit=${limit}`, secret);
}

export async function updateActivationCode(secret: string, code: string, payload: Partial<ActivationCode & { activation_status: string }>) {
  return request<{ data: ActivationCode[] }>(`/admin-api/activation-codes/${encodeURIComponent(code)}`, secret, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteActivationCode(secret: string, code: string) {
  return request<{ data: ActivationCode[] }>(`/admin-api/activation-codes/${encodeURIComponent(code)}`, secret, {
    method: "DELETE",
  });
}

export async function regenerateActivationCode(secret: string, code: string) {
  return request<{ data: ActivationCode[] }>(`/admin-api/activation-codes/${encodeURIComponent(code)}/regenerate`, secret, {
    method: "POST",
  });
}

export async function sendAdminReply(secret: string, payload: { telegram_user_id: string; text: string; source_log_id?: string; source_text?: string; full_name?: string }) {
  return request<{ data: { ok: boolean; message_id?: number | null } }>("/admin-api/admin-replies", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getBlacklist(secret: string) {
  return request<{ data: BlacklistEntry[] }>("/admin-api/blacklist", secret);
}

export async function upsertBlacklist(secret: string, payload: Record<string, string>) {
  return request<{ data: BlacklistEntry[] }>("/admin-api/blacklist", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteBlacklist(secret: string, telegramUserId: string) {
  return request<{ data: BlacklistEntry[] }>(`/admin-api/blacklist/${encodeURIComponent(telegramUserId)}`, secret, {
    method: "DELETE",
  });
}

export async function getSupportEvents(secret: string, limit = 5000) {
  return request<{ data: SupportEvent[] }>(`/admin-api/support-events?limit=${limit}`, secret);
}

export async function getKickAudit(secret: string, live = false) {
  return request<{ data: KickAuditRow[] }>(`/admin-api/kick-audit?live=${live ? "true" : "false"}`, secret);
}

export async function getVipGroupAudit(secret: string, live = false) {
  return request<{ data: VipGroupAuditRow[] }>(`/admin-api/vip-group-audit?live=${live ? "true" : "false"}`, secret);
}

export async function kickAuditMember(secret: string, payload: KickAuditPayload) {
  return request<{ data: KickAuditRow[] }>("/admin-api/kick-audit/kick", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getActivityEvents(secret: string) {
  return request<{ data: ActivityEvent[] }>("/admin-api/activity-events", secret);
}

export async function getCampaigns(secret: string) {
  return request<{ data: BroadcastCampaign[] }>("/admin-api/campaigns", secret);
}

export async function previewCampaign(secret: string, segment: string, planFilter = "ALL", planMatchScope = "ANY_PAID") {
  const params = new URLSearchParams({
    segment,
    plan_filter: planFilter,
    plan_match_scope: planMatchScope,
  });
  return request<{ data: CampaignPreview }>(`/admin-api/campaigns/preview?${params.toString()}`, secret);
}

export async function createCampaign(secret: string, payload: Record<string, unknown>) {
  return request<{ data: BroadcastCampaign }>("/admin-api/campaigns", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getCampaignRecipients(secret: string, campaignId: string, limit = 500) {
  return request<{ data: BroadcastRecipient[] }>(`/admin-api/campaigns/${encodeURIComponent(campaignId)}/recipients?limit=${limit}`, secret);
}

export async function startCampaign(secret: string, campaignId: string) {
  return request<{ data: BroadcastCampaign[] }>(`/admin-api/campaigns/${encodeURIComponent(campaignId)}/start`, secret, { method: "POST" });
}

export async function pauseCampaign(secret: string, campaignId: string) {
  return request<{ data: BroadcastCampaign[] }>(`/admin-api/campaigns/${encodeURIComponent(campaignId)}/pause`, secret, { method: "POST" });
}

export async function cancelCampaign(secret: string, campaignId: string) {
  return request<{ data: BroadcastCampaign[] }>(`/admin-api/campaigns/${encodeURIComponent(campaignId)}/cancel`, secret, { method: "POST" });
}

export async function getChannelPosts(secret: string, limit = 200) {
  return request<{ data: ChannelPost[] }>(`/admin-api/channel-posts?limit=${limit}`, secret);
}

export async function createChannelPost(secret: string, payload: Record<string, unknown>) {
  return request<{ data: ChannelPost }>("/admin-api/channel-posts", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateChannelPost(secret: string, postId: number | string, payload: Record<string, unknown>) {
  return request<{ data: ChannelPost[] }>(`/admin-api/channel-posts/${encodeURIComponent(String(postId))}`, secret, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function channelPostAction(secret: string, postId: number | string, action: string, payload: Record<string, unknown> = {}) {
  return request<{ data: ChannelPost }>(`/admin-api/channel-posts/${encodeURIComponent(String(postId))}/action`, secret, {
    method: "POST",
    body: JSON.stringify({ action, ...payload }),
  });
}

export async function getChannelPostEvents(secret: string, postId: number | string, limit = 200) {
  return request<{ data: ChannelPostEvent[] }>(`/admin-api/channel-posts/${encodeURIComponent(String(postId))}/events?limit=${limit}`, secret);
}

export async function checkSupportGroup(secret: string) {
  return request<{ data: SupportGroupCheck }>("/admin-api/support-group-check", secret);
}

export async function getWebhookInfo(secret: string) {
  return request<{ data: WebhookInfo }>("/admin-api/webhook-info", secret);
}

export async function getBotScheduleStatus(secret: string) {
  return request<{ data: BotScheduleStatus }>("/admin-api/bot-schedule-status", secret);
}

export async function resetWebhook(secret: string) {
  return request<{ data: WebhookInfo }>("/admin-api/webhook-reset", secret, {
    method: "POST",
  });
}
