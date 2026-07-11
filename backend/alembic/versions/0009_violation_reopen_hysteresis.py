"""violation reopen tracking + resolve hysteresis

Revision ID: 0009_violation_reopen_hysteresis
Revises: 0008_letter_sent_status
Create Date: 2026-07-11

Previously a violation resolved the instant one crawl saw
advertised_price >= map_price, and the next crawl to see it drop back
below MAP had no open row to match, so it inserted a brand-new,
unrelated violation. On a flickering price this produced dozens of rows
for what was really one ongoing issue. This adds:
  - resolved_at / last_detected_at so a listing's most recently resolved
    violation can be reopened (instead of re-inserted) if it drops below
    MAP again within a short window.
  - reopened_count to keep a visible signal of how often that's happened.
  - consecutive_compliant_checks so resolving requires sustained
    compliance (2 consecutive checks) rather than one crawl's reading.
"""

from alembic import op


revision = "0009_violation_reopen_hysteresis"
down_revision = "0008_letter_sent_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    op.execute(
        """
        ALTER TABLE violations
        ADD COLUMN resolved_at TIMESTAMP NULL,
        ADD COLUMN last_detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ADD COLUMN reopened_count INT NOT NULL DEFAULT 0,
        ADD COLUMN consecutive_compliant_checks INT NOT NULL DEFAULT 0
        """
    )

    # ADD COLUMN ... DEFAULT CURRENT_TIMESTAMP stamps existing rows with the
    # time of this ALTER, not their real detection time -- backfill from the
    # column that actually has it.
    op.execute("UPDATE violations SET last_detected_at = detected_at")


def downgrade() -> None:
    op.execute("USE verifishelf")
    op.execute(
        """
        ALTER TABLE violations
        DROP COLUMN resolved_at,
        DROP COLUMN last_detected_at,
        DROP COLUMN reopened_count,
        DROP COLUMN consecutive_compliant_checks
        """
    )
