"""superadmin role

Revision ID: 0004_superadmin_role
Revises: 0003_scalable_marketplace_design
Create Date: 2026-07-09
"""

from alembic import op


revision = "0004_superadmin_role"
down_revision = "0003_scalable_marketplace_design"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("USE verifishelf")

    # A superadmin (TorchProxy platform admin) isn't scoped to any single
    # brand, so brand_id must be nullable for that row. Existing brand
    # users are unaffected -- this only widens what's allowed, it doesn't
    # change any existing NOT NULL data.
    op.execute(
        """
        ALTER TABLE users
        MODIFY COLUMN brand_id INT NULL
        """
    )

    op.execute(
        """
        ALTER TABLE users
        MODIFY COLUMN role ENUM('admin','analyst','superadmin') DEFAULT 'admin'
        """
    )


def downgrade() -> None:
    op.execute("USE verifishelf")

    op.execute(
        """
        ALTER TABLE users
        MODIFY COLUMN role ENUM('admin','analyst') DEFAULT 'admin'
        """
    )

    op.execute(
        """
        ALTER TABLE users
        MODIFY COLUMN brand_id INT NOT NULL
        """
    )
