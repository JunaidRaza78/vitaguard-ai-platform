"""
Dashboard Service
Aggregates data from PostgreSQL (health events) and Neo4j (conditions, medications, risk)
to provide unified dashboard views.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.schemas.dashboard import (
    HealthEventCreate,
    HealthEventResponse,
    MemberHealthOverview,
    FamilyDashboardResponse,
    MemberDetailResponse,
    RiskScoreResponse,
    HereditaryRisk,
    TimelineResponse,
    FamilyConditionHeatmapResponse,
    ConditionHeatmapEntry,
    ConditionDetail,
    MedicationDetail,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for family health dashboard operations."""

    # ==================== Health Event CRUD (PostgreSQL) ====================

    def create_health_event(
        self, user_id: str, event_data: HealthEventCreate
    ) -> Optional[HealthEventResponse]:
        """Create a health event in PostgreSQL."""
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import HealthEvent

        try:
            with PostgresClient() as db:
                session = db.get_session()
                event = HealthEvent(
                    event_id=str(uuid.uuid4()),
                    user_id=user_id,
                    event_type=event_data.event_type.value,
                    title=event_data.title,
                    description=event_data.description,
                    event_date=event_data.event_date,
                    provider_name=event_data.provider_name,
                    location=event_data.location,
                    event_data=event_data.event_data,
                    severity=event_data.severity.value if event_data.severity else None,
                )
                session.add(event)
                session.commit()
                session.refresh(event)
                logger.info(f"Created health event {event.event_id} for user {user_id}")
                return self._event_to_response(event)
        except Exception as e:
            logger.error(f"Error creating health event: {e}")
            return None

    def get_user_timeline(
        self,
        user_id: str,
        event_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TimelineResponse:
        """Get chronological health event timeline for a user from PostgreSQL."""
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import HealthEvent

        try:
            with PostgresClient() as db:
                session = db.get_session()
                query = session.query(HealthEvent).filter(HealthEvent.user_id == user_id)

                if event_types:
                    query = query.filter(HealthEvent.event_type.in_(event_types))
                if start_date:
                    query = query.filter(HealthEvent.event_date >= start_date)
                if end_date:
                    query = query.filter(HealthEvent.event_date <= end_date)

                total = query.count()
                events = (
                    query.order_by(HealthEvent.event_date.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                return TimelineResponse(
                    user_id=user_id,
                    events=[self._event_to_response(e) for e in events],
                    total=total,
                    has_more=(offset + limit) < total,
                )
        except Exception as e:
            logger.error(f"Error getting user timeline: {e}")
            return TimelineResponse(user_id=user_id, events=[], total=0, has_more=False)

    # ==================== Family Dashboard (Neo4j + PG) ====================

    def get_family_dashboard(self, family_id: str) -> FamilyDashboardResponse:
        """
        Get aggregated family health dashboard.
        Pulls member overview from Neo4j (conditions, meds).
        """
        from shared.database.neo4j.operations.dashboard_ops import DashboardOperations
        from shared.database.neo4j.operations.family_ops import FamilyOperations

        try:
            family_ops = FamilyOperations()
            family = family_ops.get_family_by_id(family_id)
            family_name = family.get("name") if family else None

            dashboard_ops = DashboardOperations()
            members_data = dashboard_ops.get_family_health_overview(family_id)

            members = [MemberHealthOverview(**m) for m in members_data]

            return FamilyDashboardResponse(
                family_id=family_id,
                family_name=family_name,
                members=members,
                total_members=len(members),
            )
        except Exception as e:
            logger.error(f"Error getting family dashboard: {e}")
            return FamilyDashboardResponse(
                family_id=family_id, members=[], total_members=0
            )

    def get_member_detail(self, user_id: str) -> Optional[MemberDetailResponse]:
        """
        Get detailed health info for one family member.
        Combines Neo4j (conditions, medications) with PG (recent events).
        """
        from shared.database.neo4j.operations.dashboard_ops import DashboardOperations

        try:
            dashboard_ops = DashboardOperations()
            summary = dashboard_ops.get_member_health_summary(user_id)

            if not summary:
                return None

            # Get recent health events from PG
            timeline = self.get_user_timeline(user_id, limit=10)

            return MemberDetailResponse(
                userId=summary["userId"],
                name=summary["name"],
                conditions=[ConditionDetail(**c) for c in summary["conditions"]],
                medications=[MedicationDetail(**m) for m in summary["medications"]],
                recentEvents=timeline.events,
            )
        except Exception as e:
            logger.error(f"Error getting member detail: {e}")
            return None

    # ==================== Risk Scoring (Neo4j) ====================

    def get_hereditary_risk_scores(self, user_id: str) -> RiskScoreResponse:
        """
        Calculate hereditary risk scores using Neo4j graph traversal.
        Traverses PARENT_OF relationships to find conditions in ancestors.
        """
        from shared.database.neo4j.operations.dashboard_ops import DashboardOperations

        try:
            dashboard_ops = DashboardOperations()
            risks_data = dashboard_ops.calculate_hereditary_risk_scores(user_id)

            risks = [HereditaryRisk(**r) for r in risks_data]

            # Determine overall risk level
            if any(r.riskLevel == "high" for r in risks):
                overall = "high"
            elif any(r.riskLevel == "moderate" for r in risks):
                overall = "moderate"
            elif risks:
                overall = "low"
            else:
                overall = "none"

            # Get user name from Neo4j
            user_node = dashboard_ops.get_node("User", "userId", user_id)
            user_name = user_node.get("name") if user_node else None

            return RiskScoreResponse(
                user_id=user_id,
                user_name=user_name,
                risks=risks,
                overall_risk_level=overall,
                generated_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error calculating risk scores: {e}")
            return RiskScoreResponse(
                user_id=user_id,
                risks=[],
                overall_risk_level="unknown",
                generated_at=datetime.now(timezone.utc),
            )

    def get_family_condition_heatmap(
        self, family_id: str
    ) -> FamilyConditionHeatmapResponse:
        """Get condition distribution across family members."""
        from shared.database.neo4j.operations.dashboard_ops import DashboardOperations

        try:
            dashboard_ops = DashboardOperations()
            data = dashboard_ops.get_family_condition_heatmap(family_id)

            return FamilyConditionHeatmapResponse(
                family_id=family_id,
                conditions=[ConditionHeatmapEntry(**c) for c in data],
            )
        except Exception as e:
            logger.error(f"Error getting condition heatmap: {e}")
            return FamilyConditionHeatmapResponse(family_id=family_id, conditions=[])

    # ==================== Helpers ====================

    @staticmethod
    def _event_to_response(event) -> HealthEventResponse:
        return HealthEventResponse(
            event_id=str(event.event_id),
            user_id=str(event.user_id),
            event_type=event.event_type,
            title=event.title,
            description=event.description,
            event_date=event.event_date,
            provider_name=event.provider_name,
            location=event.location,
            event_data=event.event_data,
            severity=event.severity,
            created_at=event.created_at,
        )


# Singleton instance
dashboard_service = DashboardService()
