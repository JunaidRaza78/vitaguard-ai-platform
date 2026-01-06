"""
Initialize PostgreSQL database schema.
This script reads schema.sql and applies it to the database.
"""
import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

def init_database():
    """Initialize database schema from schema.sql file."""
    # Get database connection parameters
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "family_health_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    
    # Get schema.sql path
    schema_file = Path(__file__).parent / "schema.sql"
    
    if not schema_file.exists():
        print(f"Error: schema.sql not found at {schema_file}")
        sys.exit(1)
    
    try:
        # Connect to database
        print(f"Connecting to database: {db_name} on {db_host}:{db_port} as {db_user}...")
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        conn.autocommit = False
        
        cursor = conn.cursor()
        
        # Read and execute schema.sql
        print(f"Reading schema from {schema_file}...")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        print("Executing schema SQL...")
        cursor.execute(schema_sql)
        
        # Commit transaction
        conn.commit()
        print("✓ Database schema initialized successfully!")
        
        # Verify new tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('chat_conversations', 'chat_messages')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        if tables:
            print("\n✓ New chat tables created:")
            for table in tables:
                print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database()

