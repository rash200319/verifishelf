"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-06-15
"""

from alembic import op


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE DATABASE IF NOT EXISTS verifishelf")
    op.execute("USE verifishelf")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS brands (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            plan ENUM('starter','growth','enterprise') DEFAULT 'starter',
            torch_sub_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            map_price DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id)
                REFERENCES brands(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS marketplaces (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            country_code VARCHAR(10) NOT NULL,
            base_url TEXT,
            status ENUM('live','pending') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS seller_clusters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cluster_name VARCHAR(255),
            risk_score DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sellers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cluster_id INT NULL,
            seller_name VARCHAR(255) NOT NULL,
            storefront_url TEXT,
            embedding JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cluster_id)
                REFERENCES seller_clusters(id)
                ON DELETE SET NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
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
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS price_snapshots (
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
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS promo_windows (
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
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS violations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            listing_id INT NOT NULL,
            map_price DECIMAL(10,2) NOT NULL,
            advertised_price DECIMAL(10,2) NOT NULL,
            price_delta_pct DECIMAL(8,2),
            classifier_confidence DECIMAL(5,2),
            classifier_type VARCHAR(50),
            status ENUM('open','reviewed','dismissed','resolved') DEFAULT 'open',
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (listing_id)
                REFERENCES listings(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS enforcement_letters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            violation_id INT NOT NULL,
            letter_content LONGTEXT NOT NULL,
            generated_by VARCHAR(50) DEFAULT 'gpt4o',
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (violation_id)
                REFERENCES violations(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_id INT NOT NULL,
            report_start_date DATE NOT NULL,
            report_end_date DATE NOT NULL,
            report_content LONGTEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id)
                REFERENCES brands(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS crawl_jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_id INT NOT NULL,
            marketplace_id INT NOT NULL,
            status ENUM('queued','running','completed','failed') DEFAULT 'queued',
            started_at DATETIME NULL,
            finished_at DATETIME NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id)
                REFERENCES brands(id)
                ON DELETE CASCADE,
            FOREIGN KEY (marketplace_id)
                REFERENCES marketplaces(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_id INT NOT NULL,
            full_name VARCHAR(255),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin','analyst') DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id)
                REFERENCES brands(id)
                ON DELETE CASCADE
        )
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS crawl_jobs")
    op.execute("DROP TABLE IF EXISTS weekly_reports")
    op.execute("DROP TABLE IF EXISTS enforcement_letters")
    op.execute("DROP TABLE IF EXISTS violations")
    op.execute("DROP TABLE IF EXISTS promo_windows")
    op.execute("DROP TABLE IF EXISTS price_snapshots")
    op.execute("DROP TABLE IF EXISTS listings")
    op.execute("DROP TABLE IF EXISTS sellers")
    op.execute("DROP TABLE IF EXISTS seller_clusters")
    op.execute("DROP TABLE IF EXISTS marketplaces")
    op.execute("DROP TABLE IF EXISTS products")
    op.execute("DROP TABLE IF EXISTS brands")
