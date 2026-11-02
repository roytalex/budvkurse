from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('max_contact_url', sa.String(240), nullable=True))
    op.create_table('max_connections',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('max_user_id', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    for column in (
        sa.Column('max_delivery_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_delivery_minutes', sa.Integer(), nullable=True),
        sa.Column('max_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='0'),
    ):
        op.add_column('plans', column)


def downgrade():
    for name in ('max_attempts', 'max_retry_at', 'max_sent_at', 'max_delivery_minutes', 'max_delivery_for'):
        op.drop_column('plans', name)
    op.drop_table('max_connections')
    op.drop_column('users', 'max_contact_url')
