CREATE DATABASE IF NOT EXISTS verifishelf;
USE verifishelf;

-- =====================================================
-- BRANDS
-- =====================================================

CREATE TABLE brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan ENUM('starter','growth','enterprise') DEFAULT 'starter',
    status ENUM('pending_review','approved','rejected','needs_more_info') DEFAULT 'pending_review',
    company_name VARCHAR(255),
    business_url TEXT,
    onboarding_notes TEXT,
    review_notes TEXT,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP NULL,
    torch_sub_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PRODUCTS
-- =====================================================

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    map_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE CASCADE
);

-- =====================================================
-- MARKETPLACES
-- =====================================================

CREATE TABLE marketplaces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_code VARCHAR(10) NOT NULL,
    base_url TEXT,
    status ENUM('live','pending') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SELLER CLUSTERS
-- =====================================================

CREATE TABLE seller_clusters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cluster_name VARCHAR(255),
    risk_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SELLERS
-- =====================================================

CREATE TABLE sellers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cluster_id INT NULL,

    seller_name VARCHAR(255) NOT NULL,
    storefront_url TEXT,

    -- Store sentence-transformer embeddings here
    embedding JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cluster_id)
        REFERENCES seller_clusters(id)
        ON DELETE SET NULL
);

-- =====================================================
-- LISTINGS
-- =====================================================

CREATE TABLE listings (
    id INT AUTO_INCREMENT PRIMARY KEY,

    product_id INT NOT NULL,
    seller_id INT NOT NULL,
    marketplace_id INT NOT NULL,

    listing_title TEXT NOT NULL,
    listing_url TEXT NOT NULL,
    image_url TEXT,

    advertised_price DECIMAL(10,2) NOT NULL,
    currency_code VARCHAR(10) DEFAULT 'USD',

    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    FOREIGN KEY (seller_id)
        REFERENCES sellers(id)
        ON DELETE CASCADE,

    FOREIGN KEY (marketplace_id)
        REFERENCES marketplaces(id)
        ON DELETE CASCADE
);

-- =====================================================
-- PRICE SNAPSHOTS
-- =====================================================

CREATE TABLE price_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    listing_id INT NOT NULL,
    product_id INT NOT NULL,
    seller_id INT NOT NULL,

    price DECIMAL(10,2) NOT NULL,

    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (listing_id)
        REFERENCES listings(id)
        ON DELETE CASCADE,

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    FOREIGN KEY (seller_id)
        REFERENCES sellers(id)
        ON DELETE CASCADE
);

-- ======================================================
-- PROMO WINDOWS
-- =====================================================

CREATE TABLE promo_windows (
    id INT AUTO_INCREMENT PRIMARY KEY,

    brand_id INT NOT NULL,
    product_id INT NOT NULL,
    marketplace_id INT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE CASCADE,

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    FOREIGN KEY (marketplace_id)
        REFERENCES marketplaces(id)
        ON DELETE SET NULL
);

-- =====================================================
-- VIOLATIONS
-- =====================================================

CREATE TABLE violations (
    id INT AUTO_INCREMENT PRIMARY KEY,

    listing_id INT NOT NULL,

    map_price DECIMAL(10,2) NOT NULL,
    advertised_price DECIMAL(10,2) NOT NULL,

    price_delta_pct DECIMAL(8,2),

    classifier_confidence DECIMAL(5,2),

    classifier_type VARCHAR(50),

    status ENUM(
        'open',
        'reviewed',
        'dismissed',
        'resolved'
    ) DEFAULT 'open',

    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (listing_id)
        REFERENCES listings(id)
        ON DELETE CASCADE
);

-- =====================================================
-- ENFORCEMENT LETTERS
-- =====================================================

CREATE TABLE enforcement_letters (
    id INT AUTO_INCREMENT PRIMARY KEY,

    violation_id INT NOT NULL,

    letter_content LONGTEXT NOT NULL,

    generated_by VARCHAR(50) DEFAULT 'gpt4o',

    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (violation_id)
        REFERENCES violations(id)
        ON DELETE CASCADE
);

-- =====================================================
-- WEEKLY REPORTS
-- =====================================================

CREATE TABLE weekly_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,

    brand_id INT NOT NULL,

    report_start_date DATE NOT NULL,
    report_end_date DATE NOT NULL,

    report_content LONGTEXT,

    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE CASCADE
);

-- =====================================================
-- BRAND INVITES
-- =====================================================

CREATE TABLE brand_invites (
    id INT AUTO_INCREMENT PRIMARY KEY,

    brand_id INT NOT NULL,
    email VARCHAR(255),
    role ENUM('admin','analyst') DEFAULT 'analyst',
    invite_code_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_by INT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE CASCADE
);

-- =====================================================
-- CRAWL JOBS
-- =====================================================

CREATE TABLE crawl_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,

    brand_id INT NOT NULL,
    marketplace_id INT NOT NULL,

    status ENUM(
        'queued',
        'running',
        'completed',
        'failed'
    ) DEFAULT 'queued',

    started_at DATETIME NULL,
    finished_at DATETIME NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE CASCADE,

    FOREIGN KEY (marketplace_id)
        REFERENCES marketplaces(id)
        ON DELETE CASCADE
);

-- =====================================================
-- USERS (LOGIN)
-- =====================================================

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,

    brand_id INT NOT NULL,

    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    role ENUM('admin','analyst') DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    is_brand_owner BOOLEAN DEFAULT FALSE,
    invite_accepted_at TIMESTAMP NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE CASCADE
);
