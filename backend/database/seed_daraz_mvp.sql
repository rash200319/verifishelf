-- Daraz MVP seed data for local development and demo crawls.
-- Bootstraps a single brand, product, seller, and marketplace so a fresh
-- database is immediately usable for the Daraz crawl pipeline.
--
-- Day 1 (real proxy integration) note: this brand is routed through Daraz
-- PK, not LK, because the real residential proxy credentials in .env only
-- cover PK/IN today (see PROXY_POOL_PK). LK has no matching pool yet, so a
-- brand_marketplaces row left at country_code='LK' would fail proxy_lookup
-- with ProxyConfigError. The Daraz marketplace row itself stays LK/daraz.lk
-- as the platform default -- only this brand's crawl target is overridden
-- to PK via brand_marketplaces.country_code (see core/marketplaces.py
-- resolve_daraz_market for the LK/PK domain+currency mapping).
--
-- Run after schema.sql:
--   Get-Content backend\database\seed_daraz_mvp.sql | docker exec -i mysql_db mysql -uroot -p<password> verifishelf

USE verifishelf;

-- ─── Marketplace ─────────────────────────────────────────────────────────────
INSERT INTO marketplaces (id, name, country_code, base_url, status)
VALUES (1, 'Daraz', 'LK', 'https://www.daraz.lk', 'live')
ON DUPLICATE KEY UPDATE
    name         = VALUES(name),
    country_code = VALUES(country_code),
    base_url     = VALUES(base_url),
    status       = VALUES(status);

-- ─── Brand ────────────────────────────────────────────────────────────────────
-- status='approved' is required so this brand appears in the active brand list.
INSERT INTO brands (id, name, plan, status, company_name, business_url, torch_sub_id)
VALUES (1, 'Demo Brand', 'starter', 'approved', 'Demo Brand LLC', 'https://demobrand.com', 'torch_demo_brand')
ON DUPLICATE KEY UPDATE
    name          = VALUES(name),
    plan          = VALUES(plan),
    status        = VALUES(status),
    company_name  = VALUES(company_name),
    business_url  = VALUES(business_url),
    torch_sub_id  = VALUES(torch_sub_id);

-- ─── Brand × Marketplace ──────────────────────────────────────────────────────
-- country_code='PK' routes this brand's Daraz crawls to daraz.pk through the
-- real PROXY_POOL_PK residential pool (see note above).
INSERT INTO brand_marketplaces (brand_id, marketplace_id, enabled, crawl_frequency_hrs, country_code, priority)
VALUES (1, 1, 1, 2, 'PK', 1)
ON DUPLICATE KEY UPDATE
    enabled              = VALUES(enabled),
    crawl_frequency_hrs  = VALUES(crawl_frequency_hrs),
    country_code         = VALUES(country_code),
    priority             = VALUES(priority);

-- ─── Products ─────────────────────────────────────────────────────────────────
-- Both names are real, high-volume Daraz search terms (verified against live
-- daraz.lk/daraz.pk ajax search results) so the live crawl returns actual
-- listings instead of a "no_listings_found" failure for a fake product name.
INSERT INTO products (id, brand_id, name, description, map_price)
VALUES (1, 1, 'iPhone 13', 'MAP monitoring demo product for Daraz PK', 250000.00)
ON DUPLICATE KEY UPDATE
    brand_id    = VALUES(brand_id),
    name        = VALUES(name),
    description = VALUES(description),
    map_price   = VALUES(map_price);

INSERT INTO products (id, brand_id, name, description, map_price)
VALUES (2, 1, 'Philips Air Fryer', 'MAP monitoring demo product for Daraz PK', 32000.00)
ON DUPLICATE KEY UPDATE
    brand_id    = VALUES(brand_id),
    name        = VALUES(name),
    description = VALUES(description),
    map_price   = VALUES(map_price);

-- ─── Seller ───────────────────────────────────────────────────────────────────
INSERT INTO sellers (id, seller_name, storefront_url)
VALUES (1, 'Daraz Seller', 'https://www.daraz.pk/shop/demo-seller')
ON DUPLICATE KEY UPDATE
    seller_name    = VALUES(seller_name),
    storefront_url = VALUES(storefront_url);

-- ─── Admin User ───────────────────────────────────────────────────────────────
-- Real bcrypt hash of 'admin123' (auth.py no longer accepts the old 'demo'
-- sentinel -- verify_password only accepts real bcrypt hashes now).
INSERT INTO users (brand_id, full_name, email, password_hash, role, is_active, is_brand_owner)
VALUES (1, 'Admin User', 'admin@verifishelf.local', '$2b$12$gnWosz0QEKkN/zJTaDCL3.uDlQ0zYV9LBIdcYLcXgIg2uWRbFAK0y', 'admin', 1, 1)
ON DUPLICATE KEY UPDATE
    brand_id      = VALUES(brand_id),
    full_name     = VALUES(full_name),
    password_hash = VALUES(password_hash),
    role          = VALUES(role),
    is_active     = VALUES(is_active),
    is_brand_owner = VALUES(is_brand_owner);

-- ─── TorchProxy Superadmin ──────────────────────────────────────────────────────
-- Platform-level admin, not scoped to any brand (brand_id NULL). This is the
-- only account with access to /admin/torchproxy/* (brand approve/reject).
-- Real bcrypt hash of 'TorchAdmin2026!'.
INSERT INTO users (brand_id, full_name, email, password_hash, role, is_active, is_brand_owner)
VALUES (NULL, 'TorchProxy Superadmin', 'superadmin@verifishelf.local', '$2b$12$smU1Vw3IdlAQ7K5Yph/Fv.lPdJ1mf08m5Kb8ZfvSixUIYEJ98Llfm', 'superadmin', 1, 0)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role          = VALUES(role),
    is_active     = VALUES(is_active);
