"""empty message

Revision ID: 9f6e0a0470f6
Revises: 
Create Date: 2023-11-25 23:31:13.122820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f6e0a0470f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('first_name', sa.String(length=100), nullable=True),
    sa.Column('last_name', sa.String(length=100), nullable=True),
    sa.Column('last_period_date', sa.Date(), nullable=True),
    sa.Column('average_period_length', sa.Integer(), nullable=True),
    sa.Column('average_cycle_length', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('cycle_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('is_predicted', sa.Boolean(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('cycle_data', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cycle_data_end_date'), ['end_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_cycle_data_start_date'), ['start_date'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cycle_data', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_cycle_data_start_date'))
        batch_op.drop_index(batch_op.f('ix_cycle_data_end_date'))

    op.drop_table('cycle_data')
    op.drop_table('user')
    # ### end Alembic commands ###
