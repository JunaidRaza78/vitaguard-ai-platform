#!/usr/bin/env python3
"""
Database Migration Runner
Applies SQL migration files to PostgreSQL database
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Database migration runner"""

    def __init__(self, database_url: str):
        """
        Initialize migration runner.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent

    async def create_migrations_table(self, conn: asyncpg.Connection) -> None:
        """
        Create migrations tracking table.

        Args:
            conn: Database connection
        """
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id SERIAL PRIMARY KEY,
                version VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                checksum VARCHAR(64),
                success BOOLEAN DEFAULT TRUE
            )
        """)
        logger.info("Migrations table ready")

    async def get_applied_migrations(self, conn: asyncpg.Connection) -> set:
        """
        Get list of applied migrations.

        Args:
            conn: Database connection

        Returns:
            Set of applied migration versions
        """
        rows = await conn.fetch(
            "SELECT version FROM schema_migrations WHERE success = TRUE"
        )
        return {row['version'] for row in rows}

    async def apply_migration(
        self,
        conn: asyncpg.Connection,
        migration_file: Path
    ) -> bool:
        """
        Apply a single migration file.

        Args:
            conn: Database connection
            migration_file: Path to migration SQL file

        Returns:
            True if successful
        """
        version = migration_file.stem.split('_')[0]
        name = migration_file.stem

        logger.info(f"Applying migration: {name}")

        try:
            # Read migration SQL
            sql = migration_file.read_text()

            # Execute in a transaction
            async with conn.transaction():
                await conn.execute(sql)

                # Record migration
                await conn.execute("""
                    INSERT INTO schema_migrations (version, name, success)
                    VALUES ($1, $2, TRUE)
                    ON CONFLICT (version) DO UPDATE
                    SET applied_at = CURRENT_TIMESTAMP, success = TRUE
                """, version, name)

            logger.info(f"✓ Migration {name} applied successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Migration {name} failed: {e}")

            # Record failed migration
            try:
                await conn.execute("""
                    INSERT INTO schema_migrations (version, name, success)
                    VALUES ($1, $2, FALSE)
                    ON CONFLICT (version) DO UPDATE
                    SET applied_at = CURRENT_TIMESTAMP, success = FALSE
                """, version, name)
            except:
                pass

            return False

    async def rollback_migration(
        self,
        conn: asyncpg.Connection,
        migration_file: Path
    ) -> bool:
        """
        Rollback a single migration.

        Args:
            conn: Database connection
            migration_file: Path to migration rollback SQL file

        Returns:
            True if successful
        """
        version = migration_file.stem.split('_')[0]
        name = migration_file.stem.replace('_rollback', '')

        logger.info(f"Rolling back migration: {name}")

        try:
            # Read rollback SQL
            sql = migration_file.read_text()

            # Execute in a transaction
            async with conn.transaction():
                await conn.execute(sql)

                # Remove migration record
                await conn.execute(
                    "DELETE FROM schema_migrations WHERE version = $1",
                    version
                )

            logger.info(f"✓ Migration {name} rolled back successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Rollback {name} failed: {e}")
            return False

    async def migrate_up(self, target_version: Optional[str] = None) -> None:
        """
        Apply pending migrations.

        Args:
            target_version: Optional version to migrate up to
        """
        logger.info("Starting database migration...")

        conn = await asyncpg.connect(self.database_url)

        try:
            # Create migrations table
            await self.create_migrations_table(conn)

            # Get applied migrations
            applied = await self.get_applied_migrations(conn)

            # Find migration files
            migration_files = sorted([
                f for f in self.migrations_dir.glob('*.sql')
                if not f.name.endswith('_rollback.sql')
            ])

            if not migration_files:
                logger.info("No migration files found")
                return

            # Apply migrations
            applied_count = 0
            for migration_file in migration_files:
                version = migration_file.stem.split('_')[0]

                # Skip if already applied
                if version in applied:
                    logger.info(f"Skipping {migration_file.name} (already applied)")
                    continue

                # Stop if we've reached target version
                if target_version and version > target_version:
                    break

                # Apply migration
                success = await self.apply_migration(conn, migration_file)
                if success:
                    applied_count += 1
                else:
                    logger.error("Migration failed. Stopping.")
                    break

            if applied_count == 0:
                logger.info("Database is up to date")
            else:
                logger.info(f"✓ Applied {applied_count} migration(s)")

        finally:
            await conn.close()

    async def migrate_down(self, target_version: Optional[str] = None) -> None:
        """
        Rollback migrations.

        Args:
            target_version: Version to rollback to (exclusive)
        """
        logger.info("Starting database rollback...")

        conn = await asyncpg.connect(self.database_url)

        try:
            # Create migrations table
            await self.create_migrations_table(conn)

            # Get applied migrations
            applied = await self.get_applied_migrations(conn)

            if not applied:
                logger.info("No migrations to rollback")
                return

            # Find rollback files
            rollback_files = sorted([
                f for f in self.migrations_dir.glob('*_rollback.sql')
            ], reverse=True)

            # Rollback migrations
            rollback_count = 0
            for rollback_file in rollback_files:
                version = rollback_file.stem.split('_')[0]

                # Skip if not applied
                if version not in applied:
                    continue

                # Stop if we've reached target version
                if target_version and version <= target_version:
                    break

                # Rollback migration
                success = await self.rollback_migration(conn, rollback_file)
                if success:
                    rollback_count += 1
                else:
                    logger.error("Rollback failed. Stopping.")
                    break

            logger.info(f"✓ Rolled back {rollback_count} migration(s)")

        finally:
            await conn.close()

    async def migration_status(self) -> None:
        """Show migration status."""
        logger.info("Checking migration status...")

        conn = await asyncpg.connect(self.database_url)

        try:
            # Create migrations table
            await self.create_migrations_table(conn)

            # Get applied migrations
            rows = await conn.fetch("""
                SELECT version, name, applied_at, success
                FROM schema_migrations
                ORDER BY version
            """)

            # Find all migration files
            migration_files = sorted([
                f for f in self.migrations_dir.glob('*.sql')
                if not f.name.endswith('_rollback.sql')
            ])

            applied_versions = {row['version'] for row in rows}

            print("\n" + "=" * 80)
            print("MIGRATION STATUS")
            print("=" * 80)

            if rows:
                print("\nApplied Migrations:")
                for row in rows:
                    status = "✓" if row['success'] else "✗"
                    print(f"  {status} {row['version']} - {row['name']} (applied: {row['applied_at']})")
            else:
                print("\nNo migrations applied yet")

            print("\nPending Migrations:")
            pending = [
                f for f in migration_files
                if f.stem.split('_')[0] not in applied_versions
            ]

            if pending:
                for migration_file in pending:
                    print(f"  ○ {migration_file.stem}")
            else:
                print("  None - database is up to date")

            print("\n" + "=" * 80 + "\n")

        finally:
            await conn.close()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Database migration runner')
    parser.add_argument(
        'command',
        choices=['up', 'down', 'status'],
        help='Migration command (up=apply, down=rollback, status=show status)'
    )
    parser.add_argument(
        '--version',
        help='Target version (for up/down commands)'
    )
    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection URL',
        default=os.getenv('DATABASE_URL')
    )

    args = parser.parse_args()

    # Check database URL
    if not args.database_url:
        logger.error("Database URL not provided. Use --database-url or set DATABASE_URL environment variable")
        sys.exit(1)

    # Create runner
    runner = MigrationRunner(args.database_url)

    # Execute command
    try:
        if args.command == 'up':
            await runner.migrate_up(args.version)
        elif args.command == 'down':
            await runner.migrate_down(args.version)
        elif args.command == 'status':
            await runner.migration_status()

    except Exception as e:
        logger.error(f"Migration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
