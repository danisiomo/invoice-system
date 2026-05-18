"""invoice number sequence

Revision ID: 870159ceb8f3
Revises: cdcc7470f2f6
Create Date: 2026-05-17 21:57:16.546043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '870159ceb8f3'
down_revision: Union[str, None] = 'cdcc7470f2f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #Создаём sequence для номера СФ
    op.execute("CREATE SEQUENCE IF NOT EXISTS invoice_number_seq START 1;")
    #Поднимаем sequence до максимального номера, который уже есть в invoices
    #Берём хвост цифр из строки number вида 'СФ-2026-0005'
    #Если в таблице нет записей — выставится 0, следующий будет 1
    op.execute(
        """
        SELECT setval(
            'invoice_number_seq',
            COALESCE(
                (SELECT MAX((substring(number from '(\\d+)$'))::bigint) FROM invoices),
                0
            ),
            true
        );
        """
    )


def downgrade() -> None:
    pass
