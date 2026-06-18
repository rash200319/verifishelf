"""onboarding and invites

Revision ID: 0002_onboarding_and_invites
Revises: 0001_initial_schema
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_onboarding_and_invites"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    # 1. Update brands table to match schema.sql:
    op.execute(
        """
        ALTER TABLE brands
        ADD COLUMN status ENUM('pending_review','approved','rejected','needs_more_info') DEFAULT 'pending_review',
        ADD COLUMN company_name VARCHAR(255),
        ADD COLUMN business_url TEXT,
        ADD COLUMN onboarding_notes TEXT,
        ADD COLUMN review_notes TEXT,
        ADD COLUMN reviewed_by VARCHAR(255),
        ADD COLUMN reviewed_at TIMESTAMP NULL
        """
    )

    # 2. Update users table to match schema.sql:
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
        ADD COLUMN is_brand_owner BOOLEAN DEFAULT FALSE,
        ADD COLUMN invite_accepted_at TIMESTAMP NULL
        """
    )

    # 3. Create brand_invites table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS brand_invites (
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
        )
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")
    op.execute("DROP TABLE IF EXISTS brand_invites")

    op.execute(
        """
        ALTER TABLE users
        DROP COLUMN is_active,
        DROP COLUMN is_brand_owner,
        DROP COLUMN invite_accepted_at
        """
    )

    op.execute(
        """
        ALTER TABLE brands
        DROP COLUMN status,
        DROP COLUMN company_name,
        DROP COLUMN business_url,
        DROP COLUMN onboarding_notes,
        DROP COLUMN review_notes,
        DROP COLUMN reviewed_by,
        DROP COLUMN reviewed_at
        """
    )
