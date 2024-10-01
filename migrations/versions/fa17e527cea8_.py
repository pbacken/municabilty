"""empty message

Revision ID: fa17e527cea8
Revises: 5b3544b5f5b1
Create Date: 2024-09-29 12:40:14.610536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa17e527cea8'
down_revision = '5b3544b5f5b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('prompt_info', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prompt_file', sa.String(length=64), nullable=False))
        batch_op.add_column(sa.Column('meeting_id', sa.String(length=64), nullable=False))
        batch_op.drop_index('ix_prompt_info_prompt_name')
        batch_op.create_index(batch_op.f('ix_prompt_info_meeting_id'), ['meeting_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_prompt_info_prompt_file'), ['prompt_file'], unique=False)
        batch_op.drop_column('prompt_name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('prompt_info', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prompt_name', sa.VARCHAR(length=64), nullable=False))
        batch_op.drop_index(batch_op.f('ix_prompt_info_prompt_file'))
        batch_op.drop_index(batch_op.f('ix_prompt_info_meeting_id'))
        batch_op.create_index('ix_prompt_info_prompt_name', ['prompt_name'], unique=False)
        batch_op.drop_column('meeting_id')
        batch_op.drop_column('prompt_file')

    # ### end Alembic commands ###
