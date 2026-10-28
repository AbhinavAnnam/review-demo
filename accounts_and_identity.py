from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Any

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    ZoneInfo = None  # type: ignore
    ZoneInfoNotFoundError = Exception  # type: ignore


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class VerificationError(Exception):
    """Raised when account or token verification fails."""
    pass


class AccountNotFoundError(Exception):
    """Raised when an account cannot be found."""
    pass


class OrganizationAccessError(Exception):
    """Raised when access to an organization is unauthorized or forbidden."""
    pass


class InvitationNotFoundError(Exception):
    """Raised when an invitation cannot be found or is invalid."""
    pass


class DuplicateIdentifierError(Exception):
    """Raised when a unique identifier already exists."""
    pass


class InvalidOrganizationSettingException(Exception):
    """Raised when an organization setting value is invalid."""
    pass


class UnauthorizedSettingsUpdateException(Exception):
    """Raised when an unauthorized user attempts to update settings."""
    pass


class UnauthorizedRoleElevationError(Exception):
    """Raised when a user attempts to elevate their own role improperly."""
    pass


class MemberRemovalError(Exception):
    """Raised when an invalid member removal operation is attempted."""
    pass


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""
    pass


class ProjectDeletionError(Exception):
    """Raised when a project cannot be deleted."""
    pass


class ProjectOwnerRemovalError(Exception):
    """Raised when attempting to remove the project owner without designating a replacement."""
    pass


class ActivityLog:
    def __init__(self) -> None:
        self.logs: List[Dict[str, Any]] = []

    def record(self, organization_id: str, actor_id: str, action: str, details: Dict[str, Any]) -> None:
        self.logs.append({
            "timestamp": datetime.now(timezone.utc),
            "organization_id": organization_id,
            "actor_id": actor_id,
            "action": action,
            "details": details
        })

    def get_logs(self, organization_id: str) -> List[Dict[str, Any]]:
        return [log for log in self.logs if log["organization_id"] == organization_id]


class Account:
    def __init__(self, email: str, password_hash: str, display_name: Optional[str] = None) -> None:
        self.id: str = str(uuid.uuid4())
        self.email: str = email.lower()
        self.original_email_capitalization: str = email
        self.password_hash: str = password_hash
        self.display_name: str = display_name if display_name else email
        self.is_verified: bool = False
        self.verification_token: str = secrets.token_urlsafe(32)
        self.password_reset_token: Optional[str] = None
        self.password_reset_expires: Optional[datetime] = None
        self.is_active: bool = True
        self.sessions: Set[str] = set()

    def update_profile(self, display_name: Optional[str] = None) -> None:
        if display_name is not None:
            self.display_name = display_name

    def deactivate(self) -> None:
        self.is_active = False
        self.sessions.clear()

    def create_session(self) -> str:
        session_token = secrets.token_urlsafe(32)
        self.sessions.add(session_token)
        return session_token

    def invalidate_sessions(self) -> None:
        self.sessions.clear()


class Organization:
    def __init__(self, name: str, short_identifier: Optional[str], owner_id: str) -> None:
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.short_identifier: Optional[str] = short_identifier
        self.timezone: str = "UTC"
        self.members: Dict[str, str] = {owner_id: "owner"}  # user_id -> role ("owner", "administrator", "member")
        self.historical_member_references: Set[str] = {owner_id}


class Invitation:
    def __init__(self, organization_id: str, email: str, role: str) -> None:
        self.id: str = str(uuid.uuid4())
        self.organization_id: str = organization_id
        self.email: str = email.lower()
        self.role: str = role
        self.token: str = secrets.token_urlsafe(32)
        self.revoked: bool = False


class Project:
    def __init__(self, name: str, description: str, creator_id: str, organization_id: str, due_date: Optional[datetime] = None) -> None:
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.description: str = description
        self.creator_id: str = creator_id
        self.owner_id: str = creator_id
        self.organization_id: str = organization_id
        self.status: str = "active"  # "active", "archived", "completed"
        self.created_at: datetime = datetime.now(timezone.utc)
        self.due_date: Optional[datetime] = due_date
        self.members: Set[str] = {creator_id}
        self.historical_members: Set[str] = {creator_id}
        self.comments: List[Dict[str, Any]] = []
        self.work_items: List[Dict[str, Any]] = []
        self.activities: List[Dict[str, Any]] = []


