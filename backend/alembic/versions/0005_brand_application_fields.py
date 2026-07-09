"""brand application fields

Revision ID: 0005_brand_application_fields
Revises: 0004_superadmin_role
Create Date: 2026-07-09
"""

from alembic import op


revision = "0005_brand_application_fields"
down_revision = "0004_superadmin_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    # Standard KYB-style fields for the brand registration/approval form --
    # this product drafts enforcement letters in a brand's name, so a
    # superadmin reviewing a new registration needs more than just a name
    # and a URL to judge whether the applicant is a real, authorized brand.
    op.execute(
        """
        ALTER TABLE brands
        ADD COLUMN registration_number VARCHAR(255) NULL,
        ADD COLUMN business_address TEXT NULL,
        ADD COLUMN industry VARCHAR(100) NULL,
        ADD COLUMN contact_title VARCHAR(150) NULL,
        ADD COLUMN contact_phone VARCHAR(50) NULL,
        ADD COLUMN estimated_sku_range VARCHAR(50) NULL,
        ADD COLUMN current_marketplaces VARCHAR(500) NULL,
        ADD COLUMN authorized_attestation BOOLEAN NOT NULL DEFAULT FALSE
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")

    op.execute(
        """
        ALTER TABLE brands
        DROP COLUMN registration_number,
        DROP COLUMN business_address,
        DROP COLUMN industry,
        DROP COLUMN contact_title,
        DROP COLUMN contact_phone,
        DROP COLUMN estimated_sku_range,
        DROP COLUMN current_marketplaces,
        DROP COLUMN authorized_attestation
        """
    )
