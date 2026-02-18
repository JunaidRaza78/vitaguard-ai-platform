"""
Dashboard Operations for Neo4j
Aggregated queries for the Family Health Dashboard.
Provides family-level health overviews, member summaries, and hereditary risk scoring.
"""
from typing import Dict, List, Optional, Any
from shared.database.neo4j.operations.graph_ops import GraphOperations
from shared.logging import get_logger

logger = get_logger('neo4j.dashboard_ops')


class DashboardOperations(GraphOperations):
    """Dashboard-specific database operations for family health overview."""

    def get_family_health_overview(
        self,
        family_id: str,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated health overview for all family members.
        Returns per-member summary: conditions count, medications count, latest vitals.
        """
        try:
            query = """
            MATCH (u:User)-[mem:MEMBER_OF]->(f:Family {familyId: $familyId})
            OPTIONAL MATCH (u)-[hc:HAS_CONDITION]->(c:Condition)
            WHERE hc.status = 'active'
            WITH u, mem, count(DISTINCT c) as conditionCount, collect(DISTINCT c.name) as conditionNames
            OPTIONAL MATCH (u)-[t:TAKES]->(m:Medication)
            WHERE t.status = 'active'
            WITH u, mem, conditionCount, conditionNames,
                 count(DISTINCT m) as medicationCount, collect(DISTINCT m.name) as medicationNames
            RETURN u.userId as userId, u.name as name, u.email as email,
                   mem.role as role,
                   conditionCount, conditionNames,
                   medicationCount, medicationNames
            ORDER BY u.name
            """
            logger.info(f"Getting family health overview for family: {family_id}")
            records = self.execute_query(query, {"familyId": family_id}, database)
            results = []
            for record in records:
                results.append({
                    "userId": record["userId"],
                    "name": record["name"],
                    "email": record["email"],
                    "role": record["role"],
                    "conditionCount": record["conditionCount"],
                    "conditionNames": record["conditionNames"] or [],
                    "medicationCount": record["medicationCount"],
                    "medicationNames": record["medicationNames"] or [],
                    "recentVitals": []
                })
            logger.info(f"Found {len(results)} family members for dashboard")
            return results
        except Exception as e:
            logger.error(f"Failed to get family health overview: {str(e)}")
            raise

    def get_member_health_summary(
        self,
        user_id: str,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed health summary for a single family member.
        Includes conditions with details and active medications with dosage.
        """
        try:
            query = """
            MATCH (u:User {userId: $userId})
            OPTIONAL MATCH (u)-[hc:HAS_CONDITION]->(c:Condition)
            WITH u, collect(CASE WHEN c IS NOT NULL THEN {
                conditionId: c.conditionId,
                name: c.name,
                category: c.category,
                severity: hc.severity,
                status: hc.status,
                diagnosedDate: toString(hc.diagnosedDate)
            } ELSE null END) as rawConditions
            OPTIONAL MATCH (u)-[t:TAKES]->(m:Medication)
            WHERE t.status = 'active'
            WITH u, rawConditions, collect(CASE WHEN m IS NOT NULL THEN {
                medicationId: m.medicationId,
                name: m.name,
                dosage: t.dosage,
                frequency: t.frequency,
                startDate: toString(t.startDate)
            } ELSE null END) as rawMedications
            RETURN u.userId as userId, u.name as name,
                   rawConditions, rawMedications
            """
            logger.info(f"Getting member health summary for user: {user_id}")
            records = self.execute_query(query, {"userId": user_id}, database)
            if not records:
                logger.warning(f"User not found in Neo4j: {user_id}")
                return None
            record = records[0]
            return {
                "userId": record["userId"],
                "name": record["name"],
                "conditions": [c for c in record["rawConditions"] if c is not None and c.get("conditionId")],
                "medications": [m for m in record["rawMedications"] if m is not None and m.get("medicationId")]
            }
        except Exception as e:
            logger.error(f"Failed to get member health summary: {str(e)}")
            raise

    def calculate_hereditary_risk_scores(
        self,
        user_id: str,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate risk scores based on family history using graph traversal.

        Scoring logic:
        - Direct parent with condition: 0.5 base weight
        - Grandparent with condition: 0.25 base weight
        - Both parents with same condition: score doubles
        - Chronic/genetic category conditions: 1.5x multiplier
        - Risk levels: high (>=0.7), moderate (>=0.4), low (<0.4)
        """
        try:
            query = """
            MATCH (user:User {userId: $userId})
            // Find parents and their conditions
            OPTIONAL MATCH (parent:User)-[:PARENT_OF]->(user)
            OPTIONAL MATCH (parent)-[:HAS_CONDITION]->(c:Condition)
            WHERE c IS NOT NULL
            WITH user, c, collect(DISTINCT parent.userId) as parentIds,
                 count(DISTINCT parent) as parentCount,
                 CASE WHEN count(DISTINCT parent) > 0 THEN 0.5 * count(DISTINCT parent) ELSE 0 END as parentScore
            // Find grandparents with same condition
            OPTIONAL MATCH (gp:User)-[:PARENT_OF]->(:User)-[:PARENT_OF]->(user)
            OPTIONAL MATCH (gp)-[:HAS_CONDITION]->(c)
            WITH c, parentScore, parentCount,
                 count(DISTINCT gp) as gpCount
            WHERE c IS NOT NULL AND (parentScore > 0 OR gpCount > 0)
            WITH c,
                 parentScore + (gpCount * 0.25) as baseScore,
                 parentCount
            // Apply multipliers
            WITH c,
                 baseScore * CASE WHEN parentCount > 1 THEN 2.0 ELSE 1.0 END as adjustedScore,
                 CASE WHEN c.category IN ['genetic', 'chronic', 'hereditary'] THEN 1.5 ELSE 1.0 END as categoryMultiplier
            WITH c,
                 adjustedScore * categoryMultiplier as riskScore
            WHERE riskScore > 0
            RETURN c.conditionId as conditionId,
                   c.name as conditionName,
                   c.category as category,
                   c.icdCode as icdCode,
                   riskScore,
                   CASE
                       WHEN riskScore >= 0.7 THEN 'high'
                       WHEN riskScore >= 0.4 THEN 'moderate'
                       ELSE 'low'
                   END as riskLevel
            ORDER BY riskScore DESC
            """
            logger.info(f"Calculating hereditary risk scores for user: {user_id}")
            records = self.execute_query(query, {"userId": user_id}, database)
            results = [
                {
                    "conditionId": r["conditionId"],
                    "conditionName": r["conditionName"],
                    "category": r["category"],
                    "icdCode": r.get("icdCode"),
                    "riskScore": round(float(r["riskScore"]), 3),
                    "riskLevel": r["riskLevel"]
                }
                for r in records
            ]
            logger.info(f"Found {len(results)} hereditary risk factors for user {user_id}")
            return results
        except Exception as e:
            logger.error(f"Failed to calculate hereditary risk scores: {str(e)}")
            raise

    def get_family_condition_heatmap(
        self,
        family_id: str,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a cross-member condition matrix for the family.
        Shows which conditions appear across which members.
        """
        try:
            query = """
            MATCH (u:User)-[:MEMBER_OF]->(f:Family {familyId: $familyId})
            MATCH (u)-[hc:HAS_CONDITION]->(c:Condition)
            RETURN c.name as conditionName, c.category as category,
                   collect(DISTINCT {userId: u.userId, name: u.name, severity: hc.severity, status: hc.status}) as affectedMembers,
                   count(DISTINCT u) as memberCount
            ORDER BY memberCount DESC, c.name
            """
            logger.info(f"Getting condition heatmap for family: {family_id}")
            records = self.execute_query(query, {"familyId": family_id}, database)
            results = [
                {
                    "conditionName": r["conditionName"],
                    "category": r["category"],
                    "affectedMembers": r["affectedMembers"],
                    "memberCount": r["memberCount"]
                }
                for r in records
            ]
            logger.info(f"Found {len(results)} conditions across family members")
            return results
        except Exception as e:
            logger.error(f"Failed to get family condition heatmap: {str(e)}")
            raise
