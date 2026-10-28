import datetime
import html
import os
import uuid
from typing import Dict, List, Optional, Set, Union, Any

# ----------------------------------------------------------------------
# Exception definitions
# ----------------------------------------------------------------------
class WorkItemNotFoundError(Exception):
    """Raised when a work item cannot be found."""
    pass

class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

class MalformedIdentifierError(Exception):
    """Raised when an identifier is malformed."""
    pass

class InvalidParameterError(Exception):
    """Raised when a parameter is invalid."""
    pass

class ResourceAccessDeniedError(Exception):
    """Raised when a user does not have permission to access a resource."""
    pass

class CommentModerationError(Exception):
    """Raised when a moderator action on a comment fails."""
    pass

class CommentNotFoundError(Exception):
    """Raised when a comment cannot be found."""
    pass

class FileSizeLimitExceededError(Exception):
    """Raised when an uploaded file exceeds the allowed size."""
    pass

class AttachmentNotFoundError(Exception):
    """Raised when an attachment cannot be found."""
    pass

class LargeFileRejectedException(Exception):
    """Raised when a file is too large to be accepted."""
    pass

class UnauthorizedAttachmentAccessException(Exception):
    """Raised when a user attempts to access an attachment without permission."""
    pass

class AttachmentNotFoundException(Exception):
    """Raised when an attachment cannot be found."""
    pass

# ----------------------------------------------------------------------
# Basic domain models
# ----------------------------------------------------------------------
class Organization:
    def __init__(self, org_id: str, name: str):
        self.org_id = org_id
        self.name = name
        self.projects: Dict[str, 'Project'] = {}

class Project:
    def __init__(self, project_id: str, org: Organization, name: str):
        self.project_id = project_id
        self.org = org
        self.name = name
        self.members: Set[str] = set()  # user ids
        self.work_items: Dict[str, 'WorkItem'] = {}

class User:
    def __init__(self, user_id: str, org: Organization, is_admin: bool = False):
        self.user_id = user_id
        self.org = org
        self.is_admin = is_admin

# ----------------------------------------------------------------------
# Historical Activity Record Store (In-Memory for demonstration/audit)
# ----------------------------------------------------------------------
class ActivityRecord:
    def __init__(
        self,
        activity_id: str,
        organization_id: str,
        project_id: Optional[str],
        work_item_id: Optional[str],
        actor_id: Optional[str],
        action: str,
        details: Dict[str, Any],
        timestamp: datetime.datetime,
    ):
        self.activity_id = activity_id
        self.organization_id = organization_id
        self.project_id = project_id
        self.work_item_id = work_item_id
        self.actor_id = actor_id
        self.action = action
        self.details = details
        self.timestamp = timestamp

activity_logs: List[ActivityRecord] = []

def _record_activity(
    org_id: str,
    project_id: Optional[str],
    work_item_id: Optional[str],
    actor_id: Optional[str],
    action: str,
    details: Dict[str, Any],
) -> None:
    record = ActivityRecord(
        activity_id=str(uuid.uuid4()),
        organization_id=org_id,
        project_id=project_id,
        work_item_id=work_item_id,
        actor_id=actor_id,
        action=action,
        details=details,
        timestamp=datetime.datetime.utcnow(),
    )
    activity_logs.append(record)

