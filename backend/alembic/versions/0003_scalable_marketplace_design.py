"""scalable marketplace design

Revision ID: 0003_scalable_marketplace_design
Revises: 0002_onboarding_and_invites
Create Date: 2026-07-03
"""

from alembic import op


revision = "0003_scalable_marketplace_design"
down_revision = "0002_onboarding_and_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    op.execute(
        """
        INSERT INTO marketplaces (id, name, country_code, base_url, status)
        VALUES
            (1, 'Daraz', 'LK', 'https://www.daraz.lk', 'live'),
            (2, 'Amazon', 'US', 'https://www.amazon.com', 'live'),
            (3, 'Flipkart', 'IN', 'https://www.flipkart.com', 'live'),
            (4, 'Lazada', 'SG', 'https://www.lazada.com', 'live'),
            (5, 'Tokopedia', 'ID', 'https://www.tokopedia.com', 'live')
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            country_code = VALUES(country_code),
            base_url = VALUES(base_url),
            status = VALUES(status)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS brand_marketplaces (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_id INT NOT NULL,
            marketplace_id INT NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            crawl_frequency_hrs INT NULL,
            country_code VARCHAR(10) NULL,
            priority INT DEFAULT 0,
            last_crawled_at DATETIME NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_brand_marketplace (brand_id, marketplace_id),
            KEY idx_brand_marketplaces_brand_id (brand_id),
            KEY idx_brand_marketplaces_marketplace_id (marketplace_id),
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
        INSERT INTO brand_marketplaces (
            brand_id,
            marketplace_id,
            enabled,
            crawl_frequency_hrs,
            country_code,
            priority
        )
        SELECT
            b.id,
            1,
            TRUE,
            NULL,
            'LK',
            1
        FROM brands b
        ON DUPLICATE KEY UPDATE
            enabled = VALUES(enabled),
            country_code = VALUES(country_code),
            priority = VALUES(priority)
        """
    )

    op.execute(
        """
        ALTER TABLE crawl_jobs
        ADD COLUMN brand_marketplace_id INT NULL AFTER marketplace_id
        """
    )

    op.execute(
        """
        ALTER TABLE crawl_jobs
        ADD CONSTRAINT fk_crawl_jobs_brand_marketplace
        FOREIGN KEY (brand_marketplace_id)
        REFERENCES brand_marketplaces(id)
        ON DELETE SET NULL
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")

    op.execute("ALTER TABLE crawl_jobs DROP FOREIGN KEY fk_crawl_jobs_brand_marketplace")
    op.execute("ALTER TABLE crawl_jobs DROP COLUMN brand_marketplace_id")
    op.execute("DROP TABLE IF EXISTS brand_marketplaces")
