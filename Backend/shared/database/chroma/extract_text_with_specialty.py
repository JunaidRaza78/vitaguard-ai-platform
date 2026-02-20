"""
Step 1: Extract PDF with Specialty/Agent Type
- Extract document name and text from PDF
- Detect specialty (diabetes/heart/cancer)
- Remove references, lowercase
- Save to Chroma with specialty metadata
"""

from pathlib import Path
from PyPDF2 import PdfReader
import re
import chromadb
import uuid
import hashlib
import logging
from datetime import datetime
try:
    from .agent_types import MedicalSpecialty, get_agent_specialty
except ImportError:
    from agent_types import MedicalSpecialty, get_agent_specialty

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# TEXT PREPROCESSING
# ============================================

def remove_references(text):
    """Remove references section"""
    patterns = [
        r'\n\s*REFERENCES\s*\n.*',
        r'\n\s*References\s*\n.*',
        r'\n\s*BIBLIOGRAPHY\s*\n.*',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\([A-Z][a-z]+,\s*\d{4}\)', '', text)
    return text


def clean_and_lowercase(text):
    """Clean and lowercase text"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\.{2,}', ' ', text)  # Remove multiple consecutive dots
    text = text.lower()
    return text.strip()


def preprocess_text(text):
    """Complete preprocessing"""
    text = remove_references(text)
    text = clean_and_lowercase(text)
    return text


# ============================================
# SPECIALTY DETECTION
# ============================================

def detect_specialty(filename, text):
    """Detect medical specialty from filename or content"""
    filename_lower = filename.lower()
    text_lower = text[:1000].lower()  # First 1000 chars

    # Keyword mapping - expanded for your dataset
    keywords = {
        MedicalSpecialty.CARDIOLOGY: [
            "heart", "cardiac", "cardiology", "cardiovascular",
            "hypertension", "blood pressure", "bp", "hta"
        ],
        MedicalSpecialty.PULMONOLOGY: [
            "copd", "lung", "respiratory", "pulmonary", "asthma", "breathing"
        ],
        MedicalSpecialty.INFECTIOUS_DISEASE: [
            "covid", "dengue", "malaria", "viral", "hepatitis",
            "infection", "virus", "bacterial"
        ],
        MedicalSpecialty.ENDOCRINOLOGY: [
            "diabetes", "endocrin", "insulin", "blood sugar",
            "thyroid", "hypothyroid", "hyperthyroid", "obesity"
        ],
        MedicalSpecialty.ONCOLOGY: [
            "cancer", "oncology", "tumor", "chemotherapy", "malignant"
        ],
        MedicalSpecialty.GASTROENTEROLOGY: [
            "stomach", "digestive", "gastro", "intestine", "hepatitis", "liver"
        ],
        MedicalSpecialty.NEUROLOGY: [
            "brain", "neuro", "alzheimer", "parkinson", "stroke"
        ],
        MedicalSpecialty.PEDIATRICS: [
            "child", "pediatric", "infant", "baby", "adolescent"
        ],
        MedicalSpecialty.ORTHOPEDICS: [
            "bone", "joint", "orthopedic", "fracture"
        ],
        MedicalSpecialty.DERMATOLOGY: [
            "skin", "derma", "rash", "acne"
        ],
    }

    # Check filename first (higher priority)
    for specialty, words in keywords.items():
        for word in words:
            if word in filename_lower:
                return specialty

    # Check content
    for specialty, words in keywords.items():
        for word in words:
            if word in text_lower:
                return specialty

    return MedicalSpecialty.GENERAL


# ============================================
# PDF EXTRACTION
# ============================================

def extract_pdf(pdf_path):
    """Extract document name and text"""
    try:
        doc_name = Path(pdf_path).stem
        logger.debug(f"Extracting PDF: {doc_name}")

        reader = PdfReader(pdf_path)
        text = ""
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

            if page_num % 10 == 0:
                logger.debug(f"Processed {page_num} pages for {doc_name}")

        logger.info(f"Extracted {len(reader.pages)} pages from {doc_name}")
        return doc_name, text.strip()

    except Exception as e:
        logger.error(f"Error extracting PDF {pdf_path}: {str(e)}", exc_info=True)
        raise


def generate_content_hash(text):
    """
    Generate robust hash from multiple text samples for duplicate detection
    - Samples from beginning, middle, and end
    - Includes document length
    - Reduces false positives from similar introductions
    """
    text = text.strip().lower()
    length = len(text)

    # Sample from 3 positions: beginning (0-500), middle, end
    samples = []
    samples.append(text[:500])  # First 500 chars

    if length > 1000:
        mid = length // 2
        samples.append(text[mid:mid+500])  # Middle 500 chars

    if length > 1500:
        samples.append(text[-500:])  # Last 500 chars

    # Combine all samples
    combined = "".join(samples)

    # Generate hash from combined samples + total length
    hash_input = f"{combined}|{length}"
    return hashlib.md5(hash_input.encode()).hexdigest()


# ============================================
# MAIN PROCESS
# ============================================

# Find ALL PDFs
def ingest_medical_pdfs(user_id: str, document_id: str = None, pdf_path: Path = None):
    """
    Step 1:
    - Extract PDFs
    - Detect specialty / agent
    - Preprocess text
    - Save to Chroma (no embeddings) with user isolation

    Args:
        user_id: The user who uploaded the document(s) - REQUIRED for user isolation
        document_id: Optional document ID to link to PostgreSQL record
        pdf_path: Optional specific PDF file path. If None, processes all PDFs in dataset

    Returns:
        Dict with processing results including chroma_ids
    """

    print("\n" + "="*60)
    print(f"STEP 1: Extract PDF with Agent/Specialty (User: {user_id})")
    print("="*60)

    # Determine which PDFs to process
    if pdf_path:
        # Process single file
        if not pdf_path.exists():
            print(f"\n❌ File not found: {pdf_path}")
            return {"processed": 0, "skipped": 0, "chroma_ids": []}
        pdf_files = [pdf_path]
        print(f"\n📁 Processing single file: {pdf_path}")
    else:
        # Find ALL PDFs - use absolute path relative to this script's location
        # This script is in Backend/shared/database/chroma/
        # Dataset is in project_root/dataset/ (one level above Backend)
        script_dir = Path(__file__).parent  # .../Backend/shared/database/chroma
        backend_dir = script_dir.parent.parent.parent  # .../Backend
        dataset_dir = backend_dir.parent / "dataset"  # .../project_root/dataset

        print(f"\n📁 Looking for PDFs in: {dataset_dir}")
        pdf_files = list(dataset_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"\n❌ No PDFs found in {dataset_dir}")
            return {"processed": 0, "skipped": 0, "chroma_ids": []}

    print(f"\n📚 Found {len(pdf_files)} PDF(s) to process")
    print("="*60)

    # Initialize Chroma — use absolute path (same as query_by_agent.py)
    print("\n🔌 Initializing Chroma...")
    _script_dir = Path(__file__).resolve().parent  # .../shared/database/chroma/
    _chroma_path = str(_script_dir / "chroma_data")
    client = chromadb.PersistentClient(path=_chroma_path)
    print(f"   📁 ChromaDB path: {_chroma_path}")

    try:
        collection = client.get_collection("medical_docs")
        print("   ✅ Found existing collection")

        existing_docs = collection.get(include=["metadatas"])
        # Store both filename and content_hash for duplicate detection
        # CRITICAL: Filter by user_id — each user's files are independent
        existing_files = {
            meta.get("source_file") for meta in existing_docs["metadatas"]
            if meta.get("user_id") == user_id
        }
        existing_hashes = {
            meta.get("content_hash") for meta in existing_docs["metadatas"]
            if meta.get("content_hash") and meta.get("user_id") == user_id
        }
        print(f"   ✅ Already processed by this user: {len(existing_files)} PDFs")
        print(f"   ✅ Content hashes tracked: {len(existing_hashes)}")

    except:
        collection = client.create_collection(
            name="medical_docs",
            metadata={"description": "Multi-agent medical documents"}
        )
        existing_files = set()
        existing_hashes = set()
        print("   ✅ Created new collection")

    total_docs = 0
    total_chunks = 0
    skipped_docs = 0
    specialty_counts = {}
    all_chroma_ids = []  # Track all ChromaDB IDs for this document

    # Process PDFs
    for pdf_idx, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"\n{'='*60}")
            print(f"📄 [{pdf_idx}/{len(pdf_files)}] Processing: {pdf_path.name}")
            print(f"{'='*60}")
            logger.info(f"Processing PDF {pdf_idx}/{len(pdf_files)}: {pdf_path.name}")

            # Extract first to check content
            doc_name, raw_text = extract_pdf(pdf_path)
            content_hash = generate_content_hash(raw_text)
            logger.debug(f"Generated content_hash: {content_hash}")

            # Check if already processed by filename
            if pdf_path.name in existing_files:
                print("   ⏭️  Already processed (same filename) - SKIPPING")
                logger.info(f"Skipped (duplicate filename): {pdf_path.name}")
                skipped_docs += 1
                continue

            # Check if already processed by content (renamed file detection)
            if content_hash in existing_hashes:
                print("   ⏭️  Already processed (same content, different name) - SKIPPING")
                logger.info(f"Skipped (duplicate content): {pdf_path.name}")
                skipped_docs += 1
                continue

            # Detect specialty
            specialty = detect_specialty(pdf_path.name, raw_text)
            specialty_counts[specialty.value] = (
                specialty_counts.get(specialty.value, 0) + 1
            )
            logger.info(f"Detected specialty: {specialty.value}")

            # Preprocess
            clean_text = preprocess_text(raw_text)
            logger.debug(f"Preprocessed text length: {len(clean_text)}")

        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {str(e)}", exc_info=True)
            print(f"   ❌ ERROR: {str(e)}")
            continue

        # Save document name
        doc_id = str(uuid.uuid4())
        collection.add(
            ids=[doc_id],
            documents=[doc_name.lower()],
            metadatas=[{
                "type": "document_name",
                "specialty": specialty.value,
                "agent": specialty.value,
                "source_file": pdf_path.name,
                "content_hash": content_hash,
                "indexed_at": datetime.utcnow().isoformat(),
                "user_id": user_id,  # NEW: User isolation
                "document_id": document_id or f"legacy_{doc_id[:8]}"  # NEW: Link to PostgreSQL
            }]
        )
        all_chroma_ids.append(doc_id)  # Track ID
        total_docs += 1

        # Chunking
        chunk_size = 2000
        overlap = 300

        chunks = []
        for i in range(0, len(clean_text), chunk_size - overlap):
            chunk = clean_text[i:i + chunk_size]
            if len(chunk.strip()) > 100:
                chunks.append(chunk)

        for i, chunk in enumerate(chunks[:20], 1):
            chunk_id = str(uuid.uuid4())
            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[{
                    "type": "content",
                    "specialty": specialty.value,
                    "agent": specialty.value,
                    "document_name": doc_name.lower(),
                    "chunk_index": i,
                    "source_file": pdf_path.name,
                    "content_hash": content_hash,
                    "user_id": user_id,  # NEW: User isolation
                    "document_id": document_id or f"legacy_{doc_id[:8]}"  # NEW: Link to PostgreSQL
                }]
            )
            all_chroma_ids.append(chunk_id)  # Track ID
        total_chunks += min(20, len(chunks))

    print("\n" + "="*60)
    print("✅ PDF PROCESSING COMPLETE!")
    print("="*60)
    print(f"   • Newly processed: {total_docs}")
    print(f"   • Skipped: {skipped_docs}")
    print(f"   • New chunks: {total_chunks}")
    print(f"   • Total DB entries: {collection.count()}")
    print(f"   • ChromaDB IDs tracked: {len(all_chroma_ids)}")

    # Determine specialty (use the last processed file's specialty)
    detected_specialty = list(specialty_counts.keys())[0] if specialty_counts else None

    return {
        "processed": total_docs,
        "skipped": skipped_docs,
        "chunks": total_chunks,
        "specialties": specialty_counts,
        "chroma_ids": all_chroma_ids,  # NEW: Return ChromaDB IDs
        "specialty": detected_specialty  # NEW: Return detected specialty
    }
