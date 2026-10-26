
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('plans', sa.Column('reminder_read_for', sa.DateTime(timezone=True), nullable=True))
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('events.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_title', sa.String(150), nullable=False),
        sa.Column('participant_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organizer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('participant_read_id', sa.Integer(), server_default='0', nullable=False),
        sa.Column('organizer_read_id', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('event_id', 'participant_id', name='uq_conversation_event_participant'),
        sa.CheckConstraint('participant_id <> organizer_id', name='check_conversation_distinct_users'))
    for name in ('event_id', 'participant_id', 'organizer_id'):
        op.create_index('ix_conversations_'+name, 'conversations', [name])
    op.create_table('messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.String(36), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('conversation_id', 'sender_id', 'client_id', name='uq_message_client'))
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])


def downgrade():
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_column('plans', 'reminder_read_for')
