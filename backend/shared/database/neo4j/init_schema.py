"""
Initialize Neo4j schema (indexes and constraints).
Run this script once to set up the database schema.
"""
import sys
from pathlib import Path

# Add Backend directory to path for imports (works in Docker and locally)
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from shared.database.neo4j import Neo4jClient


def init_schema():
    """Initialize Neo4j schema from schema.cypher file."""
    client = Neo4jClient()
    
    # Read schema file
    schema_file = Path(__file__).parent / "schema.cypher"
    
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    print("=" * 60)
    print("Initializing Neo4j Schema...")
    print("=" * 60)
    
    try:
        with open(schema_file, 'r') as f:
            schema_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in schema_content.split(';') if s.strip()]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            try:
                # Skip comments
                if statement.startswith('--'):
                    continue
                
                print(f"\n[{i}/{len(statements)}] Executing: {statement[:50]}...")
                result = client.execute_query(statement)
                
                # Consume the result
                list(result)
                success_count += 1
                print(f"✅ Success")
                
            except Exception as e:
                error_count += 1
                # Some errors are expected (e.g., constraint/index already exists)
                if "already exists" in str(e).lower() or "already exist" in str(e).lower():
                    print(f"⚠️  Already exists (skipping)")
                else:
                    print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print(f"Schema Initialization Complete!")
        print(f"✅ Successful: {success_count}")
        print(f"⚠️  Skipped/Errors: {error_count}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing schema: {e}")
        return False


if __name__ == "__main__":
    success = init_schema()
    sys.exit(0 if success else 1)

