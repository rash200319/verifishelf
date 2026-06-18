-- Comprehensive seed data for local development and testing.
-- This script truncates existing tables in the correct order of foreign keys and seeds the database.
-- Run using:
--   Get-Content backend\database\seed_all.sql | docker exec -i mysql_db mysql -uroot -p<password> verifishelf

USE verifishelf;

-- Disable foreign key checks for clean truncation
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE enforcement_letters;
TRUNCATE TABLE violations;
TRUNCATE TABLE price_snapshots;
TRUNCATE TABLE listings;
TRUNCATE TABLE sellers;
TRUNCATE TABLE seller_clusters;
TRUNCATE TABLE crawl_jobs;
TRUNCATE TABLE weekly_reports;
TRUNCATE TABLE promo_windows;
TRUNCATE TABLE brand_invites;
TRUNCATE TABLE users;
TRUNCATE TABLE products;
TRUNCATE TABLE brands;
TRUNCATE TABLE marketplaces;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 1. MARKETPLACES
-- =====================================================
INSERT INTO marketplaces (id, name, country_code, base_url, status) VALUES
(1, 'Daraz', 'LK', 'https://www.daraz.lk', 'live'),
(2, 'Amazon', 'US', 'https://www.amazon.com', 'live');

-- =====================================================
-- 2. BRANDS
-- =====================================================
INSERT INTO brands (id, name, plan, status, company_name, business_url, onboarding_notes, review_notes, reviewed_by, reviewed_at, torch_sub_id) VALUES
-- Approved Brand 1: Demo Brand (Starter)
(1, 'Demo Brand', 'starter', 'approved', 'Demo Brand LLC', 'https://demobrand.com', 'Initial onboarding note', 'Looks legitimate, approved.', 'system_admin', NOW(), 'torch_demo_brand'),
-- Approved Brand 2: Acme Corp (Growth)
(2, 'Acme Corp', 'growth', 'approved', 'Acme Corp Ltd', 'https://acme.com', 'Transitioning from legacy solution', 'Approved for growth plan.', 'system_admin', NOW(), 'torch_acme_corp'),
-- Approved Brand 3: Global Tech (Enterprise)
(3, 'Global Tech', 'enterprise', 'approved', 'Global Tech Inc', 'https://globaltech.com', 'Enterprise account setup', 'Approved.', 'system_admin', NOW(), 'torch_global_tech'),
-- Pending Brand: Pending Inc
(4, 'Pending Inc', 'starter', 'pending_review', 'Pending Inc', 'https://pendinginc.com', 'Looking to start tracking ASAP', NULL, NULL, NULL, 'torch_pending_inc'),
-- Rejected Brand: Rejected Ltd
(5, 'Rejected Ltd', 'starter', 'rejected', 'Rejected Ltd', 'https://rejected.com', 'Suspicious registration request', 'Rejected: website URL is inactive and domain registration name does not match business.', 'system_admin', NOW(), 'torch_rejected_ltd'),
-- Needs More Info Brand: Needs Info Corp
(6, 'Needs Info Corp', 'growth', 'needs_more_info', 'Needs Info Corp', 'https://needsinfo.com', 'Growth plan request', 'Requested more info: Please provide business registration details.', 'system_admin', NOW(), 'torch_needs_info_corp');

-- =====================================================
-- 3. USERS
-- =====================================================
-- All seeded users use 'demo' as password_hash. The verify_password helper maps 'demo' to password 'admin123'.
INSERT INTO users (id, brand_id, full_name, email, password_hash, role, is_active, is_brand_owner, invite_accepted_at) VALUES
-- Users for Brand 1 (Demo Brand)
(1, 1, 'Brand Admin User', 'admin@verifishelf.local', 'demo', 'admin', 1, 1, NOW()),
(2, 1, 'Brand Analyst User', 'analyst@verifishelf.local', 'demo', 'analyst', 1, 0, NOW()),

