"""invoices_status_to_varchar

Revision ID: cdcc7470f2f6
Revises: 28e977b39e8b
Create Date: 2026-05-12 16:36:33.338558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdcc7470f2f6'
down_revision: Union[str, None] = '28e977b39e8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # invoices
    op.execute("ALTER TABLE invoices ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE invoices ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    op.execute("DROP TYPE IF EXISTS invoicestatus CASCADE")
    op.execute("ALTER TABLE invoices ALTER COLUMN status SET DEFAULT 'draft'")

    # invoice_drafts
    op.execute("ALTER TABLE invoice_drafts ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE invoice_drafts ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    op.execute("DROP TYPE IF EXISTS invoicedraftstatus CASCADE")
    op.execute("ALTER TABLE invoice_drafts ALTER COLUMN status SET DEFAULT 'draft'")

    # transactions — заодно фиксим
    op.execute("ALTER TABLE transactions ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE transactions ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    op.execute("DROP TYPE IF EXISTS transactionstatus CASCADE")
    op.execute("ALTER TABLE transactions ALTER COLUMN status SET DEFAULT 'new'")

    op.execute("ALTER TABLE transactions ALTER COLUMN transaction_type TYPE VARCHAR(50) USING transaction_type::text")
    op.execute("DROP TYPE IF EXISTS transactiontype CASCADE")


def downgrade() -> None:
    pass
