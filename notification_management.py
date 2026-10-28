import uuid
import datetime
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Callable, Any


# Exceptions
class NotificationDeliveryException(Exception):
    """Raised when a notification could not be delivered to the user."""


class InvalidNotificationPreferenceException(Exception):
    """Raised when a user's notification preference is invalid or missing."""


class EmailDeliveryFailedException(Exception):
    """Raised when sending an email fails."""


class InvalidEmailTokenException(Exception):
    """Raised when an email token used for verification or invitation is invalid or expired."""


class NotificationNotFoundException(Exception):
    """Raised when a notification is not found."""


# Data models
@dataclass(frozen=True)
class Notification:
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime
    message: str
    read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationPreference:
    user_id: uuid.UUID
    in_app_enabled: bool = True
    email_enabled: bool = True
    assignment: bool = True
    mention: bool = True
    comment: bool = True


@dataclass(frozen=True)
class EmailTemplate:
    subject: str
    body: str


# In-memory stores
_notifications: Dict[uuid.UUID, List[Notification]] = {}
_preferences: Dict[uuid.UUID, NotificationPreference] = {}
_sent_email_tokens: Set[str] = set()
_processed_events: Set[str] = set()
_email_send_lock = threading.Lock()


# Helper functions
def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _store_notification(notification: Notification) -> None:
    _notifications.setdefault(notification.user_id, []).append(notification)


def _get_user_notifications(user_id: uuid.UUID) -> List[Notification]:
    return _notifications.get(user_id, [])


def _get_preference(user_id: uuid.UUID) -> NotificationPreference:
    pref = _preferences.get(user_id)
    if pref is None:
        raise InvalidNotificationPreferenceException(f"No preferences found for user {user_id}")
    return pref


def _deduplicate_event(event_key: str) -> bool:
    if event_key in _processed_events:
        return False
    _processed_events.add(event_key)
    return True


# Public API
def set_notification_preference(preference: NotificationPreference) -> None:
    _preferences[preference.user_id] = preference


def create_notification(
    user_id: uuid.UUID,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
    event_key: Optional[str] = None,
) -> Notification:
    if event_key and not _deduplicate_event(event_key):
        for n in _get_user_notifications(user_id):
            if n.metadata.get("event_key") == event_key:
                return n
    notif = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        created_at=_now_utc(),
        message=message,
        metadata={**(metadata or {}), **({"event_key": event_key} if event_key else {})},
    )
    _store_notification(notif)
    return notif