-- Users for Brand 2 (Acme Corp)
(3, 2, 'Acme Admin', 'admin@acme.com', 'demo', 'admin', 1, 1, NOW()),
(4, 2, 'Acme Analyst', 'analyst@acme.com', 'demo', 'analyst', 1, 0, NOW()),

-- Users for Brand 3 (Global Tech)
(5, 3, 'Global Tech Admin', 'admin@globaltech.com', 'demo', 'admin', 1, 1, NOW()),

-- Users for Brand 4 (Pending Inc)
(6, 4, 'Pending Owner', 'owner@pendinginc.com', 'demo', 'admin', 0, 1, NULL);

-- =====================================================
-- 4. PRODUCTS
-- =====================================================
INSERT INTO products (id, brand_id, name, description, map_price) VALUES
-- Brand 1 Products
(1, 1, 'Demo Product 1', 'MAP monitoring demo product 1', 25000.00),
(2, 1, 'Demo Product 2', 'MAP monitoring demo product 2', 15000.00),

-- Brand 2 Products
(3, 2, 'Acme Widget A', 'Standard Acme widget A', 50.00),
(4, 2, 'Acme Widget B', 'Premium Acme widget B', 120.00),

-- Brand 3 Products
(5, 3, 'Global Smartphone', 'Flagship enterprise device', 999.00);

-- =====================================================
-- 5. SELLER CLUSTERS
-- =====================================================
INSERT INTO seller_clusters (id, cluster_name, risk_score) VALUES
(1, 'High Risk Daraz Cluster', 88.50),
(2, 'Low Risk Amazon Cluster', 12.20);

-- =====================================================
-- 6. SELLERS
-- =====================================================
INSERT INTO sellers (id, cluster_id, seller_name, storefront_url, embedding) VALUES
(1, 1, 'Daraz Discount Store', 'https://www.daraz.lk/shop/daraz-discount-store', NULL),
(2, 2, 'Acme Official Store', 'https://www.daraz.lk/shop/acme-official', NULL),
(3, 2, 'Amazon Seller Pro', 'https://www.amazon.com/sp?seller=A123', NULL);

-- =====================================================
-- 7. LISTINGS
-- =====================================================
INSERT INTO listings (id, product_id, seller_id, marketplace_id, listing_title, listing_url, image_url, advertised_price, currency_code, scraped_at) VALUES
-- Listing 1: Brand 1 Product 1 (MAP 25000), listed at 24000 LKR (Violation)
(1, 1, 1, 1, 'Demo Product 1 Super Sale', 'https://www.daraz.lk/products/demo-1-sale', 'https://verifishelf.local/images/demo1.jpg', 24000.00, 'LKR', NOW()),
-- Listing 2: Brand 1 Product 2 (MAP 15000), listed at 15000 LKR (No Violation)
(2, 2, 2, 1, 'Demo Product 2 Official', 'https://www.daraz.lk/products/demo-2', 'https://verifishelf.local/images/demo2.jpg', 15000.00, 'LKR', NOW()),
-- Listing 3: Brand 2 Product 3 (MAP 50), listed at 45 USD (Violation)
(3, 3, 3, 2, 'Acme Widget A Cheap', 'https://www.amazon.com/dp/B001', 'https://verifishelf.local/images/widgeta.jpg', 45.00, 'USD', NOW()),
-- Listing 4: Brand 2 Product 4 (MAP 120), listed at 100 USD (Allowed due to Father''s Day Promo)
(4, 4, 3, 2, 'Acme Widget B Promo Deal', 'https://www.amazon.com/dp/B002', 'https://verifishelf.local/images/widgetb.jpg', 100.00, 'USD', NOW());

