"""enforcement letter sent status

Revision ID: 0008_letter_sent_status
Revises: 0007_letter_screenshot
Create Date: 2026-07-10
"""

from alembic import op


revision = "0008_letter_sent_status"
down_revision = "0007_letter_screenshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    op.execute(
        """
        ALTER TABLE enforcement_letters
        ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'draft',
        ADD COLUMN sent_at TIMESTAMP NULL
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")
    op.execute(
        """
        ALTER TABLE enforcement_letters
        DROP COLUMN status,
        DROP COLUMN sent_at
        """
    )
