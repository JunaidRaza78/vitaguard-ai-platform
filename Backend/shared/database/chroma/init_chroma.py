"""
Initialize Chroma Database
Setup script for medical knowledge base
"""

import asyncio
import logging
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.database.chroma import (
    get_client,
    get_embedding_service,
    get_vector_operations,
    chroma_config
)
from shared.database.chroma.models import MedicalDocument, ContentType, MedicalSpecialty

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_medical_documents() -> List[MedicalDocument]:
    """Create sample medical documents for testing"""
    documents = [
        MedicalDocument(
            title="Understanding Diabetes: Types, Symptoms, and Management",
            content="""
            Diabetes is a chronic metabolic disease characterized by elevated levels of blood glucose (or blood sugar),
            which leads over time to serious damage to the heart, blood vessels, eyes, kidneys and nerves.

            There are two main types:
            - Type 1 diabetes: The body doesn't produce insulin
            - Type 2 diabetes: The body doesn't use insulin properly

            Common symptoms include increased thirst, frequent urination, extreme fatigue, blurred vision, and slow-healing wounds.

            Management includes monitoring blood sugar, taking medications as prescribed, eating a healthy diet,
            maintaining a healthy weight, and getting regular physical activity.
            """,
            content_type=ContentType.DISEASE_INFO,
            specialty=MedicalSpecialty.ENDOCRINOLOGY,
            source="CDC",
            source_url="https://www.cdc.gov/diabetes/",
            icd_codes=["E11", "E10"],
            keywords=["diabetes", "blood sugar", "insulin", "glucose"],
            reliability_score=0.95,
            peer_reviewed=True,
        ),
        MedicalDocument(
            title="Hypertension (High Blood Pressure): Causes and Prevention",
            content="""
            Hypertension, or high blood pressure, is a common condition where the force of blood against artery walls
            is too high. It can lead to serious health complications like heart disease and stroke if left untreated.

            Risk factors include:
            - Age (risk increases with age)
            - Family history
            - Being overweight or obese
            - Lack of physical activity
            - Too much salt in diet
            - Excessive alcohol consumption
            - Stress

            Prevention and management:
            - Maintain a healthy weight
            - Exercise regularly
            - Eat a healthy diet (DASH diet)
            - Limit sodium intake
            - Limit alcohol
            - Don't smoke
            - Manage stress
            - Monitor blood pressure regularly
            """,
            content_type=ContentType.DISEASE_INFO,
            specialty=MedicalSpecialty.CARDIOLOGY,
            source="Mayo Clinic",
            source_url="https://www.mayoclinic.org/diseases-conditions/high-blood-pressure/",
            icd_codes=["I10"],
            keywords=["hypertension", "blood pressure", "heart disease", "cardiovascular"],
            reliability_score=0.93,
            peer_reviewed=True,
        ),
        MedicalDocument(
            title="Metformin: Uses, Dosage, and Side Effects",
            content="""
            Metformin is an oral diabetes medication that helps control blood sugar levels.
            It is used to treat type 2 diabetes, either alone or in combination with other medications.

            How it works:
            - Decreases glucose production in the liver
            - Decreases intestinal absorption of glucose
            - Improves insulin sensitivity

            Common dosage:
            - Initial: 500mg twice daily or 850mg once daily
            - Maximum: 2000-2550mg per day in divided doses

            Common side effects:
            - Nausea and vomiting
            - Diarrhea
            - Stomach upset
            - Metallic taste

            Serious side effects (rare):
            - Lactic acidosis
            - Vitamin B12 deficiency

            Important: Always take with meals to reduce stomach upset.
            Do not crush or chew extended-release tablets.
            """,
            content_type=ContentType.DRUG_INFO,
            specialty=MedicalSpecialty.ENDOCRINOLOGY,
            source="FDA",
            source_url="https://www.fda.gov/drugs/",
            drug_names=["metformin", "glucophage"],
            keywords=["metformin", "diabetes medication", "blood sugar", "antidiabetic"],
            reliability_score=0.98,
            peer_reviewed=True,
        ),
        MedicalDocument(
            title="Childhood Immunization Schedule",
            content="""
            Childhood vaccines protect against serious diseases. The CDC recommends vaccinations from birth through adolescence.

            Birth:
            - Hepatitis B (HepB)

            2 months:
            - HepB, DTaP, Hib, IPV, PCV13, RV

            4 months:
            - DTaP, Hib, IPV, PCV13, RV

            6 months:
            - HepB, DTaP, Hib, IPV, PCV13, RV

            12-15 months:
            - MMR, Varicella, HepA, PCV13, Hib

            4-6 years:
            - DTaP, IPV, MMR, Varicella

            11-12 years:
            - Tdap, HPV, Meningococcal

            Key abbreviations:
            - DTaP: Diphtheria, tetanus, and pertussis
            - MMR: Measles, mumps, and rubella
            - IPV: Polio
            - Hib: Haemophilus influenzae type b
            - PCV13: Pneumococcal conjugate
            """,
            content_type=ContentType.GUIDELINE,
            specialty=MedicalSpecialty.PEDIATRICS,
            source="CDC",
            source_url="https://www.cdc.gov/vaccines/schedules/hcp/imz/child-adolescent.html",
            keywords=["vaccines", "immunization", "children", "pediatric", "vaccination schedule"],
            reliability_score=0.99,
            peer_reviewed=True,
        ),
        MedicalDocument(
            title="Common Cold: Symptoms and Home Remedies",
            content="""
            The common cold is a viral infection of the upper respiratory tract. While uncomfortable,
            it's usually harmless and symptoms typically resolve within 7-10 days.

            Symptoms:
            - Runny or stuffy nose
            - Sore throat
            - Cough
            - Sneezing
            - Mild headache
            - Low-grade fever
            - General malaise

            Home remedies and care:
            - Get plenty of rest
            - Drink lots of fluids (water, warm tea, soup)
            - Gargle with salt water for sore throat
            - Use saline nasal drops
            - Humidify the air
            - Use over-the-counter pain relievers (acetaminophen, ibuprofen)
            - Honey for cough (for children over 1 year)

            When to see a doctor:
            - Symptoms last more than 10 days
            - Symptoms are severe or unusual
            - High fever (over 101.3°F or 38.5°C)
            - Difficulty breathing
            - Severe headache or sinus pain

            Note: Antibiotics don't work for colds (caused by viruses, not bacteria).
            """,
            content_type=ContentType.ARTICLE,
            specialty=MedicalSpecialty.GENERAL,
            source="MedlinePlus",
            source_url="https://medlineplus.gov/commoncold.html",
            keywords=["cold", "upper respiratory infection", "viral infection", "home remedies"],
            reliability_score=0.90,
            peer_reviewed=False,
        ),
    ]

    return documents


