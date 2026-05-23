"""Migracion Inicial

Revision ID: e1785d8860ce
Revises:
Create Date: 2026-05-07 22:06:29.498313

Nota: Esta migración es un placeholder vacío que sirve como punto de origen
de la cadena de migraciones. La base de datos de producción (ekidb) tiene
este revision ID registrado en alembic_version. La migración real del esquema
completo es e1b0a75cd65e, que tiene down_revision apuntando a este archivo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1785d8860ce'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Migración placeholder — no realiza ninguna operación.
    # La base de datos de producción tiene este revision ID como punto de partida.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
