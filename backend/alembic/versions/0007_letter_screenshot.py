"""enforcement letter screenshot

Revision ID: 0007_letter_screenshot
Revises: 0006_raw_crawl_results
Create Date: 2026-07-10
"""

from alembic import op


revision = "0007_letter_screenshot"
down_revision = "0006_raw_crawl_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    op.execute(
        """
        ALTER TABLE enforcement_letters
        ADD COLUMN screenshot_base64 LONGTEXT NULL
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")
    op.execute("ALTER TABLE enforcement_letters DROP COLUMN screenshot_base64")