async def initialize_chroma_db():
    """Initialize Chroma database with sample data"""
    try:
        logger.info("=" * 60)
        logger.info("Initializing Chroma Database for Medical Knowledge")
        logger.info("=" * 60)

        # Step 1: Test connection
        logger.info("\n1. Testing Chroma DB connection...")
        client = get_client()
        version = client.get_version()
        logger.info(f"✓ Connected to Chroma DB version: {version}")

        # Step 2: Test embedding service
        logger.info("\n2. Testing Embedding Service...")
        embedding_service = get_embedding_service()
        model_info = embedding_service.get_model_info()
        logger.info(f"✓ Embedding provider: {model_info['provider']}")
        logger.info(f"  Model: {model_info['model']}")
        logger.info(f"  Dimension: {model_info['dimension']}")
        if model_info['provider'] == 'sentence-transformers':
            logger.info(f"  Device: {model_info.get('device', 'cpu')}")
            logger.info("  (Using open-source model - no API key required)")

        # Step 3: Create/get collection
        logger.info("\n3. Setting up collection...")
        collection = client.get_or_create_collection()
        logger.info(f"✓ Collection '{collection.name}' is ready")
        logger.info(f"  Current document count: {collection.count()}")

        # Step 4: Add sample documents
        logger.info("\n4. Adding sample medical documents...")
        vector_ops = get_vector_operations()

        sample_docs = create_sample_medical_documents()
        logger.info(f"  Created {len(sample_docs)} sample documents")

        for i, doc in enumerate(sample_docs, 1):
            logger.info(f"  [{i}/{len(sample_docs)}] Adding: {doc.title}")
            doc_id = vector_ops.add_document(
                text=doc.content,
                metadata=doc.to_chroma_metadata()
            )
            logger.info(f"    ✓ Added with ID: {doc_id}")

        # Step 5: Verify documents
        logger.info("\n5. Verifying documents...")
        stats = vector_ops.get_collection_stats()
        logger.info(f"✓ Total documents in collection: {stats['count']}")

        # Step 6: Test search
        logger.info("\n6. Testing search functionality...")
        test_query = "What are the symptoms of diabetes?"
        logger.info(f"  Query: '{test_query}'")

        results = vector_ops.search(test_query, top_k=3)
        logger.info(f"✓ Found {len(results)} relevant results:")

        for i, result in enumerate(results, 1):
            logger.info(f"  [{i}] {result['metadata'].get('title', 'Untitled')}")
            logger.info(f"      Score: {result['score']:.4f}")
            logger.info(f"      Source: {result['metadata'].get('source', 'Unknown')}")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✓ Chroma DB Initialization Complete!")
        logger.info("=" * 60)
        logger.info(f"Collection: {collection.name}")
        logger.info(f"Documents: {stats['count']}")
        logger.info(f"Embedding Provider: {model_info['provider']}")
        logger.info(f"Embedding Model: {model_info['model']}")
        logger.info(f"Embedding Dimension: {model_info['dimension']}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"✗ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def reset_database():
    """Reset database (delete all data)"""
    try:
        logger.warning("=" * 60)
        logger.warning("RESETTING CHROMA DATABASE - ALL DATA WILL BE DELETED")
        logger.warning("=" * 60)

        response = input("Are you sure you want to reset the database? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Reset cancelled")
            return

        client = get_client()
        client.reset()
        logger.info("✓ Database reset complete")

    except Exception as e:
        logger.error(f"✗ Error during reset: {str(e)}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize Chroma DB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (delete all data)"
    )

    args = parser.parse_args()

    if args.reset:
        reset_database()
    else:
        asyncio.run(initialize_chroma_db())


if __name__ == "__main__":
    main()
