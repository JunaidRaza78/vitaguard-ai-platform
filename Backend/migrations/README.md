# Database Migrations

This directory contains SQL migration files for the Family Health Manager application database.

## Overview

Migrations are version-controlled SQL scripts that create, modify, or delete database schema objects (tables, indexes, functions, etc.). Each migration is numbered sequentially and should be applied in order.

## Migration Files

### Current Migrations

1. **001_create_auth_tables.sql** - Creates authentication system tables
   - users
   - refresh_tokens
   - login_attempts
   - sessions
   - email_verification_tokens
   - password_reset_tokens

### Rollback Files

Each migration has a corresponding rollback file:
- **001_create_auth_tables_rollback.sql** - Drops authentication tables

## Running Migrations

### Prerequisites

Install required Python packages:
```bash
pip install asyncpg
```

Set your database connection:
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

### Using the Migration Runner

The migration runner (`run_migrations.py`) provides commands to manage database migrations.

#### Check Migration Status

```bash
python run_migrations.py status
```

This shows which migrations have been applied and which are pending.

#### Apply Migrations (Migrate Up)

Apply all pending migrations:
```bash
python run_migrations.py up
```

Apply migrations up to a specific version:
```bash
python run_migrations.py up --version 001
```

#### Rollback Migrations (Migrate Down)

Rollback the most recent migration:
```bash
python run_migrations.py down
```

Rollback to a specific version:
```bash
python run_migrations.py down --version 001
```

#### Using Custom Database URL

```bash
python run_migrations.py up --database-url "postgresql://user:pass@localhost:5432/mydb"
```

### Using psql (Manual)

You can also apply migrations manually using psql:

```bash
# Apply migration
psql -U username -d database -f 001_create_auth_tables.sql

# Rollback migration
psql -U username -d database -f 001_create_auth_tables_rollback.sql
```

## Migration Tracking

The migration runner creates a `schema_migrations` table to track applied migrations:

```sql
CREATE TABLE schema_migrations (
    migration_id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    checksum VARCHAR(64),
    success BOOLEAN DEFAULT TRUE
);
```

## Creating New Migrations

### Naming Convention

Migrations should follow this naming pattern:
```
{version}_{description}.sql
{version}_{description}_rollback.sql
```

Example:
```
002_add_user_preferences.sql
002_add_user_preferences_rollback.sql
```

### Migration Template

```sql
-- ==========================================
-- Description: [What this migration does]
-- Version: [Version number]
-- ==========================================

-- Your SQL statements here

-- Always include rollback instructions in comments
-- ROLLBACK: [How to undo this migration]
```

### Best Practices

1. **Idempotent Migrations**: Use `IF EXISTS` and `IF NOT EXISTS` clauses
   ```sql
   CREATE TABLE IF NOT EXISTS users (...);
   DROP TABLE IF EXISTS temp_table;
   ```

2. **Transactions**: Wrap statements in transactions when possible
   ```sql
   BEGIN;
   -- Your changes
   COMMIT;
   ```

3. **Indexes**: Create indexes for foreign keys and frequently queried columns
   ```sql
   CREATE INDEX idx_users_email ON users(email);
   ```

4. **Constraints**: Add constraints to ensure data integrity
   ```sql
   CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
   ```

5. **Comments**: Document tables and columns
   ```sql
   COMMENT ON TABLE users IS 'User accounts and profiles';
   COMMENT ON COLUMN users.password_hash IS 'bcrypt hashed password (12 rounds)';
   ```

6. **Rollback**: Always create a rollback file for every migration

## Database Schema

### Authentication Tables

#### users
Main user account table with authentication and profile data.

Key columns:
- `user_id` (UUID) - Primary key
- `email` (VARCHAR) - Unique email address
- `username` (VARCHAR) - Unique username
- `password_hash` (VARCHAR) - bcrypt hashed password
- `is_active`, `is_verified`, `is_superuser` (BOOLEAN) - Status flags
- `failed_login_attempts` (INTEGER) - Failed login counter
- `account_locked_until` (TIMESTAMP) - Account lockout timestamp

#### refresh_tokens
JWT refresh tokens for extended authentication.

