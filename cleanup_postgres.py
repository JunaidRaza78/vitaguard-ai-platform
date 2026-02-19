#!/usr/bin/env python3
"""
Clean up PostgreSQL connections
"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from sqlalchemy import create_engine, text
import os

def cleanup_connections():
    """Kill idle connections and show connection stats."""

    # Create a direct connection to postgres database (not family_health_db)
    db_user = os.getenv("DB_USER", os.getenv("USER", "postgres"))
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    target_db = os.getenv("DB_NAME", "family_health_db")

    admin_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"

    try:
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

        with engine.connect() as conn:
            # Check current connections
            result = conn.execute(text("""
                SELECT count(*) as total,
                       sum(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle,
                       sum(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active
                FROM pg_stat_activity
                WHERE datname = :dbname
            """), {"dbname": target_db})

            stats = result.fetchone()
            print(f"Current connections to {target_db}:")
            print(f"  Total: {stats[0]}")
            print(f"  Idle: {stats[1]}")
            print(f"  Active: {stats[2]}")

            # Kill idle connections
            if stats[1] > 0:
                print(f"\n⚠️  Terminating {stats[1]} idle connections...")
                result = conn.execute(text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :dbname
                      AND state = 'idle'
                      AND pid <> pg_backend_pid()
                """), {"dbname": target_db})

                terminated = result.rowcount
                print(f"✅ Terminated {terminated} idle connections")
            else:
                print("\n✅ No idle connections to clean up")

            # Check again
            result = conn.execute(text("""
                SELECT count(*)
                FROM pg_stat_activity
                WHERE datname = :dbname
            """), {"dbname": target_db})

            remaining = result.scalar()
            print(f"\nRemaining connections: {remaining}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nIf you see 'password authentication failed', you may need to:")
        print("1. Set DB_PASSWORD environment variable")
        print("2. Or run: export DB_PASSWORD=your_password")

if __name__ == "__main__":
    cleanup_connections()