# ----------------------------------------------------------------------
# Work item related classes
# ----------------------------------------------------------------------
class WorkItem:
    VALID_STATES = {"not_yet_completed", "in_progress", "completed"}

    def __init__(
        self,
        item_id: str,
        project: Project,
        title: str,
        status: str,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        creator: User = None,
        assignee: Optional[User] = None,
        due_date: Optional[datetime.date] = None,
    ):
        if status not in self.VALID_STATES:
            raise InvalidStateTransitionError(f"Invalid initial state: {status}")
        self.item_id = item_id
        self.project = project
        self.title = title
        self.status = status
        self.description = description
        self.priority = priority
        self.creator = creator
        self.assignee = assignee
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = self.created_at
        self.due_date = due_date
        self.comments: Dict[str, 'Comment'] = {}
        self.attachments: Dict[str, 'Attachment'] = {}
        self.reorder_index = 0  # simple integer for ordering

    def update(
        self,
        user: User,
        title: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        assignee: Optional[User] = None,
        due_date: Optional[datetime.date] = None,
    ) -> None:
        if user.org.org_id != self.project.org.org_id:
            raise ResourceAccessDeniedError("Cross-organization access unauthorized")
        if user.user_id not in self.project.members and not user.is_admin:
            raise ResourceAccessDeniedError("User not a member of the project")

        changes = {}
        if title is not None and title != self.title:
            changes["title"] = {"old": self.title, "new": title}
            self.title = title

        if status is not None and status != self.status:
            if status not in self.VALID_STATES:
                raise InvalidStateTransitionError(f"Invalid status: {status}")
            changes["status"] = {"old": self.status, "new": status}
            self.status = status

        if description is not None:
            self.description = description

        if priority is not None:
            self.priority = priority

        if assignee is not None:
            if assignee.org.org_id != self.project.org.org_id:
                raise ResourceAccessDeniedError("Assignee belongs to another organization")
            if assignee.user_id not in self.project.members:
                raise InvalidParameterError("Assignee must be a project member")
            old_assignee_id = self.assignee.user_id if self.assignee else None
            new_assignee_id = assignee.user_id
            if old_assignee_id != new_assignee_id:
                changes["assignee"] = {"old": old_assignee_id, "new": new_assignee_id}
            self.assignee = assignee

        if due_date is not None:
            self.due_date = due_date

        self.updated_at = datetime.datetime.utcnow()

        if changes:
            _record_activity(
                org_id=self.project.org.org_id,
                project_id=self.project.project_id,
                work_item_id=self.item_id,
                actor_id=user.user_id,
                action="UPDATE_WORK_ITEM",
                details=changes,
            )

    def remove_due_date(self, user: User) -> None:
        if user.org.org_id != self.project.org.org_id:
            raise ResourceAccessDeniedError("Cross-organization access unauthorized")
        if user.user_id not in self.project.members and not user.is_admin:
            raise ResourceAccessDeniedError("User not a member of the project")
        self.due_date = None
        self.updated_at = datetime.datetime.utcnow()
        _record_activity(
            org_id=self.project.org.org_id,
            project_id=self.project.project_id,
            work_item_id=self.item_id,
            actor_id=user.user_id,
            action="REMOVE_DUE_DATE",
            details={},
        )

    def reorder(self, new_index: int) -> None:
        self.reorder_index = new_index

# ----------------------------------------------------------------------
# Comment related classes
# ----------------------------------------------------------------------
class Comment:
    def __init__(self, comment_id: str, work_item: WorkItem, author: User, body: str):
        self.comment_id = comment_id
        self.work_item = work_item
        self.author = author
        # Safely escape stored body to prevent cross-site scripting
        self.body = html.escape(body)
        self.created_at = datetime.datetime.utcnow()
        self.edited_at: Optional[datetime.datetime] = None
        self.deleted = False

    def edit(self, user: User, new_body: str) -> None:
        if user.org.org_id != self.work_item.project.org.org_id:
            raise ResourceAccessDeniedError("Cross-organization access unauthorized")
        if user.user_id != self.author.user_id and not user.is_admin:
            raise ResourceAccessDeniedError("Only author or admin can edit comment")
        self.body = html.escape(new_body)
        self.edited_at = datetime.datetime.utcnow()
        _record_activity(
            org_id=self.work_item.project.org.org_id,
            project_id=self.work_item.project.project_id,
            work_item_id=self.work_item.item_id,
            actor_id=user.user_id,
            action="EDIT_COMMENT",
            details={"comment_id": self.comment_id},
        )

    def delete(self, user: User) -> None:
        if user.org.org_id != self.work_item.project.org.org_id:
            raise ResourceAccessDeniedError("Cross-organization access unauthorized")
        if user.user_id != self.author.user_id and not user.is_admin:
            raise ResourceAccessDeniedError("Only author or admin can delete comment")
        self.deleted = True
        self.edited_at = datetime.datetime.utcnow()
        _record_activity(
            org_id=self.work_item.project.org.org_id,
            project_id=self.work_item.project.project_id,
            work_item_id=self.work_item.item_id,
            actor_id=user.user_id,
            action="DELETE_COMMENT",
            details={"comment_id": self.comment_id},
        )

# ----------------------------------------------------------------------
# Attachment related classes
# ----------------------------------------------------------------------
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

