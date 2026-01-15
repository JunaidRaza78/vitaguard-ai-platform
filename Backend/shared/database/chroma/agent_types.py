"""
Agent Types & Specialties
Simple categorization for multi-agent system
"""

from enum import Enum


class MedicalSpecialty(str, Enum):
    """Medical specialties for different agents"""
    GENERAL = "general"
    CARDIOLOGY = "cardiology"                   # Heart agent
    ONCOLOGY = "oncology"                       # Cancer agent
    ENDOCRINOLOGY = "endocrinology"             # Diabetes/Thyroid agent
    NEUROLOGY = "neurology"                     # Brain/Neuro agent
    PEDIATRICS = "pediatrics"                   # Child health agent
    GASTROENTEROLOGY = "gastroenterology"       # Digestive/Liver agent
    ORTHOPEDICS = "orthopedics"                 # Bone/Joint agent
    DERMATOLOGY = "dermatology"                 # Skin agent
    PSYCHIATRY = "psychiatry"                   # Mental health agent
    PULMONOLOGY = "pulmonology"                 # Lung/Respiratory agent
    INFECTIOUS_DISEASE = "infectious_disease"   # Viral/Bacterial infections


class ContentType(str, Enum):
    """Type of medical content"""
    GUIDELINE = "guideline"
    RESEARCH = "research"
    DRUG_INFO = "drug_info"
    SYMPTOM = "symptom"
    TREATMENT = "treatment"
    GENERAL = "general"


def get_agent_specialty(agent_name: str) -> MedicalSpecialty:
    """Map agent name to specialty"""
    mapping = {
        "heart": MedicalSpecialty.CARDIOLOGY,
        "cardiology": MedicalSpecialty.CARDIOLOGY,
        "cancer": MedicalSpecialty.ONCOLOGY,
        "oncology": MedicalSpecialty.ONCOLOGY,
        "diabetes": MedicalSpecialty.ENDOCRINOLOGY,
        "endocrinology": MedicalSpecialty.ENDOCRINOLOGY,
        "brain": MedicalSpecialty.NEUROLOGY,
        "neuro": MedicalSpecialty.NEUROLOGY,
        "child": MedicalSpecialty.PEDIATRICS,
        "pediatrics": MedicalSpecialty.PEDIATRICS,
        "skin": MedicalSpecialty.DERMATOLOGY,
        "dermatology": MedicalSpecialty.DERMATOLOGY,
        "lung": MedicalSpecialty.PULMONOLOGY,
        "pulmonology": MedicalSpecialty.PULMONOLOGY,
        "infection": MedicalSpecialty.INFECTIOUS_DISEASE,
        "infectious": MedicalSpecialty.INFECTIOUS_DISEASE,
        "viral": MedicalSpecialty.INFECTIOUS_DISEASE,
    }
    return mapping.get(agent_name.lower(), MedicalSpecialty.GENERAL)


# Quick examples
if __name__ == "__main__":
    print("Agent Specialties:")
    print(f"  Heart agent: {get_agent_specialty('heart')}")
    print(f"  Cancer agent: {get_agent_specialty('cancer')}")
    print(f"  Diabetes agent: {get_agent_specialty('diabetes')}")
