from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE users SET grade = NULL, school_id = NULL WHERE role = 'organizer'")
    op.create_check_constraint('check_organizer_no_school', 'users', "role != 'organizer' OR (grade IS NULL AND school_id IS NULL)")


def downgrade():
    op.drop_constraint('check_organizer_no_school', 'users', type_='check')