class Attachment:
    def __init__(
        self,
        attachment_id: str,
        work_item: WorkItem,
        uploader: User,
        filename: str,
        storage_id: str,
        size_bytes: int,
        comment: Optional[Comment] = None,
    ):
        if size_bytes > MAX_FILE_SIZE_BYTES:
            raise FileSizeLimitExceededError("File size exceeds maximum allowed")
        self.attachment_id = attachment_id
        self.work_item = work_item
        self.uploader = uploader
        # Sanitize filename to prevent path traversal issues
        self.filename = os.path.basename(filename)
        self.storage_id = storage_id
        self.size_bytes = size_bytes
        self.comment = comment
        self.created_at = datetime.datetime.utcnow()
        self.deleted = False

    def delete(self, user: User) -> None:
        if user.org.org_id != self.work_item.project.org.org_id:
            raise ResourceAccessDeniedError("Cross-organization access unauthorized")
        if user.user_id != self.uploader.user_id and not user.is_admin:
            raise ResourceAccessDeniedError("Only uploader or admin can delete attachment")
        self.deleted = True
        _record_activity(
            org_id=self.work_item.project.org.org_id,
            project_id=self.work_item.project.project_id,
            work_item_id=self.work_item.item_id,
            actor_id=user.user_id,
            action="DELETE_ATTACHMENT",
            details={"attachment_id": self.attachment_id, "filename": self.filename},
        )

# ----------------------------------------------------------------------
# In-memory storage for demo purposes
# ----------------------------------------------------------------------
organizations: Dict[str, Organization] = {}
users: Dict[str, User] = {}
projects: Dict[str, Project] = {}
work_items: Dict[str, WorkItem] = {}
comments: Dict[str, Comment] = {}
attachments: Dict[str, Attachment] = {}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _validate_uuid(identifier: str) -> None:
    try:
        uuid.UUID(identifier)
    except ValueError:
        raise MalformedIdentifierError(f"Identifier {identifier} is not a valid UUID")

def _get_user(user_id: str) -> User:
    _validate_uuid(user_id)
    if user_id not in users:
        raise InvalidParameterError("User does not exist")
    return users[user_id]

def _get_project(project_id: str) -> Project:
    _validate_uuid(project_id)
    if project_id not in projects:
        raise InvalidParameterError("Project does not exist")
    return projects[project_id]

def _get_work_item(item_id: str) -> WorkItem:
    _validate_uuid(item_id)
    if item_id not in work_items:
        raise WorkItemNotFoundError("Work item not found")
    return work_items[item_id]

def _get_comment(comment_id: str) -> Comment:
    _validate_uuid(comment_id)
    if comment_id not in comments:
        raise CommentNotFoundError("Comment not found")
    return comments[comment_id]

def _get_attachment(attachment_id: str) -> Attachment:
    _validate_uuid(attachment_id)
    if attachment_id not in attachments:
        raise AttachmentNotFoundError("Attachment not found")
    return attachments[attachment_id]

# ----------------------------------------------------------------------
# Public API functions
# ----------------------------------------------------------------------
def create_work_item(
    user_id: str,
    project_id: str,
    title: str,
    status: str,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    assignee_id: Optional[str] = None,
    due_date: Optional[datetime.date] = None,
) -> WorkItem:
    user = _get_user(user_id)
    project = _get_project(project_id)
    
    if user.org.org_id != project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    if user.user_id not in project.members and not user.is_admin:
        raise ResourceAccessDeniedError("User not a member of the project")
        
    assignee = None
    if assignee_id:
        assignee = _get_user(assignee_id)
        if assignee.org.org_id != project.org.org_id:
            raise ResourceAccessDeniedError("Assignee belongs to another organization")
        if assignee.user_id not in project.members:
            raise InvalidParameterError("Assignee must be a project member")
            
    item_id = str(uuid.uuid4())
    work_item = WorkItem(
        item_id=item_id,
        project=project,
        title=title,
        status=status,
        description=description,
        priority=priority,
        creator=user,
        assignee=assignee,
        due_date=due_date,
    )
    project.work_items[item_id] = work_item
    work_items[item_id] = work_item
    
    _record_activity(
        org_id=project.org.org_id,
        project_id=project.project_id,
        work_item_id=item_id,
        actor_id=user.user_id,
        action="CREATE_WORK_ITEM",
        details={"title": title, "status": status},
    )
    return work_item

def update_work_item(
    user_id: str,
    item_id: str,
    title: Optional[str] = None,
    status: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    assignee_id: Optional[str] = None,
    due_date: Optional[datetime.date] = None,
) -> None:
    user = _get_user(user_id)
    work_item = _get_work_item(item_id)
    
    if user.org.org_id != work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
        
    assignee = None
    if assignee_id:
        assignee = _get_user(assignee_id)
        
    work_item.update(
        user=user,
        title=title,
        status=status,
        description=description,
        priority=priority,
        assignee=assignee,
        due_date=due_date,
    )

