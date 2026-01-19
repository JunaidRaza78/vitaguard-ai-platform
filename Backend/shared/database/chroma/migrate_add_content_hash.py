"""
Migration Script: Add content_hash to existing documents
- Read all documents without content_hash
- Generate hash from their content
- Update metadata with content_hash
"""

import chromadb
import hashlib
from pathlib import Path

def generate_content_hash(text):
    """Same logic as extract_text_with_specialty.py"""
    text = text.strip().lower()
    length = len(text)

    samples = []
    samples.append(text[:500])

    if length > 1000:
        mid = length // 2
        samples.append(text[mid:mid+500])

    if length > 1500:
        samples.append(text[-500:])

    combined = "".join(samples)
    hash_input = f"{combined}|{length}"
    return hashlib.md5(hash_input.encode()).hexdigest()


def migrate_content_hashes():
    print("\n" + "="*60)
    print("MIGRATION: Add content_hash to existing documents")
    print("="*60)

    client = chromadb.PersistentClient(path="./chroma_data")
    collection = client.get_collection("medical_docs")

    # Get all documents
    print("\n📂 Loading all documents...")
    results = collection.get(include=["documents", "metadatas"])

    ids = results["ids"]
    documents = results["documents"]
    metadatas = results["metadatas"]

    print(f"   ✅ Total documents: {len(ids)}")

    # Find documents without content_hash
    to_update = []
    already_have = 0

    for doc_id, doc, meta in zip(ids, documents, metadatas):
        if not meta.get("content_hash"):
            to_update.append((doc_id, doc, meta))
        else:
            already_have += 1

    print(f"   ✅ Already have hash: {already_have}")
    print(f"   ⚠️  Need hash: {len(to_update)}")

    if not to_update:
        print("\n✅ All documents already have content_hash!")
        return

    # Update documents with content_hash
    print(f"\n🔄 Generating content_hash for {len(to_update)} documents...")

    # Group by source_file to use same hash
    file_hashes = {}

    for idx, (doc_id, doc, meta) in enumerate(to_update, 1):
        source_file = meta.get("source_file", "unknown")

        # Generate hash (once per source file for document_name type)
        if meta.get("type") == "document_name":
            content_hash = generate_content_hash(doc)
            file_hashes[source_file] = content_hash
        else:
            # For chunks, use the hash from document_name
            content_hash = file_hashes.get(source_file)
            if not content_hash:
                # If not found, generate from chunk content
                content_hash = generate_content_hash(doc)

        # Update metadata
        meta["content_hash"] = content_hash
        collection.update(ids=[doc_id], metadatas=[meta])

        if idx % 50 == 0:
            print(f"   ✅ Updated {idx}/{len(to_update)}...")

    print(f"\n✅ Updated all {len(to_update)} documents!")
    print("="*60)
    print("MIGRATION COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    migrate_content_hashes()
