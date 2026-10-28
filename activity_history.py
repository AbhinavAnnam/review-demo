import datetime
from typing import List, Dict, Any, Optional, Set

class ActivityHistoryImmutableException(Exception):
    pass

class UnauthorizedAuditAccessException(Exception):
    pass

class AccessDeniedException(Exception):
    pass

class ParentResourceNotFoundException(Exception):
    pass

class ActivityRecord:
    def __init__(
        self,
        activity_id: str,
        organization_id: str,
        project_id: Optional[str],
        work_item_id: Optional[str],
        actor_id: Optional[str],
        actor_name: Optional[str],
        action: str,
        details: Dict[str, Any],
        timestamp: datetime.datetime,
        is_system_action: bool = False
    ) -> None:
        self.activity_id = activity_id
        self.organization_id = organization_id
        self.project_id = project_id
        self.work_item_id = work_item_id
        self.actor_id = actor_id
        self.actor_name = actor_name
        self.action = action
        self.details = details
        self.timestamp = timestamp
        self.is_system_action = is_system_action

class ActivityHistoryStore:
    def __init__(self) -> None:
        self._activities: List[ActivityRecord] = []

    def record_activity(
        self,
        organization_id: str,
        project_id: Optional[str],
        work_item_id: Optional[str],
        actor_id: Optional[str],
        actor_name: Optional[str],
        action: str,
        details: Dict[str, Any],
        is_system_action: bool = False
    ) -> ActivityRecord:
        internal_maintenance_actions = {"INDEX_UPDATE", "CACHE_REFRESH", "EMAIL_RETRY"}
        if action in internal_maintenance_actions:
            raise ValueError("Internal database maintenance operations must not appear in the user activity feed.")
        
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        activity_id = f"act_{len(self._activities) + 1}_{int(timestamp.timestamp())}"
        
        record = ActivityRecord(
            activity_id=activity_id,
            organization_id=organization_id,
            project_id=project_id,
            work_item_id=work_item_id,
            actor_id=actor_id,
            actor_name=actor_name,
            action=action,
            details=details,
            timestamp=timestamp,
            is_system_action=is_system_action
        )
        self._activities.append(record)
        return record

    def get_activities(
        self,
        user_id: Optional[str],
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        is_org_admin: bool,
        target_organization_id: str,
        target_project_id: Optional[str] = None,
        target_work_item_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not user_id:
            raise AccessDeniedException("Unauthenticated access via shared or forwarded URLs is strictly forbidden; public sharing links are unsupported.")

        if target_organization_id not in user_org_memberships:
            raise AccessDeniedException("Organization membership required to access history.")

        if target_project_id and target_project_id not in user_project_memberships and not is_org_admin:
            raise AccessDeniedException("Project membership or administrative access required.")

        results: List[Dict[str, Any]] = []
        for activity in self._activities:
            if activity.organization_id != target_organization_id:
                continue
            
            if target_project_id and activity.project_id != target_project_id:
                if not is_org_admin:
                    continue

            if target_work_item_id and activity.work_item_id != target_work_item_id:
                if not is_org_admin:
                    continue

            if not is_org_admin and activity.project_id and activity.project_id not in user_project_memberships:
                continue

            results.append({
                "activity_id": activity.activity_id,
                "organization_id": activity.organization_id,
                "project_id": activity.project_id,
                "work_item_id": activity.work_item_id,
                "actor_id": activity.actor_id,
                "actor_name": activity.actor_name,
                "action": activity.action,
                "details": activity.details,
                "timestamp": activity.timestamp.isoformat(),
                "is_system_action": activity.is_system_action
            })

        return results

    def modify_activity(self, activity_id: str) -> None:
        raise ActivityHistoryImmutableException("Activity records are append-only; ordinary users cannot modify or rewrite activity history by updating current objects.")

def verify_parent_resource_visibility(
    parent_type: str,
    parent_id: str,
    user_org_memberships: Set[str],
    user_project_memberships: Set[str],
    resource_org_id: str,
    resource_project_id: Optional[str]
) -> bool:
    if resource_org_id not in user_org_memberships:
        return False
    if resource_project_id and resource_project_id not in user_project_memberships:
        return False
    return True