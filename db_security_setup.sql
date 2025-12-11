-- Database Security Setup
-- Creates separate users with minimal required permissions
-- Run this as the postgres superuser after initial database setup
--
-- IMPORTANT: Update passwords in .env.docker.example before running:
--   - DB_PANEL_PASSWORD for panel_readonly user
--   - DB_API_PASSWORD for api_user
--   - DB_MIGRATION_PASSWORD for migration_user

-- Create read-only user for Panel dashboard
-- Password from: DB_PANEL_PASSWORD in .env
CREATE USER panel_readonly WITH PASSWORD 'tTQ]y1.+K3YBDlL%j1-]';

-- Grant connection to database
GRANT CONNECT ON DATABASE beppp TO panel_readonly;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO panel_readonly;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO panel_readonly;

-- Grant SELECT on future tables (for migrations)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO panel_readonly;

-- Create limited user for API (read/write but not schema changes)
-- Password from: DB_API_PASSWORD in .env
CREATE USER api_user WITH PASSWORD '~x84,V9]3mZOSS~MR85a';

-- Grant connection to database
GRANT CONNECT ON DATABASE beppp TO api_user;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO api_user;

-- Grant read/write on all existing tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO api_user;

-- Grant usage on sequences (for auto-increment IDs)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_user;

-- Grant for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO api_user;

-- Create migration user (only for running Alembic migrations)
-- Password from: DB_MIGRATION_PASSWORD in .env
CREATE USER migration_user WITH PASSWORD 'I$>9@TIy91uPMk8,GGbJ';

-- Grant full schema manipulation rights
GRANT ALL PRIVILEGES ON DATABASE beppp TO migration_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO migration_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO migration_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO migration_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO migration_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO migration_user;

-- Revoke dangerous permissions from api_user (extra safety)
REVOKE CREATE ON SCHEMA public FROM api_user;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Show created users
\du

COMMENT ON ROLE panel_readonly IS 'Read-only access for Panel analytics dashboard';
COMMENT ON ROLE api_user IS 'Read/write access for FastAPI application';
COMMENT ON ROLE migration_user IS 'Full access for Alembic database migrations';
