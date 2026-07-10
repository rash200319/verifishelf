"""raw crawl results

Revision ID: 0006_raw_crawl_results
Revises: 0005_brand_application_fields
Create Date: 2026-07-09
"""

from alembic import op


revision = "0006_raw_crawl_results"
down_revision = "0005_brand_application_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    # Present in schema.sql since early on, but never had a migration --
    # every crawl has been silently failing to persist the raw scraped
    # HTML (caught and logged, doesn't fail the crawl, but the table
    # genuinely didn't exist on any DB bootstrapped via `alembic upgrade
    # head` rather than the raw schema.sql file).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_crawl_results (
            id INT AUTO_INCREMENT PRIMARY KEY,

            crawl_job_id INT NOT NULL,
            brand_id INT NOT NULL,
            product_id INT NOT NULL,

            raw_html LONGTEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (crawl_job_id)
                REFERENCES crawl_jobs(id)
                ON DELETE CASCADE,

            FOREIGN KEY (brand_id)
                REFERENCES brands(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE
        )
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")
    op.execute("DROP TABLE IF EXISTS raw_crawl_results")
