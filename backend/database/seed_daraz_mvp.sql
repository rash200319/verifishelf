-- Daraz MVP seed data for local development and demo crawls.
-- Run after schema.sql:
--   docker exec -i mysql_db mysql -uroot -p<password> verifishelf < backend/database/seed_daraz_mvp.sql

USE verifishelf;

INSERT INTO marketplaces (id, name, country_code, base_url, status)
VALUES (1, 'Daraz', 'LK', 'https://www.daraz.lk', 'live')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    country_code = VALUES(country_code),
    base_url = VALUES(base_url),
    status = VALUES(status);

INSERT INTO brands (id, name, plan, torch_sub_id)
VALUES (1, 'Demo Brand', 'starter', 'torch_demo_brand')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    plan = VALUES(plan),
    torch_sub_id = VALUES(torch_sub_id);

INSERT INTO products (id, brand_id, name, description, map_price)
VALUES (1, 1, 'Demo Product', 'MAP monitoring demo product for Daraz LK', 25000.00)
ON DUPLICATE KEY UPDATE
    brand_id = VALUES(brand_id),
    name = VALUES(name),
    description = VALUES(description),
    map_price = VALUES(map_price);

INSERT INTO sellers (id, seller_name, storefront_url)
VALUES (1, 'Daraz Seller', 'https://www.daraz.lk/shop/demo-seller')
ON DUPLICATE KEY UPDATE
    seller_name = VALUES(seller_name),
    storefront_url = VALUES(storefront_url);

INSERT INTO users (brand_id, full_name, email, password_hash, role)
VALUES (1, 'Admin User', 'admin@verifishelf.local', 'demo', 'admin')
ON DUPLICATE KEY UPDATE
    brand_id = VALUES(brand_id),
    full_name = VALUES(full_name),
    password_hash = VALUES(password_hash),
    role = VALUES(role);
