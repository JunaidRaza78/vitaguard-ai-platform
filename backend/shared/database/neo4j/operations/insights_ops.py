"""
AI Insights Operations for Neo4j
Handles CRUD operations for HealthInsight and RiskFactor nodes
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class InsightsOperations:
    """AI insights and risk factor operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== HealthInsight CRUD ====================

    def create_health_insight(
        self,
        user_id: str,
        insight_type: str,
        title: str,
        description: str,
        severity: str = "info",
        category: Optional[str] = None,
        confidence_score: Optional[float] = None,
        actionable: bool = True,
        recommendations: Optional[List[str]] = None,
        data_sources: Optional[List[str]] = None,
        expires_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a HealthInsight node and link to User.

        Args:
            user_id: User UUID
            insight_type: Type (trend, alert, recommendation, prediction)
            title: Insight title
            description: Detailed description
            severity: info/low/medium/high/critical
            category: Category (medication, vitals, condition, lifestyle, etc.)
            confidence_score: AI confidence (0.0-1.0)
            actionable: Whether user can take action
            recommendations: List of recommendations
            data_sources: Sources used to generate insight
            expires_at: Optional expiration datetime

        Returns:
            Created health insight data
        """
        insight_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {userId: $userId})
        CREATE (hi:HealthInsight {
            insightId: $insightId,
            type: $type,
            title: $title,
            description: $description,
            severity: $severity,
            category: $category,
            confidenceScore: $confidenceScore,
            actionable: $actionable,
            recommendations: $recommendations,
            dataSources: $dataSources,
            status: $status,
            expiresAt: CASE WHEN $expiresAt IS NOT NULL THEN datetime($expiresAt) ELSE NULL END,
            createdAt: datetime()
        })
        CREATE (u)-[:HAS_INSIGHT {
            acknowledged: false,
            acknowledgedAt: NULL
        }]->(hi)
        RETURN hi
        """

        params = {
            "userId": user_id,
            "insightId": insight_id,
            "type": insight_type,
            "title": title,
            "description": description,
            "severity": severity,
            "category": category,
            "confidenceScore": confidence_score,
            "actionable": actionable,
            "recommendations": recommendations or [],
            "dataSources": data_sources or [],
            "status": kwargs.get("status", "active"),
            "expiresAt": expires_at
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["hi"]) if result else None

    def get_health_insight(self, insight_id: str) -> Optional[Dict[str, Any]]:
        """Get health insight by ID."""
        query = """
        MATCH (hi:HealthInsight {insightId: $insightId})
        RETURN hi
        """
        result = self.client.execute_query(query, {"insightId": insight_id})
        return dict(result[0]["hi"]) if result else None

    def get_user_insights(
        self,
        user_id: str,
        insight_type: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all insights for a user with optional filters."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_INSIGHT]->(hi:HealthInsight)
        WHERE hi.status = $status
        AND ($type IS NULL OR hi.type = $type)
        AND ($severity IS NULL OR hi.severity = $severity)
        AND ($category IS NULL OR hi.category = $category)
        AND (hi.expiresAt IS NULL OR hi.expiresAt > datetime())
        RETURN hi, r
        ORDER BY hi.createdAt DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "type": insight_type,
            "severity": severity,
            "category": category,
            "status": status,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{
            "insight": dict(r["hi"]),
            "relationship": dict(r["r"])
        } for r in result]

    def acknowledge_insight(
        self,
        user_id: str,
        insight_id: str,
        feedback: Optional[str] = None
    ) -> bool:
        """Mark an insight as acknowledged by user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_INSIGHT]->(hi:HealthInsight {insightId: $insightId})
        SET r.acknowledged = true,
            r.acknowledgedAt = datetime(),
            r.feedback = $feedback
        RETURN count(r) as updated
        """

        params = {
            "userId": user_id,
            "insightId": insight_id,
            "feedback": feedback
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    def update_insight_status(
        self,
        insight_id: str,
        status: str
    ) -> bool:
        """Update insight status (active, resolved, dismissed)."""
        query = """
        MATCH (hi:HealthInsight {insightId: $insightId})
        SET hi.status = $status,
            hi.updatedAt = datetime()
        RETURN count(hi) as updated
        """

        params = {
            "insightId": insight_id,
            "status": status
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    def delete_insight(self, insight_id: str) -> bool:
        """Delete health insight."""
        query = """
        MATCH (hi:HealthInsight {insightId: $insightId})
        DETACH DELETE hi
        RETURN count(hi) as deleted
        """
        result = self.client.execute_query(query, {"insightId": insight_id})
        return result[0]["deleted"] > 0 if result else False

    # ==================== RiskFactor CRUD ====================

    def create_risk_factor(
        self,
        user_id: str,
        risk_type: str,
        name: str,
        description: str,
        risk_level: str = "medium",
        risk_score: Optional[float] = None,
        contributing_factors: Optional[List[str]] = None,
        mitigation_strategies: Optional[List[str]] = None,
        evidence: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a RiskFactor node and link to User.

        Args:
            user_id: User UUID
            risk_type: Type (disease, lifestyle, genetic, environmental)
            name: Risk factor name
            description: Detailed description
            risk_level: low/medium/high/critical
            risk_score: Numeric risk score (0.0-1.0)
            contributing_factors: List of contributing factors
            mitigation_strategies: List of mitigation strategies
            evidence: Supporting evidence data

        Returns:
            Created risk factor data
        """
        risk_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {userId: $userId})
        CREATE (rf:RiskFactor {
            riskId: $riskId,
            type: $type,
            name: $name,
            description: $description,
            riskLevel: $riskLevel,
            riskScore: $riskScore,
            contributingFactors: $contributingFactors,
            mitigationStrategies: $mitigationStrategies,
            evidence: $evidence,
            status: $status,
            createdAt: datetime()
        })
        CREATE (u)-[:HAS_RISK_FACTOR {
            identifiedAt: datetime(),
            reviewed: false
        }]->(rf)
        RETURN rf
        """

        params = {
            "userId": user_id,
            "riskId": risk_id,
            "type": risk_type,
            "name": name,
            "description": description,
            "riskLevel": risk_level,
            "riskScore": risk_score,
            "contributingFactors": contributing_factors or [],
            "mitigationStrategies": mitigation_strategies or [],
            "evidence": evidence,
            "status": kwargs.get("status", "active")
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["rf"]) if result else None

    def get_risk_factor(self, risk_id: str) -> Optional[Dict[str, Any]]:
        """Get risk factor by ID."""
        query = """
        MATCH (rf:RiskFactor {riskId: $riskId})
        RETURN rf
        """
        result = self.client.execute_query(query, {"riskId": risk_id})
        return dict(result[0]["rf"]) if result else None

    def get_user_risk_factors(
        self,
        user_id: str,
        risk_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: str = "active",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all risk factors for a user with optional filters."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_RISK_FACTOR]->(rf:RiskFactor)
        WHERE rf.status = $status
        AND ($type IS NULL OR rf.type = $type)
        AND ($riskLevel IS NULL OR rf.riskLevel = $riskLevel)
        RETURN rf, r
        ORDER BY rf.riskScore DESC, rf.createdAt DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "type": risk_type,
            "riskLevel": risk_level,
            "status": status,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{
            "risk_factor": dict(r["rf"]),
            "relationship": dict(r["r"])
        } for r in result]

    def mark_risk_reviewed(
        self,
        user_id: str,
        risk_id: str,
        reviewed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Mark a risk factor as reviewed."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_RISK_FACTOR]->(rf:RiskFactor {riskId: $riskId})
        SET r.reviewed = true,
            r.reviewedAt = datetime(),
            r.reviewedBy = $reviewedBy,
            r.reviewNotes = $notes
        RETURN count(r) as updated
        """

        params = {
            "userId": user_id,
            "riskId": risk_id,
            "reviewedBy": reviewed_by,
            "notes": notes
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    def update_risk_level(
        self,
        risk_id: str,
        risk_level: str,
        risk_score: Optional[float] = None
    ) -> bool:
        """Update risk factor level and score."""
        query = """
        MATCH (rf:RiskFactor {riskId: $riskId})
        SET rf.riskLevel = $riskLevel,
            rf.riskScore = CASE WHEN $riskScore IS NOT NULL THEN $riskScore ELSE rf.riskScore END,
            rf.updatedAt = datetime()
        RETURN count(rf) as updated
        """

        params = {
            "riskId": risk_id,
            "riskLevel": risk_level,
            "riskScore": risk_score
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    # ==================== Relationship Operations ====================

    def link_insight_to_condition(
        self,
        insight_id: str,
        condition_id: str
    ) -> bool:
        """Link insight to a specific condition."""
        query = """
        MATCH (hi:HealthInsight {insightId: $insightId})
        MATCH (c:Condition {conditionId: $conditionId})
        MERGE (hi)-[r:RELATED_TO]->(c)
        RETURN count(r) as created
        """

        params = {
            "insightId": insight_id,
            "conditionId": condition_id
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def link_insight_to_medication(
        self,
        insight_id: str,
        medication_id: str
    ) -> bool:
        """Link insight to a specific medication."""
        query = """
        MATCH (hi:HealthInsight {insightId: $insightId})
        MATCH (m:Medication {medicationId: $medicationId})
        MERGE (hi)-[r:RELATED_TO]->(m)
        RETURN count(r) as created
        """

        params = {
            "insightId": insight_id,
            "medicationId": medication_id
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def link_risk_to_condition(
        self,
        risk_id: str,
        condition_id: str,
        probability: Optional[float] = None
    ) -> bool:
        """Link risk factor to a potential condition."""
        query = """
        MATCH (rf:RiskFactor {riskId: $riskId})
        MATCH (c:Condition {conditionId: $conditionId})
        MERGE (rf)-[r:MAY_LEAD_TO {
            probability: $probability,
            createdAt: datetime()
        }]->(c)
        RETURN count(r) as created
        """

        params = {
            "riskId": risk_id,
            "conditionId": condition_id,
            "probability": probability
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    # ==================== Advanced Queries ====================

    def get_critical_insights(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get critical and high severity insights for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_INSIGHT]->(hi:HealthInsight)
        WHERE hi.status = 'active'
        AND hi.severity IN ['high', 'critical']
        AND (hi.expiresAt IS NULL OR hi.expiresAt > datetime())
        AND r.acknowledged = false
        RETURN hi, r
        ORDER BY
            CASE hi.severity
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                ELSE 3
            END,
            hi.createdAt DESC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [{
            "insight": dict(r["hi"]),
            "relationship": dict(r["r"])
        } for r in result]

    def get_high_risk_factors(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get high and critical risk factors for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_RISK_FACTOR]->(rf:RiskFactor)
        WHERE rf.status = 'active'
        AND rf.riskLevel IN ['high', 'critical']
        RETURN rf, r
        ORDER BY
            CASE rf.riskLevel
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                ELSE 3
            END,
            rf.riskScore DESC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [{
            "risk_factor": dict(r["rf"]),
            "relationship": dict(r["r"])
        } for r in result]

    def get_insights_by_category(
        self,
        user_id: str,
        category: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get insights for a specific category."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_INSIGHT]->(hi:HealthInsight)
        WHERE hi.category = $category
        AND hi.status = 'active'
        AND (hi.expiresAt IS NULL OR hi.expiresAt > datetime())
        RETURN hi, r
        ORDER BY hi.createdAt DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "category": category,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{
            "insight": dict(r["hi"]),
            "relationship": dict(r["r"])
        } for r in result]

    def get_family_risk_analysis(
        self,
        family_id: str
    ) -> Dict[str, Any]:
        """Analyze common risk factors across family members."""
        query = """
        MATCH (u:User)-[:MEMBER_OF]->(f:Family {familyId: $familyId})
        MATCH (u)-[:HAS_RISK_FACTOR]->(rf:RiskFactor)
        WHERE rf.status = 'active'
        WITH rf.type as riskType, rf.name as riskName, rf.riskLevel as riskLevel,
             count(DISTINCT u) as affectedMembers,
             collect(DISTINCT u.name) as memberNames,
             avg(rf.riskScore) as avgRiskScore
        WHERE affectedMembers > 1
        RETURN riskType, riskName, riskLevel, affectedMembers, memberNames, avgRiskScore
        ORDER BY affectedMembers DESC, avgRiskScore DESC
        """

        result = self.client.execute_query(query, {"familyId": family_id})
        return [{
            "risk_type": r["riskType"],
            "risk_name": r["riskName"],
            "risk_level": r["riskLevel"],
            "affected_members": r["affectedMembers"],
            "member_names": r["memberNames"],
            "avg_risk_score": r["avgRiskScore"]
        } for r in result]

    def get_actionable_insights(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get actionable insights that user can act upon."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_INSIGHT]->(hi:HealthInsight)
        WHERE hi.actionable = true
        AND hi.status = 'active'
        AND r.acknowledged = false
        AND (hi.expiresAt IS NULL OR hi.expiresAt > datetime())
        RETURN hi, r
        ORDER BY
            CASE hi.severity
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                ELSE 4
            END,
            hi.createdAt DESC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [{
            "insight": dict(r["hi"]),
            "relationship": dict(r["r"])
        } for r in result]

    def get_insight_with_context(
        self,
        insight_id: str
    ) -> Dict[str, Any]:
        """Get insight with all related entities."""
        query = """
        MATCH (hi:HealthInsight {insightId: $insightId})
        OPTIONAL MATCH (u:User)-[:HAS_INSIGHT]->(hi)
        OPTIONAL MATCH (hi)-[:RELATED_TO]->(related)
        RETURN hi, u, collect(DISTINCT related) as relatedEntities
        """

        result = self.client.execute_query(query, {"insightId": insight_id})

        if not result:
            return None

        r = result[0]
        return {
            "insight": dict(r["hi"]),
            "user": dict(r["u"]) if r.get("u") else None,
            "related_entities": [dict(entity) for entity in r["relatedEntities"]] if r.get("relatedEntities") else []
        }
