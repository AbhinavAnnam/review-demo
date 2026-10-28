import datetime
import uuid
from typing import List, Dict, Any, Optional, Set, Tuple

class ProjectNotFoundException(Exception):
    pass

class ProjectAccessDeniedException(Exception):
    pass

class ProjectDeletionConstraintException(Exception):
    pass

class ProjectMembershipNotFoundException(Exception):
    pass

class LastProjectOwnerRemovalException(Exception):
    pass

class WorkItemNotFoundException(Exception):
    pass

class InvalidStatusTransitionException(Exception):
    pass

class InvalidPriorityException(Exception):
    pass

class MalformedIdentifierException(Exception):
    pass

class InvalidWorkItemStateException(Exception):
    pass

class CrossOrganizationAccessException(Exception):
    pass


class Project:
    def __init__(
        self,
        project_id: str,
        organization_id: str,
        name: str,
        description: Optional[str],
        creator_id: str,
        owner_id: str,
        status: str = "active",
        due_date: Optional[str] = None,
        archived: bool = False
    ) -> None:
        self.project_id = project_id
        self.organization_id = organization_id
        self.name = name
        self.description = description or ""
        self.creator_id = creator_id
        self.owner_id = owner_id
        self.status = status
        self.due_date = due_date
        self.archived = archived
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.version = 1
        self.members: Set[str] = {owner_id, creator_id}


class WorkItem:
    def __init__(
        self,
        work_item_id: str,
        project_id: str,
        organization_id: str,
        title: str,
        status: str = "uncompleted",
        description: Optional[str] = None,
        priority: str = "medium",
        creator_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        due_date: Optional[str] = None,
        order_index: int = 0
    ) -> None:
        valid_priorities = {"low", "medium", "high", "urgent"}
        if priority not in valid_priorities:
            raise InvalidPriorityException(f"Invalid priority: {priority}")

        valid_statuses = {"uncompleted", "in_progress", "completed", "archived", "closed"}
        if status not in valid_statuses:
            raise InvalidWorkItemStateException(f"Invalid work item status: {status}")

        self.work_item_id = work_item_id
        self.project_id = project_id
        self.organization_id = organization_id
        self.title = title
        self.status = status
        self.description = description or ""
        self.priority = priority
        self.creator_id = creator_id
        self.assignee_id = assignee_id
        self.due_date = due_date
        self.order_index = order_index
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.version = 1


