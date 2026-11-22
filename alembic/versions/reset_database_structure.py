"""reset database structure

Revision ID: reset_db_2025
Revises: 6fab867e1971
Create Date: 2026-01-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = 'reset_db_2025'
down_revision: Union[str, Sequence[str], None] = '6fab867e1971'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Reset all tables to match current models."""
    
    # Enable PostGIS extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    
    # Drop existing tables if they exist (in correct order to handle foreign keys)
    op.execute('DROP TABLE IF EXISTS rescue_request_disaster_types CASCADE;')
    op.execute('DROP TABLE IF EXISTS rescue_request_needs CASCADE;')
    op.execute('DROP TABLE IF EXISTS rescue_request CASCADE;')
    op.execute('DROP TABLE IF EXISTS disaster_type CASCADE;')
    op.execute('DROP TABLE IF EXISTS needs CASCADE;')
    op.execute('DROP TABLE IF EXISTS region CASCADE;')
    
    # Create region table
    op.create_table(
        'region',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['region.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_region_id'), 'region', ['id'], unique=False)
    
    # Create disaster_type table
    op.create_table(
        'disaster_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disaster_type_id'), 'disaster_type', ['id'], unique=False)
    
    # Create needs table
    op.create_table(
        'needs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_needs_id'), 'needs', ['id'], unique=False)
    
    # Create rescue_request table
    op.create_table(
        'rescue_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('coordinate', geoalchemy2.types.Geometry(
            geometry_type='POINT', 
            srid=4326,
            dimension=2,
            from_text='ST_GeomFromEWKT',
            name='geometry'
        ), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('map_link', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('posted_time', sa.String(), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=True),
        sa.Column('image', sa.String(), nullable=True),
        sa.Column('urgency_score', sa.Float(), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True),
        sa.Column('contact', sa.String(), nullable=True),
        sa.Column('region_id', sa.Integer(), nullable=True),
        sa.Column('affected_people', sa.Integer(), nullable=True),
        sa.Column('infrastructure_damage', sa.Boolean(), nullable=True),
        sa.Column('is_isolated', sa.Boolean(), nullable=True),
        sa.Column('deathly', sa.Boolean(), nullable=True),
        sa.Column('has_emergency', sa.Boolean(), nullable=True),
        sa.Column('has_emotion', sa.Boolean(), nullable=True),
        sa.Column('has_emphasis', sa.Boolean(), nullable=True),
        sa.Column('reactions', sa.Integer(), nullable=True),
        sa.Column('replies', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['region_id'], ['region.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rescue_request_id'), 'rescue_request', ['id'], unique=False)
    # Create GIST index for coordinate geometry if not exists
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_rescue_request_coordinate 
        ON rescue_request USING gist (coordinate);
    """)
    
    # Create rescue_request_needs association table
    op.create_table(
        'rescue_request_needs',
        sa.Column('rescue_request_id', sa.Integer(), nullable=False),
        sa.Column('needs_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['needs_id'], ['needs.id'], ),
        sa.ForeignKeyConstraint(['rescue_request_id'], ['rescue_request.id'], ),
        sa.PrimaryKeyConstraint('rescue_request_id', 'needs_id')
    )
    
    # Create rescue_request_disaster_types association table
    op.create_table(
        'rescue_request_disaster_types',
        sa.Column('rescue_request_id', sa.Integer(), nullable=False),
        sa.Column('disaster_type_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['disaster_type_id'], ['disaster_type.id'], ),
        sa.ForeignKeyConstraint(['rescue_request_id'], ['rescue_request.id'], ),
        sa.PrimaryKeyConstraint('rescue_request_id', 'disaster_type_id')
    )


def downgrade() -> None:
    """Downgrade schema - Drop all tables."""
    op.drop_table('rescue_request_disaster_types')
    op.drop_table('rescue_request_needs')
    op.drop_index('idx_rescue_request_coordinate', table_name='rescue_request')
    op.drop_index(op.f('ix_rescue_request_id'), table_name='rescue_request')
    op.drop_table('rescue_request')
    op.drop_index(op.f('ix_needs_id'), table_name='needs')
    op.drop_table('needs')
    op.drop_index(op.f('ix_disaster_type_id'), table_name='disaster_type')
    op.drop_table('disaster_type')
    op.drop_index(op.f('ix_region_id'), table_name='region')
    op.drop_table('region')