Key columns:
- `token_id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `token_hash` (VARCHAR) - SHA-256 hash of refresh token
- `expires_at` (TIMESTAMP) - Token expiration
- `revoked` (BOOLEAN) - Revocation status

#### sessions
Active user sessions linked to access tokens.

Key columns:
- `session_id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `access_token` (TEXT) - JWT access token
- `is_active` (BOOLEAN) - Session status
- `expires_at` (TIMESTAMP) - Session expiration

#### login_attempts
Security audit log of all login attempts.

Key columns:
- `attempt_id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users (nullable)
- `success` (BOOLEAN) - Success/failure flag
- `ip_address` (VARCHAR) - Client IP address
- `attempted_at` (TIMESTAMP) - Attempt timestamp

### Maintenance Functions

#### cleanup_expired_tokens()
Periodic cleanup function to remove expired tokens and old records.

Run manually:
```sql
SELECT cleanup_expired_tokens();
```

Or set up a cron job to run daily:
```bash
0 2 * * * psql -U user -d db -c "SELECT cleanup_expired_tokens();"
```

## Initial Data

The migration creates a default admin user:
- **Email**: admin@example.com
- **Username**: admin
- **Password**: AdminPass123!

⚠️ **IMPORTANT**: Change this password immediately in production!

```sql
-- Update admin password
UPDATE users
SET password_hash = '[new_bcrypt_hash]'
WHERE email = 'admin@example.com';
```

## Troubleshooting

### Migration Fails

If a migration fails:

1. Check the error message in the output
2. The migration runner will record the failure in `schema_migrations`
3. Fix the issue in the migration file
4. Manually rollback if needed:
   ```bash
   python run_migrations.py down --version [failed_version]
   ```
5. Re-run the migration:
   ```bash
   python run_migrations.py up
   ```

### Inconsistent State

If migrations are in an inconsistent state:

1. Check status:
   ```bash
   python run_migrations.py status
   ```

2. Manually inspect the `schema_migrations` table:
   ```sql
   SELECT * FROM schema_migrations ORDER BY version;
   ```

3. If needed, manually update the migration record:
   ```sql
   DELETE FROM schema_migrations WHERE version = '001';
   ```

### Connection Issues

Check your database URL format:
```
postgresql://username:password@host:port/database
```

Test connection with psql:
```bash
psql "postgresql://username:password@host:port/database"
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Test migrations in staging environment
- [ ] Backup production database
- [ ] Review all SQL statements
- [ ] Verify rollback scripts work
- [ ] Plan downtime window (if needed)
- [ ] Coordinate with team

### Deployment Steps

1. **Backup Database**
   ```bash
   pg_dump -U user -d database > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Apply Migrations**
   ```bash
   python run_migrations.py up --database-url $PROD_DATABASE_URL
   ```

3. **Verify Success**
   ```bash
   python run_migrations.py status --database-url $PROD_DATABASE_URL
   ```

4. **Test Application**
   - Verify authentication works
   - Check all endpoints
   - Monitor logs

5. **Rollback Plan** (if issues occur)
   ```bash
   python run_migrations.py down --database-url $PROD_DATABASE_URL
   # Restore from backup if needed
   psql -U user -d database < backup_file.sql
   ```

## Security Considerations

1. **Never commit database URLs** with credentials to version control
2. **Use environment variables** for sensitive connection strings
3. **Restrict database user permissions** - only grant necessary privileges
4. **Audit migration changes** before applying to production
5. **Keep backups** of all production databases
6. **Change default passwords** immediately after deployment

## Azure PostgreSQL Notes

When using Azure PostgreSQL Flexible Server:

1. **Connection String Format**:
   ```
   postgresql://username:password@servername.postgres.database.azure.com:5432/database?sslmode=require
   ```

2. **Firewall Rules**: Ensure your IP is whitelisted
3. **SSL Required**: Azure PostgreSQL requires SSL connections
4. **Admin User**: Use the admin user created during provisioning

## Support

For issues or questions:
1. Check this README
2. Review migration error logs
3. Check PostgreSQL logs
4. Contact the development team