class ProjectMembershipManager:
    def __init__(self) -> None:
        self.projects: Dict[str, Project] = {}
        self.work_items: Dict[str, WorkItem] = {}
        self.activity_log: List[Dict[str, Any]] = []

    def _validate_id(self, identifier: Optional[str]) -> str:
        if not identifier or not isinstance(identifier, str) or len(identifier.strip()) == 0:
            raise MalformedIdentifierException("Identifier is malformed or missing.")
        return identifier.strip()

    def create_project(
        self,
        organization_id: str,
        user_id: str,
        user_org_memberships: Set[str],
        name: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        org_id = self._validate_id(organization_id)
        creator_id = self._validate_id(user_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("User is not a member of the target organization.")

        if not name or not name.strip():
            raise MalformedIdentifierException("Project name is required.")

        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        project = Project(
            project_id=project_id,
            organization_id=org_id,
            name=name.strip(),
            description=description,
            creator_id=creator_id,
            owner_id=creator_id,
            due_date=due_date
        )

        self.projects[project_id] = project

        activity = {
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "project_id": project_id,
            "actor_id": creator_id,
            "action": "CREATE_PROJECT",
            "details": {"name": project.name},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.activity_log.append(activity)

        return {
            "project_id": project.project_id,
            "organization_id": project.organization_id,
            "name": project.name,
            "description": project.description,
            "creator_id": project.creator_id,
            "owner_id": project.owner_id,
            "status": project.status,
            "due_date": project.due_date,
            "archived": project.archived,
            "members": list(project.members),
            "created_at": project.created_at,
            "version": project.version
        }

    def get_project(
        self,
        project_id: str,
        organization_id: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        is_org_admin: bool
    ) -> Dict[str, Any]:
        p_id = self._validate_id(project_id)
        org_id = self._validate_id(organization_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Organization access denied.")

        project = self.projects.get(p_id)
        if not project or project.organization_id != org_id:
            raise ProjectNotFoundException("Project not found.")

        if p_id not in user_project_memberships and not is_org_admin:
            raise ProjectAccessDeniedException("Access to project denied.")

        return {
            "project_id": project.project_id,
            "organization_id": project.organization_id,
            "name": project.name,
            "description": project.description,
            "creator_id": project.creator_id,
            "owner_id": project.owner_id,
            "status": project.status,
            "due_date": project.due_date,
            "archived": project.archived,
            "members": list(project.members),
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "version": project.version
        }

    def update_project(
        self,
        project_id: str,
        organization_id: str,
        actor_id: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        is_org_admin: bool,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        due_date: Optional[str] = None,
        archived: Optional[bool] = None,
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        p_id = self._validate_id(project_id)
        org_id = self._validate_id(organization_id)
        actor = self._validate_id(actor_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Organization mismatch.")

        project = self.projects.get(p_id)
        if not project or project.organization_id != org_id:
            raise ProjectNotFoundException("Project not found.")

        if expected_version is not None and project.version != expected_version:
            raise ProjectAccessDeniedException("Stale data detected: version mismatch. Please reload and retry.")

        is_owner = project.owner_id == actor
        if not is_org_admin and not is_owner and p_id not in user_project_memberships:
            raise ProjectAccessDeniedException("Insufficient permissions to update project.")

        if name is not None:
            if not name.strip():
                raise MalformedIdentifierException("Project name cannot be empty.")
            project.name = name.strip()
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status
        if due_date is not None:
            project.due_date = due_date if due_date != "" else None
        if archived is not None:
            project.archived = archived

        project.version += 1
        project.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self.activity_log.append({
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "project_id": p_id,
            "actor_id": actor,
            "action": "UPDATE_PROJECT",
            "details": {"name": project.name, "status": project.status},
            "timestamp": project.updated_at
        })

        return {
            "project_id": project.project_id,
            "organization_id": project.organization_id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "due_date": project.due_date,
            "archived": project.archived,
            "updated_at": project.updated_at,
            "version": project.version
        }

    def delete_project(
        self,
        project_id: str,
        organization_id: str,
        actor_id: str,
        user_org_memberships: Set[str],
        is_org_admin: bool
    ) -> None:
        p_id = self._validate_id(project_id)
        org_id = self._validate_id(organization_id)
        actor = self._validate_id(actor_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Unauthorized org access.")

        project = self.projects.get(p_id)
        if not project or project.organization_id != org_id:
            raise ProjectNotFoundException("Project not found.")

        if not is_org_admin and project.owner_id != actor:
            raise ProjectAccessDeniedException("Only project owners or organization admins can delete projects.")

        associated_items = [item for item in self.work_items.values() if item.project_id == p_id]
        if associated_items and not project.archived:
            raise ProjectDeletionConstraintException("Cannot permanently delete a project containing active work items without prior archival or cleanup.")

        for item_id in [item.work_item_id for item in associated_items]:
            del self.work_items[item_id]

        del self.projects[p_id]

        self.activity_log.append({
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "project_id": p_id,
            "actor_id": actor,
            "action": "DELETE_PROJECT",
            "details": {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def add_project_member(
        self,
        project_id: str,
        organization_id: str,
        actor_id: str,
        target_user_id: str,
        target_user_org_memberships: Set[str],
        user_org_memberships: Set[str],
        is_org_admin: bool
    ) -> None:
        p_id = self._validate_id(project_id)
        org_id = self._validate_id(organization_id)
        actor = self._validate_id(actor_id)
        target = self._validate_id(target_user_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Unauthorized organization context.")

        if target not in target_user_org_memberships or org_id not in target_user_org_memberships:
            raise CrossOrganizationAccessException("Target user is not a member of the organization and cannot be added to the project.")

        project = self.projects.get(p_id)
        if not project or project.organization_id != org_id:
            raise ProjectNotFoundException("Project not found.")

        if not is_org_admin and project.owner_id != actor:
            raise ProjectAccessDeniedException("Only project owners or organization admins can add members.")

        project.members.add(target)

        self.activity_log.append({
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "project_id": p_id,
            "actor_id": actor,
            "action": "ADD_PROJECT_MEMBER",
            "details": {"target_user_id": target},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def remove_project_member(
        self,
        project_id: str,
        organization_id: str,
        actor_id: str,
        target_user_id: str,
        user_org_memberships: Set[str],
        is_org_admin: bool
    ) -> None:
        p_id = self._validate_id(project_id)
        org_id = self._validate_id(organization_id)
        actor = self._validate_id(actor_id)
        target = self._validate_id(target_user_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Unauthorized organization context.")

        project = self.projects.get(p_id)
        if not project or project.organization_id != org_id:
            raise ProjectNotFoundException("Project not found.")

        if not is_org_admin and project.owner_id != actor:
            raise ProjectAccessDeniedException("Insufficient permissions to remove project members.")

        if target not in project.members:
            raise ProjectMembershipNotFoundException("Target user is not a member of this project.")

        if target == project.owner_id:
            other_owners = [m for m in project.members if m != target]
            if not other_owners:
                raise LastProjectOwnerRemovalException("Cannot remove the sole project owner without assigning a new owner first.")

        project.members.remove(target)

        self.activity_log.append({
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "project_id": p_id,
            "actor_id": actor,
            "action": "REMOVE_PROJECT_MEMBER",
            "details": {"target_user_id": target},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def create_work_item(
        self,
        project_id: str,
        organization_id: str,
        actor_id: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        is_org_admin: bool,
        title: str,
        status: str = "uncompleted",
        description: Optional[str] = None,
        priority: str = "medium",
        assignee_id: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        p_id = self._validate_id(project_id)
        org_id = self._validate_id(organization_id)
        actor = self._validate_id(actor_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Organization context mismatch.")

        project = self.projects.get(p_id)
        if not project or project.organization_id != org_id:
            raise ProjectNotFoundException("Project not found.")

        if not is_org_admin and p_id not in user_project_memberships:
            raise ProjectAccessDeniedException("User lacks project access to create work items.")

        if not title or not title.strip():
            raise MalformedIdentifierException("Work item title is required.")

        if assignee_id and assignee_id not in project.members:
            raise ProjectAccessDeniedException("Assignee must be a member of the project.")

        work_item_id = f"wi_{uuid.uuid4().hex[:12]}"
        item = WorkItem(
            work_item_id=work_item_id,
            project_id=p_id,
            organization_id=org_id,
            title=title.strip(),
            status=status,
            description=description,
            priority=priority,
            creator_id=actor,
            assignee_id=assignee_id,
            due_date=due_date
        )

        self.work_items[work_item_id] = item

        self.activity_log.append({
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "project_id": p_id,
            "work_item_id": work_item_id,
            "actor_id": actor,
            "action": "CREATE_WORK_ITEM",
            "details": {"title": item.title, "status": item.status, "assignee_id": item.assignee_id},
            "timestamp": item.created_at
        })

        return {
            "work_item_id": item.work_item_id,
            "project_id": item.project_id,
            "organization_id": item.organization_id,
            "title": item.title,
            "status": item.status,
            "description": item.description,
            "priority": item.priority,
            "creator_id": item.creator_id,
            "assignee_id": item.assignee_id,
            "due_date": item.due_date,
            "order_index": item.order_index,
            "created_at": item.created_at,
            "version": item.version
        }

    def update_work_item(
        self,
        work_item_id: str,
        organization_id: str,
        actor_id: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        is_org_admin: bool,
        title: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[str] = None,
        due_date: Optional[str] = None,
        order_index: Optional[int] = None,
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        w_id = self._validate_id(work_item_id)
        org_id = self._validate_id(organization_id)
        actor = self._validate_id(actor_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Organization validation failed.")

        item = self.work_items.get(w_id)
        if not item or item.organization_id != org_id:
            raise WorkItemNotFoundException("Work item not found.")

        if expected_version is not None and item.version != expected_version:
            raise ProjectAccessDeniedException("Stale data detected: work item version mismatch.")

        project = self.projects.get(item.project_id)
        if not project:
            raise ProjectNotFoundException("Associated project not found.")

        if not is_org_admin and item.project_id not in user_project_memberships:
            raise ProjectAccessDeniedException("Access denied to update work item.")

        if title is not None:
            if not title.strip():
                raise MalformedIdentifierException("Work item title cannot be empty.")
            item.title = title.strip()
        if status is not None:
            valid_statuses = {"uncompleted", "in_progress", "completed", "archived", "closed"}
            if status not in valid_statuses:
                raise InvalidWorkItemStateException(f"Invalid status value: {status}")
            item.status = status
        if description is not None:
            item.description = description
        if priority is not None:
            valid_priorities = {"low", "medium", "high", "urgent"}
            if priority not in valid_priorities:
                raise InvalidPriorityException(f"Invalid priority: {priority}")
            item.priority = priority
        if assignee_id is not None:
            if assignee_id != "" and assignee_id not in project.members:
                raise ProjectAccessDeniedException("Assignee must be a project member.")
            item.assignee_id = assignee_id if assignee_id != "" else None
        if due_date is not None:
            item.due_date = due_date if due_date != "" else None
        if order_index is not None:
            item.order_index = order_index

        item.version += 1
        item.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self.activity_log.append({
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,
            "project_id": item.project_id,
            "work_item_id": w_id,
            "actor_id": actor,
            "action": "UPDATE_WORK_ITEM",
            "details": {"title": item.title, "status": item.status, "assignee_id": item.assignee_id},
            "timestamp": item.updated_at
        })

        return {
            "work_item_id": item.work_item_id,
            "project_id": item.project_id,
            "organization_id": item.organization_id,
            "title": item.title,
            "status": item.status,
            "description": item.description,
            "priority": item.priority,
            "creator_id": item.creator_id,
            "assignee_id": item.assignee_id,
            "due_date": item.due_date,
            "order_index": item.order_index,
            "updated_at": item.updated_at,
            "version": item.version
        }

    def get_work_items(
        self,
        project_id: str,
        organization_id: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        is_org_admin: bool,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        p_id = self._validate_id(project_id)
        org_id = self._validate_id(organization_id)

        if org_id not in user_org_memberships:
            raise CrossOrganizationAccessException("Unauthorized organization context.")

        project = self.projects.get(p_id)
        if not project or project.organization_id != org_id:
            raise ProjectNotFoundException("Project not found.")

        if not is_org_admin and p_id not in user_project_memberships:
            raise ProjectAccessDeniedException("Access to project items denied.")

        items = [item for item in self.work_items.values() if item.project_id == p_id]
        items.sort(key=lambda x: (x.order_index, x.work_item_id))

        if offset is not None and offset > 0:
            items = items[offset:]
        if limit is not None and limit >= 0:
            items = items[:limit]

        return [
            {
                "work_item_id": item.work_item_id,
                "project_id": item.project_id,
                "organization_id": item.organization_id,
                "title": item.title,
                "status": item.status,
                "description": item.description,
                "priority": item.priority,
                "creator_id": item.creator_id,
                "assignee_id": item.assignee_id,
                "due_date": item.due_date,
                "order_index": item.order_index,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "version": item.version
            }
            for item in items
        ]