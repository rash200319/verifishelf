export type AuthRole = "superadmin" | "admin" | "analyst";

export interface SessionData {
  access_token: string;
  token_type: "bearer";
  user_id: number;
  // Null for a superadmin -- not scoped to any brand.
  brand_id: number | null;
  brand_name: string | null;
  // "approved" once the brand has completed onboarding; null for a
  // superadmin (not scoped to any brand).
  brand_status: string | null;
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
  registration_number?: string | null;
  business_address?: string | null;
  industry?: string | null;
  contact_title?: string | null;
  contact_phone?: string | null;
  estimated_sku_range?: string | null;
  current_marketplaces?: string | null;
  authorized_attestation?: boolean;
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

export interface ProductRecord {
  id: number;
  brand_id: number;
  name: string;
  description: string | null;
  map_price: number;
  created_at: string;
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
  repeat_offenders: number;
}

export interface WeeklyReportProductStat {
  product_id: number;
  product_name: string;
  map_price: number;
  avg_observed_price: number | null;
  snapshot_count: number;
  latest_price: number | null;
  price_90d_start: number | null;
  price_90d_end: number | null;
  price_drift_pct: number | null;
}

export interface WeeklyReportOffendingSeller {
  seller_id: number;
  seller_name: string;
  violation_count: number;
  listing_url: string | null;
}

export interface WeeklyReportRecord {
  id: number;
  brand_id: number;
  report_start_date: string;
  report_end_date: string;
  summary: WeeklyReportSummary;
  products: WeeklyReportProductStat[];
  top_offending_sellers: WeeklyReportOffendingSeller[];
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
  last_detected_at: string;
  reopened_count: number;
  listing: ViolationListingInfo | null;
}

export interface EnforcementLetterRecord {
  id: number;
  violation_id: number;
  letter_content: string;
  generated_by: string;
  screenshot_base64: string | null;
  status: string;
  sent_at: string | null;
  generated_at: string;
}

export interface SellerSignature {
  signature_hash?: string | null;
  normalized_name?: string | null;
  storefront_hint?: string | null;
  linkage_method?: string | null;
}

export interface ClusterSellerRecord {
  seller_id: number;
  seller_name: string;
  storefront_url?: string | null;
  signature?: SellerSignature | null;
  open_violation_count: number;
}

export interface SellerClusterRecord {
  cluster_id: number;
  cluster_name?: string | null;
  risk_score?: number | null;
  open_violation_count: number;
  sellers: ClusterSellerRecord[];
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

export interface ProxyHealthRecord {
  proxy: string;
  country: string | null;
  type: string | null;
  healthy: boolean;
  consecutive_failures: number;
  last_success_at: number | null;
  last_failure_at: number | null;
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