class AccountsAndIdentityManager:
    def __init__(self) -> None:
        self.accounts: Dict[str, Account] = {}  # email.lower() -> Account
        self.accounts_by_id: Dict[str, Account] = {}  # account_id -> Account
        self.organizations: Dict[str, Organization] = {}
        self.invitations: Dict[str, Invitation] = {}
        self.projects: Dict[str, Project] = {}
        self.activity_log: ActivityLog = ActivityLog()

    def register_account(self, email: str, password: str, display_name: Optional[str] = None) -> Account:
        normalized_email = email.lower()
        if normalized_email in self.accounts:
            raise DuplicateIdentifierError("Account with this email already exists.")
        
        salt = secrets.token_bytes(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()
        stored_hash = f"{salt.hex()}${pwd_hash}"

        account = Account(email=email, password_hash=stored_hash, display_name=display_name)
        self.accounts[normalized_email] = account
        self.accounts_by_id[account.id] = account
        return account

    def verify_account(self, verification_token: str) -> Account:
        for account in self.accounts.values():
            if account.verification_token == verification_token:
                account.is_verified = True
                return account
        raise VerificationError("Invalid or expired verification token.")

    def authenticate(self, email: str, password: str) -> Tuple[Account, str]:
        normalized_email = email.lower()
        account = self.accounts.get(normalized_email)
        if not account or not account.is_active:
            raise AuthenticationError("Invalid email or password.")

        try:
            salt_hex, pwd_hex = account.password_hash.split('$')
            salt = bytes.fromhex(salt_hex)
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()
            if not hmac.compare_digest(computed_hash, pwd_hex):
                raise AuthenticationError("Invalid email or password.")
        except Exception:
            raise AuthenticationError("Invalid email or password.")

        session_token = account.create_session()
        return account, session_token

    def request_password_reset(self, email: str) -> Optional[str]:
        normalized_email = email.lower()
        account = self.accounts.get(normalized_email)
        if not account or not account.is_active:
            return None
        
        reset_token = secrets.token_urlsafe(32)
        account.password_reset_token = reset_token
        account.password_reset_expires = datetime.now(timezone.utc)
        return reset_token

    def complete_password_reset(self, reset_token: str, new_password: str) -> Account:
        target_account = None
        for account in self.accounts.values():
            if account.password_reset_token == reset_token:
                target_account = account
                break
        
        if not target_account or not target_account.is_active:
            raise VerificationError("Invalid or expired password reset token.")

        salt = secrets.token_bytes(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode('utf-8'), salt, 100000).hex()
        target_account.password_hash = f"{salt.hex()}${pwd_hash}"
        target_account.password_reset_token = None
        target_account.password_reset_expires = None
        target_account.invalidate_sessions()
        return target_account

    def change_password(self, account_id: str, old_password: str, new_password: str) -> Account:
        account = self.accounts_by_id.get(account_id)
        if not account or not account.is_active:
            raise AccountNotFoundError("Account not found.")

        try:
            salt_hex, pwd_hex = account.password_hash.split('$')
            salt = bytes.fromhex(salt_hex)
            computed_hash = hashlib.pbkdf2_hmac('sha256', old_password.encode('utf-8'), salt, 100000).hex()
            if not hmac.compare_digest(computed_hash, pwd_hex):
                raise AuthenticationError("Old password is incorrect.")
        except Exception:
            raise AuthenticationError("Old password is incorrect.")

        salt = secrets.token_bytes(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode('utf-8'), salt, 100000).hex()
        account.password_hash = f"{salt.hex()}${pwd_hash}"
        account.invalidate_sessions()
        return account

    def create_organization(self, name: str, owner_account_id: str, short_identifier: Optional[str] = None) -> Organization:
        owner = self.accounts_by_id.get(owner_account_id)
        if not owner or not owner.is_active:
            raise AccountNotFoundError("Owner account not found or inactive.")

        if short_identifier:
            for org in self.organizations.values():
                if org.short_identifier == short_identifier:
                    raise DuplicateIdentifierError("Organization short identifier already taken.")

        org = Organization(name=name, short_identifier=short_identifier, owner_id=owner_account_id)
        self.organizations[org.id] = org
        self.activity_log.record(org.id, owner_account_id, "ORGANIZATION_CREATED", {"name": name, "short_identifier": short_identifier})
        return org

    def update_organization_settings(self, organization_id: str, actor_id: str, name: Optional[str] = None, timezone_str: Optional[str] = None) -> Organization:
        org = self.organizations.get(organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_role = org.members.get(actor_id)
        if actor_role not in ["owner", "administrator"]:
            raise UnauthorizedSettingsUpdateException("User does not have permission to update organization settings.")

        updates = {}
        if name is not None:
            org.name = name
            updates["name"] = name
        
        if timezone_str is not None:
            if ZoneInfo is not None:
                try:
                    ZoneInfo(timezone_str)
                except (ZoneInfoNotFoundError, Exception):
                    raise InvalidOrganizationSettingException("Invalid timezone provided.")
            else:
                try:
                    datetime.now(timezone.utc)
                except Exception:
                    raise InvalidOrganizationSettingException("Invalid timezone provided.")
            org.timezone = timezone_str
            updates["timezone"] = timezone_str

        self.activity_log.record(org.id, actor_id, "SETTINGS_UPDATED", updates)
        return org

    def invite_member(self, organization_id: str, actor_id: str, email: str, role: str) -> Invitation:
        org = self.organizations.get(organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_role = org.members.get(actor_id)
        if actor_role not in ["owner", "administrator"]:
            raise OrganizationAccessError("Unauthorized to invite members.")

        if role not in ["owner", "administrator", "member"]:
            raise InvalidOrganizationSettingException("Invalid role specified.")

        invitation = Invitation(organization_id=organization_id, email=email, role=role)
        self.invitations[invitation.id] = invitation
        self.activity_log.record(org.id, actor_id, "MEMBER_INVITED", {"email": email, "role": role})
        return invitation

    def revoke_invitation(self, organization_id: str, actor_id: str, invitation_id: str) -> None:
        org = self.organizations.get(organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_role = org.members.get(actor_id)
        if actor_role not in ["owner", "administrator"]:
            raise OrganizationAccessError("Unauthorized to revoke invitations.")

        invitation = self.invitations.get(invitation_id)
        if not invitation or invitation.organization_id != organization_id:
            raise InvitationNotFoundError("Invitation not found.")

        invitation.revoked = True
        self.activity_log.record(org.id, actor_id, "INVITATION_REVOKED", {"invitation_id": invitation_id})

    def accept_invitation(self, invitation_token: str, account_id: str) -> Organization:
        target_invitation = None
        for inv in self.invitations.values():
            if inv.token == invitation_token and not inv.revoked:
                target_invitation = inv
                break

        if not target_invitation:
            raise InvitationNotFoundError("Valid invitation not found.")

        account = self.accounts_by_id.get(account_id)
        if not account or not account.is_active:
            raise AccountNotFoundError("Account not found.")

        if account.email != target_invitation.email:
            raise OrganizationAccessError("Account email does not match invitation email.")

        org = self.organizations.get(target_invitation.organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        org.members[account.id] = target_invitation.role
        org.historical_member_references.add(account.id)
        
        del self.invitations[target_invitation.id]

        self.activity_log.record(org.id, account.id, "INVITATION_ACCEPTED", {"role": target_invitation.role})
        return org

    def change_member_role(self, organization_id: str, actor_id: str, target_user_id: str, new_role: str) -> None:
        org = self.organizations.get(organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_role = org.members.get(actor_id)
        if actor_role not in ["owner", "administrator"]:
            raise OrganizationAccessError("Unauthorized to change member roles.")

        if target_user_id not in org.members:
            raise AccountNotFoundError("Target user is not a member of this organization.")

        if new_role not in ["owner", "administrator", "member"]:
            raise InvalidOrganizationSettingException("Invalid role specified.")

        if actor_id == target_user_id:
            raise UnauthorizedRoleElevationError("Cannot modify your own role.")

        if actor_role == "administrator" and new_role == "owner":
            raise UnauthorizedRoleElevationError("Administrators cannot promote members to owner.")

        if org.members[target_user_id] == "owner" and actor_role != "owner":
            raise UnauthorizedRoleElevationError("Only owners can modify owner roles.")

        org.members[target_user_id] = new_role
        self.activity_log.record(org.id, actor_id, "MEMBER_ROLE_CHANGED", {"target_user_id": target_user_id, "new_role": new_role})

    def remove_member(self, organization_id: str, actor_id: str, target_user_id: str) -> None:
        org = self.organizations.get(organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_role = org.members.get(actor_id)
        if actor_role not in ["owner", "administrator"]:
            raise OrganizationAccessError("Unauthorized to remove members.")

        if target_user_id not in org.members:
            raise AccountNotFoundError("Target user is not a member of this organization.")

        if org.members[target_user_id] == "owner":
            owners_count = sum(1 for r in org.members.values() if r == "owner")
            if owners_count <= 1:
                raise MemberRemovalError("Cannot remove the sole organization owner.")

        if actor_role == "administrator" and org.members[target_user_id] in ["owner", "administrator"]:
            raise MemberRemovalError("Administrators cannot remove owners or other administrators.")

        del org.members[target_user_id]
        org.historical_member_references.add(target_user_id)
        self.activity_log.record(org.id, actor_id, "MEMBER_REMOVED", {"target_user_id": target_user_id})

    def transfer_ownership(self, organization_id: str, current_owner_id: str, new_owner_id: str) -> None:
        org = self.organizations.get(organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        if org.members.get(current_owner_id) != "owner":
            raise OrganizationAccessError("Current user is not the organization owner.")

        if new_owner_id not in org.members:
            raise AccountNotFoundError("New owner must be an organization member.")

        org.members[current_owner_id] = "administrator"
        org.members[new_owner_id] = "owner"
        self.activity_log.record(org.id, current_owner_id, "OWNERSHIP_TRANSFERRED", {"new_owner_id": new_owner_id})

    def create_project(self, organization_id: str, actor_id: str, name: str, description: str, due_date: Optional[datetime] = None) -> Project:
        org = self.organizations.get(organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        if actor_id not in org.members:
            raise OrganizationAccessError("User must be an organization member to create a project.")

        project = Project(name=name, description=description, creator_id=actor_id, organization_id=organization_id, due_date=due_date)
        self.projects[project.id] = project
        self.activity_log.record(org.id, actor_id, "PROJECT_CREATED", {"project_id": project.id, "name": name})
        return project

    def add_project_member(self, project_id: str, actor_id: str, target_user_id: str) -> None:
        project = self.projects.get(project_id)
        if not project:
            raise ProjectNotFoundError("Project not found.")

        org = self.organizations.get(project.organization_id)
        if not org or actor_id not in org.members:
            raise OrganizationAccessError("Unauthorized organization context.")

        actor_org_role = org.members.get(actor_id)
        if project.owner_id != actor_id and actor_org_role not in ["owner", "administrator"]:
            raise OrganizationAccessError("Unauthorized to add project members.")

        if target_user_id not in org.members:
            raise MemberRemovalError("Target user must be a member of the organization.")

        project.members.add(target_user_id)
        project.historical_members.add(target_user_id)
        self.activity_log.record(org.id, actor_id, "PROJECT_MEMBER_ADDED", {"project_id": project_id, "target_user_id": target_user_id})

    def remove_project_member(self, project_id: str, actor_id: str, target_user_id: str) -> None:
        project = self.projects.get(project_id)
        if not project:
            raise ProjectNotFoundError("Project not found.")

        org = self.organizations.get(project.organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_org_role = org.members.get(actor_id)
        if project.owner_id != actor_id and actor_org_role not in ["owner", "administrator"]:
            raise OrganizationAccessError("Unauthorized to remove project members.")

        if target_user_id == project.owner_id:
            raise ProjectOwnerRemovalError("Cannot remove the project owner without designating another owner.")

        if target_user_id in project.members:
            project.members.remove(target_user_id)
            project.historical_members.add(target_user_id)
            self.activity_log.record(org.id, actor_id, "PROJECT_MEMBER_REMOVED", {"project_id": project_id, "target_user_id": target_user_id})

    def archive_project(self, project_id: str, actor_id: str) -> None:
        project = self.projects.get(project_id)
        if not project:
            raise ProjectNotFoundError("Project not found.")

        org = self.organizations.get(project.organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_org_role = org.members.get(actor_id)
        if project.owner_id != actor_id and actor_org_role not in ["owner", "administrator"]:
            raise OrganizationAccessError("Unauthorized to archive project.")

        project.status = "archived"
        self.activity_log.record(org.id, actor_id, "PROJECT_ARCHIVED", {"project_id": project_id})

    def delete_project(self, project_id: str, actor_id: str) -> None:
        project = self.projects.get(project_id)
        if not project:
            raise ProjectNotFoundError("Project not found.")

        org = self.organizations.get(project.organization_id)
        if not org:
            raise OrganizationAccessError("Organization not found.")

        actor_org_role = org.members.get(actor_id)
        if project.owner_id != actor_id and actor_org_role != "owner":
            raise OrganizationAccessError("Only project owners or organization owners can delete projects.")

        # Clean up dependent work items, comments, attachments, and activity records
        project.work_items.clear()
        project.comments.clear()
        project.activities.clear()
        project.members.clear()
        project.historical_members.clear()

        del self.projects[project_id]
        self.activity_log.record(org.id, actor_id, "PROJECT_DELETED", {"project_id": project_id})