-- =====================================================
-- 8. PRICE SNAPSHOTS
-- =====================================================
INSERT INTO price_snapshots (listing_id, product_id, seller_id, price, snapshot_time) VALUES
(1, 1, 1, 24000.00, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(1, 1, 1, 24000.00, NOW()),
(2, 2, 2, 15000.00, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(3, 3, 3, 45.00, NOW()),
(4, 4, 3, 100.00, NOW());

-- =====================================================
-- 9. PROMO WINDOWS
-- =====================================================
INSERT INTO promo_windows (id, brand_id, product_id, marketplace_id, start_date, end_date, notes) VALUES
-- Expired promo window for Brand 1 Product 1
(1, 1, 1, 1, DATE_SUB(CURDATE(), INTERVAL 15 DAY), DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'Early Summer Sale'),
-- Active promo window for Brand 2 Product 4
(2, 2, 4, 2, DATE_SUB(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 5 DAY), 'Father''s Day Promotion');

-- =====================================================
-- 10. VIOLATIONS
-- =====================================================
INSERT INTO violations (id, listing_id, map_price, advertised_price, price_delta_pct, classifier_confidence, classifier_type, status, detected_at) VALUES
-- Violation on Listing 1 (Open)
(1, 1, 25000.00, 24000.00, 4.00, 0.92, 'price_tracker', 'open', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
-- Violation on Listing 3 (Open)
(2, 3, 50.00, 45.00, 10.00, 0.98, 'price_tracker', 'open', NOW()),
-- Violation on Listing 4 (Dismissed - falls in Promo Window)
(3, 4, 120.00, 100.00, 16.67, 0.95, 'price_tracker', 'dismissed', NOW());

-- =====================================================
-- 11. ENFORCEMENT LETTERS
-- =====================================================
INSERT INTO enforcement_letters (id, violation_id, letter_content, generated_by, generated_at) VALUES
(1, 1, 'Dear Seller,\n\nWe have detected that you are listing "Demo Product 1" at LKR 24,000.00, which is below our Minimum Advertised Price (MAP) of LKR 25,000.00.\n\nPlease update your listing pricing immediately.\n\nRegards,\nBrand Enforcement Team', 'gpt4o', DATE_SUB(NOW(), INTERVAL 1 HOUR));

-- =====================================================
-- 12. WEEKLY REPORTS
-- =====================================================
INSERT INTO weekly_reports (id, brand_id, report_start_date, report_end_date, report_content, generated_at) VALUES
(1, 1, DATE_SUB(CURDATE(), INTERVAL 7 DAY), CURDATE(), '--- Weekly MAP Monitoring Report ---\n\nSummary for Demo Brand:\n- Products Monitored: 2\n- Active Listings: 2\n- Violations Detected: 1 (Demo Product 1)\n- Action Taken: Enforcement letter sent to Daraz Discount Store.\n\nStatus is clean for Demo Product 2.', NOW());

-- =====================================================
-- 13. BRAND INVITES
-- =====================================================
INSERT INTO brand_invites (id, brand_id, email, role, invite_code_hash, expires_at, used_at, created_by) VALUES
-- Active Invite
(1, 1, 'new-analyst@verifishelf.local', 'analyst', 'b801a2f6479f60f64c12', DATE_ADD(NOW(), INTERVAL 7 DAY), NULL, 1),
-- Expired Invite
(2, 1, 'expired@verifishelf.local', 'analyst', 'e100f91e92d77d73010b', DATE_SUB(NOW(), INTERVAL 1 DAY), NULL, 1),
-- Used Invite
(3, 2, 'joined-teammate@acme.com', 'analyst', 'a28c30d9fb823023023e', DATE_ADD(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY), 3);

-- =====================================================
-- 14. CRAWL JOBS
-- =====================================================
INSERT INTO crawl_jobs (id, brand_id, marketplace_id, status, started_at, finished_at) VALUES
(1, 1, 1, 'completed', DATE_SUB(NOW(), INTERVAL 1 HOUR), DATE_SUB(NOW(), INTERVAL 59 MINUTE)),
(2, 2, 2, 'completed', DATE_SUB(NOW(), INTERVAL 30 MINUTE), DATE_SUB(NOW(), INTERVAL 28 MINUTE));
