"""
Web search functionality for medical information
Uses DuckDuckGo with trusted source filtering
"""

from duckduckgo_search import DDGS
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def duckduckgo_medical_search(query: str, max_results: int = 5) -> str:
    """
    DuckDuckGo medical web search with trusted source filtering and quality scoring.
    Returns combined text snippets from reliable medical sources.
    
    Args:
        query: User's medical question
        max_results: Maximum number of results to fetch (default: 5)
    
    Returns:
        Combined text from search results with source attribution
    """
    
    # Trusted medical sources with quality scores (higher = more trusted)
    trusted_sources = {
        # Medical institutions (highest priority)
        "mayoclinic.org": 10,
        "clevelandclinic.org": 10,
        "who.int": 10,
        "cdc.gov": 10,
        "nih.gov": 10,
        "nhs.uk": 10,
        
        # Medical information sites (high priority)
        "webmd.com": 8,
        "healthline.com": 8,
        "medicalnewstoday.com": 8,
        "medlineplus.gov": 8,
        
        # Medical journals and databases (high priority)
        "pubmed.ncbi.nlm.nih.gov": 9,
        "bmj.com": 9,
        "thelancet.com": 9,
        
        # General health info (medium priority)
        "health.harvard.edu": 7,
        "hopkinsmedicine.org": 7,
        "verywellhealth.com": 7,
    }
    
    results_with_scores = []

    try:
        with DDGS() as ddgs:
            # Enhanced query for medical information
            enhanced_query = f"{query} medical information health"
            
            logger.info(f"Searching web for: {enhanced_query}")
            
            results = ddgs.text(
                enhanced_query,
                max_results=max_results * 3  # Fetch more to filter better
            )

            for r in results:
                body = r.get("body", "")
                href = r.get("href", "")
                title = r.get("title", "")
                
                if not body or len(body) < 50:  # Skip very short snippets
                    continue
                
                # Calculate quality score
                score = 0
                source_name = ""
                
                # Check if from trusted source
                for source, source_score in trusted_sources.items():
                    if source in href.lower():
                        score = source_score
                        source_name = source
                        break
                
                # If not from trusted source, give low score
                if score == 0:
                    # Check if content seems medical
                    medical_keywords = ["health", "medical", "disease", "treatment", "symptom", "doctor", "medication", "diagnosis"]
                    if any(keyword in body.lower() for keyword in medical_keywords):
                        score = 3  # Low but acceptable
                
                if score > 0:
                    results_with_scores.append({
                        "body": body,
                        "title": title,
                        "href": href,
                        "source": source_name or "General source",
                        "score": score
                    })
            
            # Sort by score (highest first)
            results_with_scores.sort(key=lambda x: x["score"], reverse=True)
            
            # Log results
            if results_with_scores:
                logger.info(f"Found {len(results_with_scores)} web results")
                top_sources = [r['source'] for r in results_with_scores[:3]]
                logger.info(f"Top sources: {top_sources}")
            else:
                logger.warning(f"No suitable web results found for: {query}")

    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return ""

    # Build response from top 3 results
    if not results_with_scores:
        logger.warning("No web search results available")
        return ""
    
    snippets = []
    for result in results_with_scores[:3]:
        # Format: Source attribution + content
        snippet = f"**Source: {result['title']}** (Quality: {result['score']}/10)\n{result['body']}"
        snippets.append(snippet)
    
    combined = "\n\n---\n\n".join(snippets)
    return f"MEDICAL INFORMATION FROM WEB:\n\n{combined}"


def search_medical_condition(condition: str, max_results: int = 5) -> str:
    """
    Specialized search for specific medical conditions.
    
    Args:
        condition: Medical condition name (e.g., "diabetes", "hypertension")
        max_results: Maximum results to fetch
    
    Returns:
        Relevant information about the condition
    """
    query = f"{condition} symptoms causes treatment prevention"
    logger.info(f"Searching for medical condition: {condition}")
    return duckduckgo_medical_search(query, max_results)


def search_medicine_info(medicine_name: str, max_results: int = 3) -> str:
    """
    Search for information about a specific medicine.
    
    Args:
        medicine_name: Name of the medicine (e.g., "Paracetamol")
        max_results: Maximum results to fetch
    
    Returns:
        Medicine information including dosage, side effects
    """
    query = f"{medicine_name} dosage side effects uses medication"
    logger.info(f"Searching for medicine info: {medicine_name}")
    return duckduckgo_medical_search(query, max_results)


def search_symptom_causes(symptom: str, max_results: int = 5) -> str:
    """
    Search for possible causes of a symptom.
    
    Args:
        symptom: Symptom description (e.g., "headache", "stomach pain")
        max_results: Maximum results to fetch
    
    Returns:
        Information about possible causes and treatments
    """
    query = f"{symptom} causes treatment when to see doctor"
    logger.info(f"Searching for symptom causes: {symptom}")
    return duckduckgo_medical_search(query, max_results)


# Optional: Function to check if a source is trusted
def is_trusted_source(url: str) -> bool:
    """
    Check if a URL is from a trusted medical source.
    
    Args:
        url: URL to check
    
    Returns:
        True if from trusted source, False otherwise
    """
    trusted_domains = [
        "mayoclinic.org", "clevelandclinic.org", "who.int", "cdc.gov",
        "nih.gov", "nhs.uk", "webmd.com", "healthline.com",
        "medicalnewstoday.com", "medlineplus.gov", "pubmed.ncbi.nlm.nih.gov"
    ]
    
    url_lower = url.lower()
