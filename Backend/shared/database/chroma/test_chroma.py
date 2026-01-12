"""
Test Chroma DB Setup
Quick test script to verify Chroma DB installation and configuration
"""

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test if all imports work"""
    logger.info("Testing imports...")
    try:
        from shared.database.chroma import (
            get_client,
            get_embedding_service,
            get_vector_operations,
            chroma_config
        )
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_connection():
    """Test Chroma DB connection"""
    logger.info("\nTesting Chroma DB connection...")
    try:
        from shared.database.chroma import get_client

        client = get_client()
        version = client.get_version()
        heartbeat = client.heartbeat()

        logger.info(f"✓ Connected to Chroma DB")
        logger.info(f"  Version: {version}")
        logger.info(f"  Heartbeat: {heartbeat}")
        return True
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return False


def test_collection():
    """Test collection operations"""
    logger.info("\nTesting collection operations...")
    try:
        from shared.database.chroma import get_client

        client = get_client()
        collection = client.get_or_create_collection()

        logger.info(f"✓ Collection ready")
        logger.info(f"  Name: {collection.name}")
        logger.info(f"  Count: {collection.count()}")
        return True
    except Exception as e:
        logger.error(f"✗ Collection test failed: {e}")
        return False


def test_embeddings():
    """Test embedding service"""
    logger.info("\nTesting embedding service...")
    try:
        from shared.database.chroma import get_embedding_service

        service = get_embedding_service()
        model_info = service.get_model_info()

        logger.info(f"✓ Embedding service ready")
        logger.info(f"  Provider: {model_info['provider']}")
        logger.info(f"  Model: {model_info['model']}")
        logger.info(f"  Dimension: {model_info['dimension']}")

        # Test embedding generation
        test_text = "This is a test sentence."
        embedding = service.generate_embedding(test_text)

        logger.info(f"  Test embedding dimension: {len(embedding)}")
        return True
    except Exception as e:
        logger.error(f"✗ Embedding test failed: {e}")
        if "openai" in str(e).lower():
            logger.error(f"  If using OpenAI, make sure OPENAI_API_KEY is set in .env")
        elif "sentence" in str(e).lower() or "transformers" in str(e).lower():
            logger.error(f"  Make sure sentence-transformers is installed: pip install sentence-transformers")
        return False


def test_vector_operations():
    """Test vector store operations"""
    logger.info("\nTesting vector operations...")
    try:
        from shared.database.chroma import get_vector_operations
        import uuid

        ops = get_vector_operations()

        # Test add document
        test_id = f"test-{uuid.uuid4()}"
        test_text = "Diabetes is a chronic disease that affects blood sugar levels."
        test_metadata = {
            "title": "Test Document",
            "source": "Test",
            "content_type": "article"
        }

        doc_id = ops.add_document(test_text, test_metadata, test_id)
        logger.info(f"✓ Added test document: {doc_id}")

        # Test search
        results = ops.search("diabetes", top_k=3)
        logger.info(f"✓ Search returned {len(results)} results")

        # Test get document
        doc = ops.get_document(doc_id)
        if doc:
            logger.info(f"✓ Retrieved document: {doc['id']}")
        else:
            logger.warning(f"⚠ Document not found: {doc_id}")

        # Test delete
        ops.delete_document(doc_id)
        logger.info(f"✓ Deleted test document")

        return True
    except Exception as e:
        logger.error(f"✗ Vector operations test failed: {e}")
        return False


def test_models():
    """Test data models"""
    logger.info("\nTesting data models...")
    try:
        from shared.database.chroma.models import (
            MedicalDocument,
            ContentType,
            MedicalSpecialty,
            SearchQuery
        )

        # Test MedicalDocument
        doc = MedicalDocument(
            title="Test Document",
            content="Test content",
            content_type=ContentType.ARTICLE,
            specialty=MedicalSpecialty.GENERAL,
            source="Test Source",
            keywords=["test", "document"]
        )

        metadata = doc.to_chroma_metadata()
        logger.info(f"✓ MedicalDocument model works")
        logger.info(f"  Metadata keys: {list(metadata.keys())}")

        # Test SearchQuery
        query = SearchQuery(
            query="test query",
            top_k=5,
            min_score=0.7
        )

        filters = query.to_metadata_filter()
        logger.info(f"✓ SearchQuery model works")
        logger.info(f"  Filters: {filters}")

        return True
    except Exception as e:
        logger.error(f"✗ Models test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Chroma DB Setup Test Suite")
    logger.info("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Connection", test_connection),
        ("Collection", test_collection),
        ("Embeddings", test_embeddings),
        ("Vector Operations", test_vector_operations),
        ("Data Models", test_models),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 60)

    if passed == total:
        logger.info("✓ All tests passed! Chroma DB is ready to use.")
        return 0
    else:
        logger.error(f"✗ {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
