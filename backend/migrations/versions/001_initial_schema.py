# migrations/versions/001_initial_schema.py

"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2026-08-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='user', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False, unique=True),
        sa.Column('machine_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), server_default='OFFLINE', nullable=False),
        sa.Column('version', sa.String(50), server_default='1.0.0', nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create simulation_jobs table
    op.create_table(
        'simulation_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_id', sa.String(50), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), server_default='QUEUED', nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create simulation_parameters table
    op.create_table(
        'simulation_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parameter_name', sa.String(100), nullable=False),
        sa.Column('parameter_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['simulation_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create simulation_results table
    op.create_table(
        'simulation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('result_type', sa.String(50), nullable=False),
        sa.Column('result_url', sa.Text(), nullable=True),
        sa.Column('storage_key', sa.String(255), nullable=True),
        sa.Column('crs', sa.String(50), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['simulation_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['simulation_jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index('idx_simulation_jobs_job_id', 'simulation_jobs', ['job_id'])
    op.create_index('idx_simulation_jobs_user_id', 'simulation_jobs', ['user_id'])
    op.create_index('idx_simulation_jobs_status', 'simulation_jobs', ['status'])
    op.create_index('idx_simulation_jobs_created_at', 'simulation_jobs', ['created_at'])
    op.create_index('idx_simulation_parameters_job_id', 'simulation_parameters', ['job_id'])
    op.create_index('idx_simulation_results_job_id', 'simulation_results', ['job_id'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_agents_status', 'agents', ['status'])
    
    # Create function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    
    # Create triggers
    op.execute("""
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    
    op.execute("""
        CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users')
    op.execute('DROP TRIGGER IF EXISTS update_agents_updated_at ON agents')
    
    # Drop function
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop indexes
    op.drop_index('idx_agents_status')
    op.drop_index('idx_audit_logs_created_at')
    op.drop_index('idx_audit_logs_user_id')
    op.drop_index('idx_simulation_results_job_id')
    op.drop_index('idx_simulation_parameters_job_id')
    op.drop_index('idx_simulation_jobs_created_at')
    op.drop_index('idx_simulation_jobs_status')
    op.drop_index('idx_simulation_jobs_user_id')
    op.drop_index('idx_simulation_jobs_job_id')
    
    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('simulation_results')
    op.drop_table('simulation_parameters')
    op.drop_table('simulation_jobs')
    op.drop_table('agents')
    op.drop_table('users')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')