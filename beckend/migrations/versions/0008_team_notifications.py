from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('team_members', sa.Column('captain_notice_pending', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('team_members', sa.Column('captain_notice_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('team_members', sa.Column('captain_notice_retry_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('team_members', sa.Column('captain_notice_attempts', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    for name in ('captain_notice_attempts', 'captain_notice_retry_at', 'captain_notice_sent_at', 'captain_notice_pending'):
        op.drop_column('team_members', name)
