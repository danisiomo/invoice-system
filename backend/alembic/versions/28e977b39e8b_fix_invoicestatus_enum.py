"""fix invoicestatus enum

Revision ID: 28e977b39e8b
Revises:
Create Date: 2026-05-12

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '28e977b39e8b'
down_revision: Union[str, None] = 'bfcb60686521'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE invoices ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE invoices ALTER COLUMN status TYPE varchar(50)")
    op.execute("DROP TYPE IF EXISTS invoicestatus")
    op.execute("CREATE TYPE invoicestatus AS ENUM ('draft', 'review', 'approved', 'sent', 'error')")
    op.execute("ALTER TABLE invoices ALTER COLUMN status TYPE invoicestatus USING status::invoicestatus")
    op.execute("ALTER TABLE invoices ALTER COLUMN status SET DEFAULT 'draft'")

    op.execute("ALTER TABLE invoice_drafts ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE invoice_drafts ALTER COLUMN status TYPE varchar(50)")
    op.execute("DROP TYPE IF EXISTS invoicedraftstatus")
    op.execute("CREATE TYPE invoicedraftstatus AS ENUM ('draft', 'confirmed')")
    op.execute("ALTER TABLE invoice_drafts ALTER COLUMN status TYPE invoicedraftstatus USING status::invoicedraftstatus")
    op.execute("ALTER TABLE invoice_drafts ALTER COLUMN status SET DEFAULT 'draft'")


def downgrade() -> None:
    pass