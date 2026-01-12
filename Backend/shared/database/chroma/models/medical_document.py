"""
Medical Document Models
Data models for medical knowledge documents
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """Medical content types"""
    ARTICLE = "article"
    GUIDELINE = "guideline"
    DRUG_INFO = "drug_info"
    DISEASE_INFO = "disease_info"
    PROCEDURE = "procedure"
    SYMPTOM = "symptom"
    FAQ = "faq"
    RESEARCH = "research"


class MedicalSpecialty(str, Enum):
    """Medical specialties"""
    GENERAL = "general"
    CARDIOLOGY = "cardiology"
    PEDIATRICS = "pediatrics"
    ONCOLOGY = "oncology"
    NEUROLOGY = "neurology"
    PSYCHIATRY = "psychiatry"
    DERMATOLOGY = "dermatology"
    ORTHOPEDICS = "orthopedics"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"


class TargetAudience(str, Enum):
    """Target audience complexity levels"""
    PATIENT = "patient"
    GENERAL_PUBLIC = "general_public"
    HEALTHCARE_PROFESSIONAL = "healthcare_professional"
    RESEARCHER = "researcher"


class MedicalDocument(BaseModel):
    """Medical knowledge document model"""

    # Core fields
    id: Optional[str] = Field(default=None, description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content text")

    # Classification
    content_type: ContentType = Field(..., description="Type of medical content")
    specialty: MedicalSpecialty = Field(default=MedicalSpecialty.GENERAL, description="Medical specialty")
    target_audience: TargetAudience = Field(default=TargetAudience.PATIENT, description="Target audience")

    # Source information
    source: str = Field(..., description="Source (e.g., CDC, FDA, Mayo Clinic)")
    source_url: Optional[str] = Field(default=None, description="Original URL")
    author: Optional[str] = Field(default=None, description="Author or organization")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")

    # Medical codes and identifiers
    icd_codes: List[str] = Field(default_factory=list, description="ICD-10 codes")
    drug_names: List[str] = Field(default_factory=list, description="Drug names mentioned")
    snomed_codes: List[str] = Field(default_factory=list, description="SNOMED CT codes")

    # Quality metrics
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Reliability score (0-1)")
    peer_reviewed: bool = Field(default=False, description="Is peer-reviewed")
    evidence_level: Optional[str] = Field(default=None, description="Evidence level (A, B, C)")

    # Metadata
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    language: str = Field(default="en", description="Language code")

    # Timestamps
    indexed_at: Optional[datetime] = Field(default=None, description="Indexing timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    # Additional metadata
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert to Chroma-compatible metadata"""
        metadata = {
            "title": self.title,
            "content_type": self.content_type.value,
            "specialty": self.specialty.value,
            "target_audience": self.target_audience.value,
            "source": self.source,
            "reliability_score": self.reliability_score,
            "peer_reviewed": self.peer_reviewed,
            "language": self.language,
        }

        # Add optional fields if present
        if self.source_url:
            metadata["source_url"] = self.source_url
        if self.author:
            metadata["author"] = self.author
        if self.published_date:
            metadata["published_date"] = self.published_date.isoformat()
        if self.evidence_level:
            metadata["evidence_level"] = self.evidence_level

        # Add lists as JSON strings (Chroma limitation)
        if self.icd_codes:
            metadata["icd_codes"] = ",".join(self.icd_codes)
        if self.drug_names:
            metadata["drug_names"] = ",".join(self.drug_names)
        if self.keywords:
            metadata["keywords"] = ",".join(self.keywords)

        return metadata

    @classmethod
    def from_chroma_result(cls, result: Dict[str, Any]) -> 'MedicalDocument':
        """Create from Chroma search result"""
        metadata = result.get("metadata", {})

        return cls(
            id=result.get("id"),
            title=metadata.get("title", ""),
            content=result.get("document", ""),
            content_type=ContentType(metadata.get("content_type", "article")),
            specialty=MedicalSpecialty(metadata.get("specialty", "general")),
            target_audience=TargetAudience(metadata.get("target_audience", "patient")),
            source=metadata.get("source", ""),
            source_url=metadata.get("source_url"),
            author=metadata.get("author"),
            published_date=datetime.fromisoformat(metadata["published_date"]) if metadata.get("published_date") else None,
            icd_codes=metadata.get("icd_codes", "").split(",") if metadata.get("icd_codes") else [],
            drug_names=metadata.get("drug_names", "").split(",") if metadata.get("drug_names") else [],
            keywords=metadata.get("keywords", "").split(",") if metadata.get("keywords") else [],
            reliability_score=metadata.get("reliability_score", 0.8),
            peer_reviewed=metadata.get("peer_reviewed", False),
            evidence_level=metadata.get("evidence_level"),
            language=metadata.get("language", "en"),
            indexed_at=datetime.fromisoformat(metadata["indexed_at"]) if metadata.get("indexed_at") else None,
            updated_at=datetime.fromisoformat(metadata["updated_at"]) if metadata.get("updated_at") else None,
        )

    class Config:
        use_enum_values = True


class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    min_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum relevance score")

    # Filters
    content_type: Optional[ContentType] = Field(default=None, description="Filter by content type")
    specialty: Optional[MedicalSpecialty] = Field(default=None, description="Filter by specialty")
    language: str = Field(default="en", description="Language filter")
    min_reliability: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum reliability score")

    def to_metadata_filter(self) -> Dict[str, Any]:
        """Convert to Chroma metadata filter"""
        filters = {"language": self.language}

        if self.content_type:
            filters["content_type"] = self.content_type.value
        if self.specialty:
            filters["specialty"] = self.specialty.value

        return filters


class SearchResult(BaseModel):
    """Search result model"""
    document: MedicalDocument
    score: float = Field(..., description="Relevance score (0-1)")
    distance: float = Field(..., description="Vector distance")
    rank: int = Field(..., description="Result rank")
