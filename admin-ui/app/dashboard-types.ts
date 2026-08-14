export type ConfigField = {
  key: string;
  label: string;
  placeholder: string;
  help: string;
  kind?: "input" | "textarea" | "select" | "multi_select" | "multiselect";
  options?: { label: string; value: string }[];
};

export type OrderPeriod = "all" | "today" | "7d" | "month" | "year";

export type RenewalKickV2TaskRow = {
  id: string;
  order_id: string;
  telegram_user_id: string;
  plan_name: string;
  task_state: string;
  due_at: string;
  locked_at: string | null;
  locked_by: string | null;
  last_transition_at: string;
  total_groups: number;
  kicked_groups: number;
  retained_groups: number;
  pending_groups: number;
  error_groups: number;
  review_groups: number;
  attempt_count: number;
  confirm_count: number;
  retry_count: number;
  last_error: string | null;
  last_reason: string | null;
  review_reason: string | null;
  terminal_reason: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  resolved_at: string | null;
};

export type RenewalKickV2GroupTaskRow = {
  id: string;
  task_id: string;
  order_id: string;
  telegram_user_id: string;
  group_id: string;
  group_name: string;
  group_no: string | null;
  plan_name: string;
  group_state: string;
  attempt_count: number;
  confirm_count: number;
  locked_at: string | null;
  locked_by: string | null;
  first_due_at: string | null;
  next_retry_at: string | null;
  last_transition_at: string;
  last_error: string | null;
  last_reason: string | null;
  review_reason: string | null;
  terminal_reason: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  resolved_at: string | null;
};

export type RenewalKickV2AttemptRow = {
  id: string;
  task_id: string;
  group_task_id: string | null;
  order_id: string;
  telegram_user_id: string;
  group_id: string;
  group_name: string;
  attempt_no: number;
  attempt_state: string;
  action: string;
  actor: string;
  reason_code: string | null;
  error_code: string | null;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
  metadata: Record<string, unknown>;
};

export type RenewalAdminViewGroupRow = {
  group_id: string;
  group_name: string;
  group_state: string;
  status: string;
  latest_error: string;
};

export type RenewalAdminViewRow = {
  order_id: string;
  telegram_user_id: string;
  customer_name: string;
  plan_name: string;
  expire_at: string;
  task_state: string;
  kick_state: string;
  status: string;
  status_label: string;
  needs_action: boolean;
  task_id: string;
  group_count: number;
  kicked_count: number;
  blocked_count: number;
  review_count: number;
  pending_count: number;
  latest_kick_at: string;
  latest_error: string;
  groups: RenewalAdminViewGroupRow[];
  attempt_count: number;
  reason: string;
};

export type RenewalAdminView = {
  rows: RenewalAdminViewRow[];
  summary: {
    total: number;
    needs_action: number;
    done: number;
    review: number;
    blocked: number;
    processing: number;
  };
};
