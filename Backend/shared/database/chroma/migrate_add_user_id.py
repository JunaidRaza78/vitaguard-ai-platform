"""
Migration: Add user_id to existing ChromaDB documents
WARNING: This assigns all existing documents to a default user (admin).
For production, you should manually reassign documents to correct users.
"""

import chromadb
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the correct ChromaDB path
BACKEND_DIR = Path(__file__).parent.parent.parent.parent
CHROMA_DATA_PATH = BACKEND_DIR / "shared" / "database" / "chroma" / "chroma_data"


def migrate_add_user_id(default_user_id: str = "admin"):
    """
    Add user_id to all existing ChromaDB documents.

    Args:
        default_user_id: User ID to assign to existing documents (default: "admin")
    """
    print("\n" + "="*60)
    print("MIGRATION: Adding user_id to existing documents")
    print("="*60)
    print(f"ChromaDB path: {CHROMA_DATA_PATH}")
    print(f"Default user_id: {default_user_id}")

    # Connect to ChromaDB
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DATA_PATH))
        print("✅ Connected to ChromaDB")
    except Exception as e:
        print(f"❌ Failed to connect to ChromaDB: {e}")
        return

    # Get collection
    try:
        collection = client.get_collection("medical_docs")
        total_docs = collection.count()
        print(f"\n✅ Found collection 'medical_docs' with {total_docs} documents")
    except Exception as e:
        print(f"❌ Collection not found or error: {e}")
        return

    if total_docs == 0:
        print("\n⚠️  No documents in collection - nothing to migrate")
        return

    # Get all documents
    print("\nFetching all documents...")
    results = collection.get(include=["metadatas"])

    updated = 0
    skipped = 0
    errors = 0

    print(f"\nProcessing {len(results['ids'])} documents...")

    # Process each document
    for idx, (doc_id, metadata) in enumerate(zip(results["ids"], results["metadatas"]), 1):
        try:
            # Skip if already has user_id
            if "user_id" in metadata and metadata["user_id"]:
                skipped += 1
                if idx % 100 == 0:
                    print(f"  Progress: {idx}/{total_docs} (Updated: {updated}, Skipped: {skipped})")
                continue

            # Add user_id to metadata
            metadata["user_id"] = default_user_id
            if "document_id" not in metadata:
                metadata["document_id"] = f"legacy_{doc_id[:8]}"  # Generate document_id

            # Update in ChromaDB
            collection.update(
                ids=[doc_id],
                metadatas=[metadata]
            )

            updated += 1

            if idx % 100 == 0:
                print(f"  Progress: {idx}/{total_docs} (Updated: {updated}, Skipped: {skipped})")

        except Exception as e:
            errors += 1
            logger.error(f"Error updating document {doc_id}: {e}")

    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE!")
    print("="*60)
    print(f"  Updated:  {updated}")
    print(f"  Skipped:  {skipped}")
    print(f"  Errors:   {errors}")
    print(f"  Total:    {total_docs}")
    print("="*60)

    # Verify migration
    print("\nVerifying migration...")
    results_after = collection.get(include=["metadatas"], limit=10)

    user_id_count = sum(1 for meta in results_after["metadatas"] if "user_id" in meta)
    print(f"✅ Sample check: {user_id_count}/10 documents have user_id")

    if user_id_count == 0:
        print("⚠️  WARNING: Migration may have failed - no user_id found in sample")


def verify_migration():
    """Verify that all documents have user_id."""
    print("\n" + "="*60)
    print("VERIFICATION: Checking user_id presence")
    print("="*60)

    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DATA_PATH))
        collection = client.get_collection("medical_docs")

        # Sample 100 documents
        results = collection.get(include=["metadatas"], limit=100)

        with_user_id = 0
        without_user_id = 0

        for metadata in results["metadatas"]:
            if "user_id" in metadata and metadata["user_id"]:
                with_user_id += 1
            else:
                without_user_id += 1

        print(f"\nSample of 100 documents:")
        print(f"  ✅ With user_id:    {with_user_id}")
        print(f"  ❌ Without user_id: {without_user_id}")

        if without_user_id > 0:
            print("\n⚠️  WARNING: Some documents are missing user_id. Run migration again.")
        else:
            print("\n✅ All sampled documents have user_id!")

    except Exception as e:
        print(f"❌ Verification failed: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ChromaDB Migration Tool - Add user_id")
    print("="*60)

    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "verify":
            verify_migration()
        else:
            print(f"Unknown action: {action}")
            print("Usage: python migrate_add_user_id.py [verify]")
    else:
        # Default action: migrate
        print("\n⚠️  IMPORTANT: This will assign ALL existing documents to 'admin' user")
        print("   If you have multiple users, you should manually reassign documents after migration.\n")

        response = input("Continue with migration? (yes/no): ").strip().lower()

        if response == "yes":
            # Get default user ID
            default_user = input("Enter default user_id for existing documents (default: admin): ").strip()
            if not default_user:
                default_user = "admin"

            migrate_add_user_id(default_user_id=default_user)

            # Verify
            print("\nRunning verification...")
            verify_migration()
        else:
            print("\nMigration cancelled.")
