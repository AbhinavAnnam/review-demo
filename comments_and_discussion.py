import datetime
import html
import os
import uuid
import threading
from typing import List, Dict, Any, Optional, Set, Tuple


class CommentNotFoundException(Exception):
    """Raised when a specified comment cannot be found."""
    pass


class CommentModerationPermissionException(Exception):
    """Raised when a user lacks permission to moderate or edit a comment."""
    pass


class UnsafeContentException(Exception):
    """Raised when comment content contains unsafe or unescaped executable patterns."""
    pass


class AttachmentNotFoundException(Exception):
    """Raised when a requested attachment does not exist."""
    pass


class FileTooLargeException(Exception):
    """Raised when an uploaded file exceeds the configured size limit."""
    pass


class InvalidFilePathException(Exception):
    """Raised when a user-supplied filename contains path traversal sequences or invalid structures."""
    pass


class StorageFailureException(Exception):
    """Raised when an error occurs while interacting with remote or local file storage."""
    pass


class FileUploadLimitExceededException(Exception):
    """Raised when file upload quotas or rate/size limits are exceeded."""
    pass


class UnauthorizedAttachmentAccessException(Exception):
    """Raised when a user lacks access privileges to view or download an attachment."""
    pass


class Comment:
    def __init__(
        self,
        comment_id: str,
        work_item_id: str,
        author_id: str,
        author_name: str,
        body: str,
        created_at: datetime.datetime,
        edited_at: Optional[datetime.datetime] = None,
        is_deleted: bool = False
    ) -> None:
        self.comment_id = comment_id
        self.work_item_id = work_item_id
        self.author_id = author_id
        self.author_name = author_name
        self.body = body
        self.created_at = created_at
        self.edited_at = edited_at
        self.is_deleted = is_deleted


class Attachment:
    def __init__(
        self,
        attachment_id: str,
        org_id: str,
        project_id: str,
        work_item_id: Optional[str],
        comment_id: Optional[str],
        uploader_id: str,
        display_name: str,
        storage_path: str,
        file_bytes: bytes,
        file_size: int,
        content_type: str,
        created_at: datetime.datetime,
        is_deleted: bool = False
    ) -> None:
        self.attachment_id = attachment_id
        self.org_id = org_id
        self.project_id = project_id
        self.work_item_id = work_item_id
        self.comment_id = comment_id
        self.uploader_id = uploader_id
        self.display_name = display_name
        self.storage_path = storage_path
        self.file_bytes = file_bytes
        self.file_size = file_size
        self.content_type = content_type
        self.created_at = created_at
        self.is_deleted = is_deleted