def remove_due_date(user_id: str, item_id: str) -> None:
    user = _get_user(user_id)
    work_item = _get_work_item(item_id)
    if user.org.org_id != work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    work_item.remove_due_date(user)

def reorder_work_item(user_id: str, item_id: str, new_index: int) -> None:
    user = _get_user(user_id)
    work_item = _get_work_item(item_id)
    if user.org.org_id != work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    if user.user_id not in work_item.project.members and not user.is_admin:
        raise ResourceAccessDeniedError("User not a member of the project")
    work_item.reorder(new_index)

def add_comment(
    user_id: str,
    item_id: str,
    body: str,
) -> Comment:
    user = _get_user(user_id)
    work_item = _get_work_item(item_id)
    if user.org.org_id != work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    if user.user_id not in work_item.project.members and not user.is_admin:
        raise ResourceAccessDeniedError("User not a member of the project")
    comment_id = str(uuid.uuid4())
    comment = Comment(comment_id=comment_id, work_item=work_item, author=user, body=body)
    work_item.comments[comment_id] = comment
    comments[comment_id] = comment
    
    _record_activity(
        org_id=work_item.project.org.org_id,
        project_id=work_item.project.project_id,
        work_item_id=work_item.item_id,
        actor_id=user.user_id,
        action="ADD_COMMENT",
        details={"comment_id": comment_id},
    )
    return comment

def edit_comment(
    user_id: str,
    comment_id: str,
    new_body: str,
) -> None:
    user = _get_user(user_id)
    comment = _get_comment(comment_id)
    if user.org.org_id != comment.work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    comment.edit(user, new_body)

def delete_comment(
    user_id: str,
    comment_id: str,
) -> None:
    user = _get_user(user_id)
    comment = _get_comment(comment_id)
    if user.org.org_id != comment.work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    comment.delete(user)

def upload_attachment(
    user_id: str,
    item_id: str,
    filename: str,
    storage_id: str,
    size_bytes: int,
    comment_id: Optional[str] = None,
) -> Attachment:
    user = _get_user(user_id)
    work_item = _get_work_item(item_id)
    
    if user.org.org_id != work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    if user.user_id not in work_item.project.members and not user.is_admin:
        raise ResourceAccessDeniedError("User not a member of the project")
        
    comment = None
    if comment_id:
        comment = _get_comment(comment_id)
        if comment.work_item.item_id != item_id:
            raise InvalidParameterError("Comment does not belong to the work item")
            
    attachment_id = str(uuid.uuid4())
    attachment = Attachment(
        attachment_id=attachment_id,
        work_item=work_item,
        uploader=user,
        filename=filename,
        storage_id=storage_id,
        size_bytes=size_bytes,
        comment=comment,
    )
    work_item.attachments[attachment_id] = attachment
    attachments[attachment_id] = attachment
    
    _record_activity(
        org_id=work_item.project.org.org_id,
        project_id=work_item.project.project_id,
        work_item_id=work_item.item_id,
        actor_id=user.user_id,
        action="UPLOAD_ATTACHMENT",
        details={"attachment_id": attachment_id, "filename": attachment.filename},
    )
    return attachment

def delete_attachment(
    user_id: str,
    attachment_id: str,
) -> None:
    user = _get_user(user_id)
    attachment = _get_attachment(attachment_id)
    if user.org.org_id != attachment.work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    attachment.delete(user)

def get_attachment_download_url(
    user_id: str,
    attachment_id: str,
) -> str:
    user = _get_user(user_id)
    attachment = _get_attachment(attachment_id)
    
    if user.org.org_id != attachment.work_item.project.org.org_id:
        raise ResourceAccessDeniedError("Cross-organization access unauthorized")
    if attachment.deleted:
        raise AttachmentNotFoundException("Attachment has been deleted")
        
    # Attachments inherit and follow the exact access rules of the parent work item
    work_item = attachment.work_item
    if user.user_id not in work_item.project.members and not user.is_admin:
        raise UnauthorizedAttachmentAccessException("User not authorized to download this attachment")
        
    # In a real system this would generate a signed URL; here we return a placeholder
    return f"https://storage.example.com/{attachment.storage_id}"

# ----------------------------------------------------------------------
# End of module
# ----------------------------------------------------------------------