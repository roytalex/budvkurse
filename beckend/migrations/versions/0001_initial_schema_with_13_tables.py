




from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table('cities',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('region', sa.String(length=120), nullable=False),
    sa.Column('country_code', sa.String(length=2), nullable=False),
    sa.Column('latitude', sa.Float(), nullable=False),
    sa.Column('longitude', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint('latitude BETWEEN -90 AND 90', name='check_cities_latitude'),
    sa.CheckConstraint('length(country_code) = 2', name='check_cities_country_code'),
    sa.CheckConstraint('longitude BETWEEN -180 AND 180', name='check_cities_longitude'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('topics',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('schools',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('city_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('address', sa.Text(), nullable=False),
    sa.Column('latitude', sa.Double(), nullable=True),
    sa.Column('longitude', sa.Double(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint('(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)', name='check_schools_coordinates_pair'),
    sa.CheckConstraint('latitude BETWEEN -90 AND 90', name='check_schools_latitude'),
    sa.CheckConstraint('longitude BETWEEN -180 AND 180', name='check_schools_longitude'),
    sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schools_city_id'), 'schools', ['city_id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('role', sa.String(length=20), server_default='student', nullable=False),
    sa.Column('grade', sa.Integer(), nullable=True),
    sa.Column('city_id', sa.Integer(), nullable=True),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("role IN ('student', 'organizer', 'admin')", name='check_users_role'),
    sa.CheckConstraint('grade BETWEEN 1 AND 11', name='check_users_grade'),
    sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uploaded_by', sa.Integer(), nullable=False),
    sa.Column('storage_key', sa.String(length=100), nullable=False),
    sa.Column('original_name', sa.String(length=255), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('storage_key')
    )
    op.create_index(op.f('ix_files_uploaded_by'), 'files', ['uploaded_by'], unique=False)
    op.create_table('sessions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('refresh_token_hash', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('refresh_token_hash')
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_table('user_interests',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'topic_id', name='uq_user_interests_user_topic')
    )
    op.create_index(op.f('ix_user_interests_topic_id'), 'user_interests', ['topic_id'], unique=False)
    op.create_index(op.f('ix_user_interests_user_id'), 'user_interests', ['user_id'], unique=False)
    op.create_table('events',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organizer_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('category', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('city_id', sa.Integer(), nullable=False),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('cover_file_id', sa.Integer(), nullable=True),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('timezone', sa.String(length=64), server_default='Europe/Moscow', nullable=False),
    sa.Column('registration_deadline', sa.DateTime(timezone=True), nullable=True),
    sa.Column('format', sa.String(length=10), nullable=False),
    sa.Column('place_name', sa.String(length=200), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('latitude', sa.Double(), nullable=True),
    sa.Column('longitude', sa.Double(), nullable=True),
    sa.Column('online_url', sa.Text(), nullable=True),
    sa.Column('min_grade', sa.Integer(), nullable=True),
    sa.Column('max_grade', sa.Integer(), nullable=True),
    sa.Column('min_age', sa.Integer(), nullable=True),
    sa.Column('max_age', sa.Integer(), nullable=True),
    sa.Column('price', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=True),
    sa.Column('registration_mode', sa.String(length=10), server_default='none', nullable=False),
    sa.Column('registration_url', sa.Text(), nullable=True),
    sa.Column('take_with_you', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("category IN ('city', 'school', 'olympiad', 'project')", name='check_events_category'),
    sa.CheckConstraint("format IN ('offline', 'online')", name='check_events_format'),
    sa.CheckConstraint("registration_mode IN ('internal', 'external', 'none')", name='check_events_registration_mode'),
    sa.CheckConstraint("status IN ('draft', 'pending', 'published', 'rejected', 'cancelled')", name='check_events_status'),
    sa.CheckConstraint('(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)', name='check_events_coordinates_pair'),
    sa.CheckConstraint('capacity > 0', name='check_events_capacity'),
    sa.CheckConstraint('ends_at > starts_at', name='check_events_dates'),
    sa.CheckConstraint('latitude BETWEEN -90 AND 90', name='check_events_latitude'),
    sa.CheckConstraint('longitude BETWEEN -180 AND 180', name='check_events_longitude'),
    sa.CheckConstraint('max_age >= 0', name='check_events_max_age'),
    sa.CheckConstraint('max_grade BETWEEN 1 AND 11', name='check_events_max_grade'),
    sa.CheckConstraint('min_age <= max_age', name='check_events_ages'),
    sa.CheckConstraint('min_age >= 0', name='check_events_min_age'),
    sa.CheckConstraint('min_grade <= max_grade', name='check_events_grades'),
    sa.CheckConstraint('min_grade BETWEEN 1 AND 11', name='check_events_min_grade'),
    sa.CheckConstraint('price >= 0', name='check_events_price'),
    sa.CheckConstraint('registration_deadline <= starts_at', name='check_events_registration_deadline'),
    sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['cover_file_id'], ['files.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_city_id'), 'events', ['city_id'], unique=False)
    op.create_index(op.f('ix_events_cover_file_id'), 'events', ['cover_file_id'], unique=False)
    op.create_index(op.f('ix_events_ends_at'), 'events', ['ends_at'], unique=False)
    op.create_index(op.f('ix_events_organizer_id'), 'events', ['organizer_id'], unique=False)
    op.create_index(op.f('ix_events_school_id'), 'events', ['school_id'], unique=False)
    op.create_index(op.f('ix_events_starts_at'), 'events', ['starts_at'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)
    op.create_table('event_moderation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('reviewer_id', sa.Integer(), nullable=False),
    sa.Column('decision', sa.String(length=20), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("decision IN ('approved', 'rejected')", name='check_moderation_decision'),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_moderation_event_id'), 'event_moderation', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_moderation_reviewer_id'), 'event_moderation', ['reviewer_id'], unique=False)
    op.create_table('event_topics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id', 'topic_id', name='uq_event_topics_pair')
    )
    op.create_index(op.f('ix_event_topics_event_id'), 'event_topics', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_topics_topic_id'), 'event_topics', ['topic_id'], unique=False)
    op.create_table('favorites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'event_id', name='uq_favorites_pair')
    )
    op.create_index(op.f('ix_favorites_event_id'), 'favorites', ['event_id'], unique=False)
    op.create_index(op.f('ix_favorites_user_id'), 'favorites', ['user_id'], unique=False)
    op.create_table('plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('reminder_minutes_before', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint('reminder_minutes_before BETWEEN 0 AND 10080', name='check_plan_reminder'),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'event_id', name='uq_plans_pair')
    )
    op.create_index(op.f('ix_plans_event_id'), 'plans', ['event_id'], unique=False)
    op.create_index(op.f('ix_plans_user_id'), 'plans', ['user_id'], unique=False)
    op.create_table('registrations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='registered', nullable=False),
    sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('registered', 'cancelled')", name='check_registration_status'),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'event_id', name='uq_registrations_pair')
    )
    op.create_index(op.f('ix_registrations_event_id'), 'registrations', ['event_id'], unique=False)
    op.create_index(op.f('ix_registrations_user_id'), 'registrations', ['user_id'], unique=False)



def downgrade():

    op.drop_index(op.f('ix_registrations_user_id'), table_name='registrations')
    op.drop_index(op.f('ix_registrations_event_id'), table_name='registrations')
    op.drop_table('registrations')
    op.drop_index(op.f('ix_plans_user_id'), table_name='plans')
    op.drop_index(op.f('ix_plans_event_id'), table_name='plans')
    op.drop_table('plans')
    op.drop_index(op.f('ix_favorites_user_id'), table_name='favorites')
    op.drop_index(op.f('ix_favorites_event_id'), table_name='favorites')
    op.drop_table('favorites')
    op.drop_index(op.f('ix_event_topics_topic_id'), table_name='event_topics')
    op.drop_index(op.f('ix_event_topics_event_id'), table_name='event_topics')
    op.drop_table('event_topics')
    op.drop_index(op.f('ix_event_moderation_reviewer_id'), table_name='event_moderation')
    op.drop_index(op.f('ix_event_moderation_event_id'), table_name='event_moderation')
    op.drop_table('event_moderation')
    op.drop_index(op.f('ix_events_status'), table_name='events')
    op.drop_index(op.f('ix_events_starts_at'), table_name='events')
    op.drop_index(op.f('ix_events_school_id'), table_name='events')
    op.drop_index(op.f('ix_events_organizer_id'), table_name='events')
    op.drop_index(op.f('ix_events_ends_at'), table_name='events')
    op.drop_index(op.f('ix_events_cover_file_id'), table_name='events')
    op.drop_index(op.f('ix_events_city_id'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_user_interests_user_id'), table_name='user_interests')
    op.drop_index(op.f('ix_user_interests_topic_id'), table_name='user_interests')
    op.drop_table('user_interests')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_files_uploaded_by'), table_name='files')
    op.drop_table('files')
    op.drop_table('users')
    op.drop_index(op.f('ix_schools_city_id'), table_name='schools')
    op.drop_table('schools')
    op.drop_table('topics')
    op.drop_table('cities')


