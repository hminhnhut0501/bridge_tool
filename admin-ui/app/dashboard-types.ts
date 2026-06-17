export type ConfigField = {
  key: string;
  label: string;
  placeholder: string;
  help: string;
  kind?: "input" | "textarea" | "select";
  options?: { label: string; value: string }[];
};

export type OrderPeriod = "all" | "today" | "7d" | "month" | "year";
