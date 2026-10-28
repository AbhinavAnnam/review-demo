from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
import threading

class UnauthorizedAdminAccessException(Exception):
    pass

class PrivilegeRevokedException(Exception):
    pass

class DestructiveActionUnconfirmedException(Exception):
    pass

class InvalidOwnershipRecipientException(Exception):
    pass

class ConflictingOwnershipTransferException(Exception):
    pass

class OwnershipRecoveryFailedException(Exception):
    pass

class OrganizationMember:
    def __init__(self, user_id: str, username: str, role: str, is_active: bool = True):
        self.user_id = user_id
        self.username = username
        self.role = role  # 'owner', 'administrator', 'member'
        self.is_active = is_active
        self.project_memberships: Set[str] = set()

class AuditLogEntry:
    def __init__(self, timestamp: datetime, actor_id: str, action: str, details: Dict[str, Any]):
        self.timestamp = timestamp
        self.actor_id = actor_id
        self.action = action
        self.details = details

class OrganizationAdministration:
    def __init__(self, org_id: str, org_name: str):
        self.org_id = org_id
        self.org_name = org_name
        self.members: Dict[str, OrganizationMember] = {}
        self.audit_history: List[AuditLogEntry] = []
        self._lock = threading.RLock()

    def add_member(self, user_id: str, username: str, role: str = "member") -> OrganizationMember:
        with self._lock:
            member = OrganizationMember(user_id=user_id, username=username, role=role, is_active=True)
            self.members[user_id] = member
            return member

    def _verify_admin_access(self, actor_id: str) -> OrganizationMember:
        if actor_id not in self.members:
            raise UnauthorizedAdminAccessException("User is not a member of this organization.")
        member = self.members[actor_id]
        if not member.is_active:
            raise PrivilegeRevokedException("User account is deactivated or suspended.")
        if member.role not in ("owner", "administrator"):
            raise UnauthorizedAdminAccessException("User lacks administrative privileges.")
        return member

    def _verify_owner_access(self, actor_id: str) -> OrganizationMember:
        if actor_id not in self.members:
            raise UnauthorizedAdminAccessException("User is not a member of this organization.")
        member = self.members[actor_id]
        if not member.is_active:
            raise PrivilegeRevokedException("User account is deactivated or suspended.")
        if member.role != "owner":
            raise UnauthorizedAdminAccessException("User lacks ownership privileges.")
        return member

    def get_members(self, actor_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            self._verify_admin_access(actor_id)
            result = []
            for m in self.members.values():
                result.append({
                    "user_id": m.user_id,
                    "username": m.username,
                    "role": m.role,
                    "is_active": m.is_active,
                    "project_memberships": list(m.project_memberships)
                })
            return result

    def remove_member_from_org(self, actor_id: str, target_user_id: str, confirmed: bool) -> None:
        with self._lock:
            self._verify_admin_access(actor_id)
            if not confirmed:
                raise DestructiveActionUnconfirmedException("Destructive action requires explicit user confirmation.")
            
            if target_user_id not in self.members:
                raise ValueError("Target user not found in organization.")
            
            target_member = self.members[target_user_id]
            if target_member.role == "owner":
                owners = [m for m in self.members.values() if m.role == "owner" and m.is_active]
                if len(owners) <= 1:
                    raise OwnershipRecoveryFailedException("Cannot remove the sole owner without transferring ownership first.")

            del self.members[target_user_id]
            
            self.audit_history.append(AuditLogEntry(
                timestamp=datetime.now(timezone.utc),
                actor_id=actor_id,
                action="REMOVE_MEMBER_FROM_ORG",
                details={"target_user_id": target_user_id}
            ))

    def remove_member_from_project(self, actor_id: str, target_user_id: str, project_id: str, confirmed: bool) -> None:
        with self._lock:
            self._verify_admin_access(actor_id)
            if not confirmed:
                raise DestructiveActionUnconfirmedException("Destructive action requires explicit user confirmation.")
            
            if target_user_id not in self.members:
                raise ValueError("Target user not found in organization.")
            
            target_member = self.members[target_user_id]
            if project_id not in target_member.project_memberships:
                raise ValueError("Target user is not a member of the specified project.")

            target_member.project_memberships.remove(project_id)
            
            self.audit_history.append(AuditLogEntry(
                timestamp=datetime.now(timezone.utc),
                actor_id=actor_id,
                action="REMOVE_MEMBER_FROM_PROJECT",
                details={"target_user_id": target_user_id, "project_id": project_id}
            ))

    def add_member_to_project(self, actor_id: str, target_user_id: str, project_id: str) -> None:
        with self._lock:
            self._verify_admin_access(actor_id)
            if target_user_id not in self.members:
                raise ValueError("Target user not found in organization.")
            
            target_member = self.members[target_user_id]
            target_member.project_memberships.add(project_id)
            
            self.audit_history.append(AuditLogEntry(
                timestamp=datetime.now(timezone.utc),
                actor_id=actor_id,
                action="ADD_MEMBER_TO_PROJECT",
                details={"target_user_id": target_user_id, "project_id": project_id}
            ))

    def transfer_ownership(self, actor_id: str, new_owner_id: str, previous_owner_new_role: str, confirmed: bool) -> None:
        with self._lock:
            current_owner = self._verify_owner_access(actor_id)
            
            if not confirmed:
                raise DestructiveActionUnconfirmedException("Ownership transfer requires explicit user confirmation.")
            
            if new_owner_id not in self.members:
                raise InvalidOwnershipRecipientException("The transfer recipient must be a member of the organization.")
            
            recipient = self.members[new_owner_id]
            if not recipient.is_active:
                raise InvalidOwnershipRecipientException("The transfer recipient must be an active member of the organization.")
            
            if new_owner_id == actor_id:
                raise InvalidOwnershipRecipientException("Cannot transfer ownership to yourself.")

            if previous_owner_new_role not in ("administrator", "member"):
                raise ValueError("Previous owner must transition to 'administrator' or 'member'.")

            active_owners = [m for m in self.members.values() if m.role == "owner" and m.is_active]
            if len(active_owners) > 1:
                pass

            if recipient.role == "owner":
                raise ConflictingOwnershipTransferException("Recipient is already an owner.")

            recipient.role = "owner"
            current_owner.role = previous_owner_new_role

            self.audit_history.append(AuditLogEntry(
                timestamp=datetime.now(timezone.utc),
                actor_id=actor_id,
                action="TRANSFER_OWNERSHIP",
                details={
                    "previous_owner_id": actor_id,
                    "new_owner_id": new_owner_id,
                    "previous_owner_new_role": previous_owner_new_role
                }
            ))

    def get_audit_history(self, actor_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            self._verify_admin_access(actor_id)
            history = []
            for entry in self.audit_history:
                history.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "actor_id": entry.actor_id,
                    "action": entry.action,
                    "details": entry.details
                })
            return history