class CommentsAndDiscussionsManager:
    def __init__(self, max_file_size_bytes: int = 25 * 1024 * 1024) -> None:
        self.comments: Dict[str, Comment] = {}
        self.attachments: Dict[str, Attachment] = {}
        self.max_file_size_bytes = max_file_size_bytes
        self._lock = threading.RLock()

    def _sanitize_and_escape(self, raw_text: str) -> str:
        if not isinstance(raw_text, str):
            raise UnsafeContentException("Content must be a string.")
        if "<script" in raw_text.lower() or "javascript:" in raw_text.lower():
            raise UnsafeContentException("Content contains potential executable scripts or unsafe tags.")
        return html.escape(raw_text, quote=True)

    def _sanitize_filename(self, filename: str) -> str:
        if not filename or not isinstance(filename, str):
            raise InvalidFilePathException("Filename is missing or invalid.")
        
        normalized = filename.replace("\\", "/")
        base_name = os.path.basename(normalized)
        
        if not base_name or base_name in (".", "..") or ".." in normalized:
            raise InvalidFilePathException("Path traversal sequence detected in filename.")
        
        return base_name

    def add_comment(
        self,
        work_item_id: str,
        org_id: str,
        project_id: str,
        author_id: str,
        author_name: str,
        body: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str]
    ) -> Dict[str, Any]:
        with self._lock:
            if org_id not in user_org_memberships:
                raise UnauthorizedAttachmentAccessException("User lacks organization membership.")
            if project_id not in user_project_memberships:
                raise UnauthorizedAttachmentAccessException("User lacks project membership.")

            safe_body = self._sanitize_and_escape(body)
            comment_id = f"com_{uuid.uuid4().hex}"
            now = datetime.datetime.now(datetime.timezone.utc)

            comment = Comment(
                comment_id=comment_id,
                work_item_id=work_item_id,
                author_id=author_id,
                author_name=author_name,
                body=safe_body,
                created_at=now,
                edited_at=None,
                is_deleted=False
            )
            self.comments[comment_id] = comment

            return {
                "comment_id": comment.comment_id,
                "work_item_id": comment.work_item_id,
                "author_id": comment.author_id,
                "author_name": comment.author_name,
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
                "edited_at": None,
                "is_deleted": comment.is_deleted
            }

    def edit_comment(
        self,
        comment_id: str,
        actor_id: str,
        is_org_admin: bool,
        new_body: str,
        user_org_memberships: Set[str]
    ) -> Dict[str, Any]:
        with self._lock:
            if comment_id not in self.comments:
                raise CommentNotFoundException(f"Comment {comment_id} not found.")

            comment = self.comments[comment_id]
            if comment.is_deleted:
                raise CommentNotFoundException("Cannot edit a deleted comment.")

            if comment.author_id != actor_id and not is_org_admin:
                raise CommentModerationPermissionException("Users can only edit their own comments unless they are organization administrators.")

            safe_body = self._sanitize_and_escape(new_body)
            comment.body = safe_body
            comment.edited_at = datetime.datetime.now(datetime.timezone.utc)

            return {
                "comment_id": comment.comment_id,
                "work_item_id": comment.work_item_id,
                "author_id": comment.author_id,
                "author_name": comment.author_name,
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
                "edited_at": comment.edited_at.isoformat(),
                "is_deleted": comment.is_deleted
            }

    def delete_comment(
        self,
        comment_id: str,
        actor_id: str,
        is_org_admin: bool
    ) -> None:
        with self._lock:
            if comment_id not in self.comments:
                raise CommentNotFoundException(f"Comment {comment_id} not found.")

            comment = self.comments[comment_id]
            if comment.author_id != actor_id and not is_org_admin:
                raise CommentModerationPermissionException("User lacks permission to delete this comment.")

            comment.is_deleted = True
            comment.body = "[Content removed]"

    def list_comments(self, work_item_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            result = []
            for comment in self.comments.values():
                if comment.work_item_id == work_item_id:
                    result.append({
                        "comment_id": comment.comment_id,
                        "work_item_id": comment.work_item_id,
                        "author_id": comment.author_id,
                        "author_name": comment.author_name,
                        "body": comment.body,
                        "created_at": comment.created_at.isoformat(),
                        "edited_at": comment.edited_at.isoformat() if comment.edited_at else None,
                        "is_deleted": comment.is_deleted
                    })
            return result

    def upload_attachment(
        self,
        org_id: str,
        project_id: str,
        uploader_id: str,
        display_name: str,
        file_bytes: bytes,
        content_type: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        work_item_id: Optional[str] = None,
        comment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
            if org_id not in user_org_memberships:
                raise UnauthorizedAttachmentAccessException("Organization membership required.")
            if project_id not in user_project_memberships:
                raise UnauthorizedAttachmentAccessException("Project membership required.")

            if len(file_bytes) > self.max_file_size_bytes:
                raise FileTooLargeException(f"File exceeds maximum allowed size of {self.max_file_size_bytes} bytes.")

            sanitized_name = self._sanitize_filename(display_name)
            attachment_id = f"att_{uuid.uuid4().hex}"
            unique_storage_filename = f"{uuid.uuid4().hex}_{sanitized_name}"
            storage_path = f"/remote_storage/{org_id}/{project_id}/{unique_storage_filename}"

            try:
                # Simulated remote or decentralized storage persistence
                if file_bytes is None:
                    raise ValueError("File content cannot be None")
            except Exception as e:
                raise StorageFailureException(f"Failed to persist attachment to storage: {str(e)}")

            now = datetime.datetime.now(datetime.timezone.utc)
            attachment = Attachment(
                attachment_id=attachment_id,
                org_id=org_id,
                project_id=project_id,
                work_item_id=work_item_id,
                comment_id=comment_id,
                uploader_id=uploader_id,
                display_name=sanitized_name,
                storage_path=storage_path,
                file_bytes=file_bytes,
                file_size=len(file_bytes),
                content_type=content_type,
                created_at=now,
                is_deleted=False
            )
            self.attachments[attachment_id] = attachment

            return {
                "attachment_id": attachment.attachment_id,
                "org_id": attachment.org_id,
                "project_id": attachment.project_id,
                "work_item_id": attachment.work_item_id,
                "comment_id": attachment.comment_id,
                "display_name": attachment.display_name,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type,
                "created_at": attachment.created_at.isoformat()
            }

    def delete_attachment(
        self,
        attachment_id: str,
        actor_id: str,
        is_org_admin: bool,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str]
    ) -> None:
        with self._lock:
            if attachment_id not in self.attachments:
                raise AttachmentNotFoundException(f"Attachment {attachment_id} not found.")

            attachment = self.attachments[attachment_id]
            if attachment.org_id not in user_org_memberships:
                raise UnauthorizedAttachmentAccessException("Unauthorized organization context.")
            if attachment.project_id not in user_project_memberships and not is_org_admin:
                raise UnauthorizedAttachmentAccessException("Unauthorized project context.")

            if attachment.uploader_id != actor_id and not is_org_admin:
                raise UnauthorizedAttachmentAccessException("User lacks permission to delete this attachment.")

            attachment.is_deleted = True
            attachment.storage_path = ""
            attachment.file_bytes = b""

    def download_attachment(
        self,
        attachment_id: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        is_org_admin: bool
    ) -> Tuple[str, str, str, bytes]:
        with self._lock:
            if attachment_id not in self.attachments:
                raise AttachmentNotFoundException(f"Attachment {attachment_id} not found.")

            attachment = self.attachments[attachment_id]
            if attachment.is_deleted:
                raise AttachmentNotFoundException("Attachment has been deleted.")

            if attachment.org_id not in user_org_memberships:
                raise UnauthorizedAttachmentAccessException("Access denied for organization.")
            if attachment.project_id not in user_project_memberships and not is_org_admin:
                raise UnauthorizedAttachmentAccessException("Access denied for project.")

            inline_safe_types = {"application/pdf", "image/png", "image/jpeg", "text/plain"}
            content_disposition = "inline" if attachment.content_type in inline_safe_types else "attachment"

            return attachment.display_name, attachment.content_type, content_disposition, attachment.file_bytes

    def list_attachments_for_work_item(
        self,
        work_item_id: str,
        user_org_memberships: Set[str],
        user_project_memberships: Set[str],
        org_id: str,
        project_id: str,
        is_org_admin: bool
    ) -> List[Dict[str, Any]]:
        with self._lock:
            if org_id not in user_org_memberships:
                raise UnauthorizedAttachmentAccessException("Unauthorized organization.")
            if project_id not in user_project_memberships and not is_org_admin:
                raise UnauthorizedAttachmentAccessException("Unauthorized project.")

            results = []
            for att in self.attachments.values():
                if att.work_item_id == work_item_id and not att.is_deleted and att.org_id == org_id:
                    results.append({
                        "attachment_id": att.attachment_id,
                        "display_name": att.display_name,
                        "file_size": att.file_size,
                        "content_type": att.content_type,
                        "created_at": att.created_at.isoformat(),
                        "uploader_id": att.uploader_id
                    })
            return results