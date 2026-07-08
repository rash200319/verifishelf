export type AuthRole = "admin" | "analyst";

export interface SessionData {
  access_token: string;
  token_type: "bearer";
  user_id: number;
  brand_id: number;
  brand_name: string;
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

export interface PendingBrand {
  id: number;
  name: string;
  status: string;
  company_name: string;
  business_url: string;
  onboarding_notes: string;
  created_at: string;
}

export interface PendingBrandsResponse {
  brands: PendingBrand[];
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
  narrative_source?: string;
  generated_at: string;
}

export interface ViolationListingInfo {
  id: number;
  product_id: number;
  seller_id: number;
  marketplace_id: number;
  listing_title: string;
  listing_url: string;
  image_url?: string | null;
  currency_code: string;
  seller_name?: string | null;
  product_name?: string | null;
}

export interface ViolationRecord {
  id: number;
  listing_id: number;
  map_price: number;
  advertised_price: number;
  price_delta_pct: number | null;
  classifier_confidence: number | null;
  classifier_type: string | null;
  status: string;
  severity: string | null;
  detected_at: string;
  listing: ViolationListingInfo | null;
}

export interface EnforcementLetterRecord {
  id: number;
  violation_id: number;
  letter_content: string;
  generated_by: string;
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

export interface MarketplaceFeaturedItem {
  title: string;
  url?: string | null;
  image_url?: string | null;
  rating_value?: number | null;
  rating_count?: number | null;
}

export interface MarketplacePreviewRecord {
  marketplace: string;
  source_file: string;
  source_url?: string | null;
  page_title?: string | null;
  meta_description?: string | null;
  has_next_page: boolean;
  has_json_ld: boolean;
  json_ld_types: string[];
  verification_hint?: string | null;
  featured_items: MarketplaceFeaturedItem[];
}
