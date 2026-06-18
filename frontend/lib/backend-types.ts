export type AuthRole = "admin" | "analyst";

export interface SessionData {
  access_token: string;
  token_type: "bearer";
  user_id: number;
  brand_id: number;
  brand_name: string;
  brandName?: string;
  role: AuthRole | string;
  email?: string;
}

export interface LoginResponse extends SessionData {}

export interface BrandOnboardResponse {
  message: string;
  brand: {
    id: number;
    name: string;
    plan: "starter" | "growth" | "enterprise" | string;
    torch_sub_id: string;
    created_at: string;
  };
}

export interface CreateUserResponse {
  message: string;
  user: {
    id: number;
    brand_id: number;
    full_name: string;
    email: string;
    role: string;
    created_at: string;
  };
}

export interface PromoRecord {
  id: number;
  brand_id: number;
  product_id: number;
  marketplace_id: number | null;
  start_date: string;
  end_date: string;
  notes: string | null;
  created_at: string;
}

export interface WeeklyReportSummary {
  listings_monitored: number;
  price_snapshots: number;
  violations_detected: number;
  violations_open: number;
  active_promo_windows: number;
}

export interface WeeklyReportProductStat {
  product_id: number;
  product_name: string;
  map_price: number;
  avg_observed_price: number | null;
  snapshot_count: number;
  latest_price: number | null;
}

export interface WeeklyReportRecord {
  id: number;
  brand_id: number;
  report_start_date: string;
  report_end_date: string;
  summary: WeeklyReportSummary;
  products: WeeklyReportProductStat[];
  narrative: string;
  generated_at: string;
}

export interface CrawlJobRecord {
  id: number;
  brand_id: number;
  marketplace_id: number;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface CrawlScheduleRecord {
  demo_mode: boolean;
  marketplace: string;
  country_code: string;
  scheduler_tick_seconds: number;
  intervals_seconds: Record<string, number>;
}