def mark_notification_as_read(user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
    notifs = _get_user_notifications(user_id)
    for idx, n in enumerate(notifs):
        if n.id == notification_id:
            if not n.read:
                notifs[idx] = Notification(
                    id=n.id,
                    user_id=n.user_id,
                    created_at=n.created_at,
                    message=n.message,
                    read=True,
                    metadata=n.metadata,
                )
            return
    raise NotificationNotFoundException(f"Notification {notification_id} not found for user {user_id}")


def get_unread_notifications(user_id: uuid.UUID) -> List[Notification]:
    return [n for n in _get_user_notifications(user_id) if not n.read]


def generate_assignment_notification(
    assignee_id: uuid.UUID,
    assigner_id: uuid.UUID,
    work_item_id: uuid.UUID,
    work_item_title: str,
    organization_id: Optional[uuid.UUID] = None,
) -> Notification:
    pref = _get_preference(assignee_id)
    if not pref.in_app_enabled or not pref.assignment:
        raise InvalidNotificationPreferenceException("Assignment notifications are disabled for this user.")

    message = f"You have been assigned to work item '{work_item_title}'."
    event_key = f"assign:{work_item_id}:{assignee_id}"
    notif = create_notification(
        user_id=assignee_id,
        message=message,
        metadata={
            "type": "assignment",
            "work_item_id": str(work_item_id),
            "assigner_id": str(assigner_id),
            "organization_id": str(organization_id) if organization_id else "",
        },
        event_key=event_key,
    )
    if pref.email_enabled:
        try:
            _enqueue_email(
                recipient_id=assignee_id,
                template=EmailTemplate(
                    subject="New Work Item Assignment",
                    body=f"Hello,\n\nYou have been assigned to '{work_item_title}'.\n\nView it in the app."
                ),
                context={"work_item_id": work_item_id, "assigner_id": assigner_id},
                organization_id=organization_id,
                resource_id=work_item_id,
            )
        except EmailDeliveryFailedException:
            pass
    return notif


def generate_mention_notification(
    mentioned_user_id: uuid.UUID,
    author_id: uuid.UUID,
    work_item_id: uuid.UUID,
    comment_id: uuid.UUID,
    snippet: str,
    organization_id: Optional[uuid.UUID] = None,
) -> Notification:
    pref = _get_preference(mentioned_user_id)
    if not pref.in_app_enabled or not pref.mention:
        raise InvalidNotificationPreferenceException("Mention notifications are disabled for this user.")

    message = f"You were mentioned in a comment: \"{snippet}\""
    event_key = f"mention:{comment_id}:{mentioned_user_id}"
    notif = create_notification(
        user_id=mentioned_user_id,
        message=message,
        metadata={
            "type": "mention",
            "work_item_id": str(work_item_id),
            "comment_id": str(comment_id),
            "author_id": str(author_id),
            "organization_id": str(organization_id) if organization_id else "",
        },
        event_key=event_key,
    )
    if pref.email_enabled:
        try:
            _enqueue_email(
                recipient_id=mentioned_user_id,
                template=EmailTemplate(
                    subject="You were mentioned in a comment",
                    body=f"Hello,\n\n{snippet}\n\nView the comment in the app."
                ),
                context={"work_item_id": work_item_id, "comment_id": comment_id, "author_id": author_id},
                organization_id=organization_id,
                resource_id=comment_id,
            )
        except EmailDeliveryFailedException:
            pass
    return notif


def generate_comment_notification(
    follower_user_id: uuid.UUID,
    commenter_id: uuid.UUID,
    work_item_id: uuid.UUID,
    comment_id: uuid.UUID,
    snippet: str,
    organization_id: Optional[uuid.UUID] = None,
) -> Optional[Notification]:
    pref = _get_preference(follower_user_id)
    if not pref.in_app_enabled or not pref.comment:
        return None

    message = f"New comment on a work item you follow: \"{snippet}\""
    event_key = f"comment:{comment_id}:{follower_user_id}"
    notif = create_notification(
        user_id=follower_user_id,
        message=message,
        metadata={
            "type": "comment",
            "work_item_id": str(work_item_id),
            "comment_id": str(comment_id),
            "commenter_id": str(commenter_id),
            "organization_id": str(organization_id) if organization_id else "",
        },
        event_key=event_key,
    )
    if pref.email_enabled:
        try:
            _enqueue_email(
                recipient_id=follower_user_id,
                template=EmailTemplate(
                    subject="New comment on followed work item",
                    body=f"Hello,\n\n{snippet}\n\nView the comment in the app."
                ),
                context={"work_item_id": work_item_id, "comment_id": comment_id, "commenter_id": commenter_id},
                organization_id=organization_id,
                resource_id=comment_id,
            )
        except EmailDeliveryFailedException:
            pass
    return notif


# Email handling
def _send_email(recipient_email: str, subject: str, body: str) -> None:
    if "fail" in recipient_email:
        raise EmailDeliveryFailedException(f"Failed to deliver email to recipient.")


def _resolve_user_email(user_id: uuid.UUID) -> str:
    return f"user-{user_id}@example.com"


def _enqueue_email(
    recipient_id: uuid.UUID,
    template: EmailTemplate,
    context: Optional[Dict[str, Any]] = None,
    organization_id: Optional[uuid.UUID] = None,
    resource_id: Optional[uuid.UUID] = None,
) -> None:
    org_id = organization_id or uuid.UUID("00000000-0000-0000-0000-000000000000")
    res_id = resource_id or recipient_id

    def worker():
        with _email_send_lock:
            try:
                email = _resolve_user_email(recipient_id)
                subject = template.subject.format(**(context or {}))
                body = template.body.format(**(context or {}))
                _send_email(email, subject, body)
            except EmailDeliveryFailedException as e:
                raise NotificationDeliveryException(str(e))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


# Invitation handling
def create_invitation(
    inviter_id: uuid.UUID,
    invitee_email: str,
    organization_id: uuid.UUID,
    token_generator: Callable[[], str],
) -> str:
    token = token_generator()
    if token in _sent_email_tokens:
        return token
    _sent_email_tokens.add(token)

    template = EmailTemplate(
        subject="You are invited to join",
        body=(
            "Hello,\n\nYou have been invited to join organization.\n"
            f"Please accept the invitation using this link: https://example.com/invite/{token}\n"
        ),
    )
    try:
        _enqueue_email(
            recipient_id=uuid.uuid4(),
            template=template,
            context={"token": token},
            organization_id=organization_id,
            resource_id=inviter_id,
        )
    except Exception:
        pass
    return token


def verify_invitation_token(token: str) -> bool:
    if token not in _sent_email_tokens:
        raise InvalidEmailTokenException("Token does not exist or has already been used.")
    _sent_email_tokens.remove(token)
    return True


def send_transactional_email(
    recipient_id: uuid.UUID,
    template: EmailTemplate,
    context: Optional[Dict[str, Any]] = None,
    organization_id: Optional[uuid.UUID] = None,
    resource_id: Optional[uuid.UUID] = None,
) -> None:
    try:
        _enqueue_email(recipient_id, template, context, organization_id=organization_id, resource_id=resource_id)
    except Exception:
        pass