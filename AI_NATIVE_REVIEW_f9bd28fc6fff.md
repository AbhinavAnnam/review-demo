# Northstar — change report

Run: `648d756a-a8ac-4d3c-9c5d-ae8b9d37eb42`
Candidate: `e0d7a5a51e6c157f5fd1c54a756955fb3332b1ac6108a0e989243f85262010c0`

## Change summary

207 requirements assessed; 5 confirmed defects, 1 uncertain findings, 1 suggestions.

Critic verdict: **changes_requested**. 207 requirements assessed.
Coverage: met: 151, partial: 3, missing: 8, unclear: 45.
Findings: 5 confirmed defects, 1 uncertain findings, 1 suggestions.

Repository: https://github.com/AbhinavAnnam/review-demo.git
Base branch: `main`
Baseline commit: `186928a2bb3b1666105008bdb32a803617a08831`
Working branch: `ai-native/3faf99b64fed40229ca9a7c1e5e3c8ec`

## Files and modifications

| File | Change | Lines added | Lines removed |
| --- | --- | ---: | ---: |
| accounts_and_identity.py | modified | 430 | 290 |
| comments_and_discussion.py | added | 386 | 0 |
| notification_management.py | modified | 90 | 103 |
| project_membership.py | added | 627 | 0 |
| search_management.py | modified | 76 | 5 |

### accounts_and_identity.py

- Account: changed
- AccountsAndIdentityManager: changed
- ActivityLog: changed
- AuthenticationException: added
- ConcurrentOwnershipTransferException: added
- DestructiveActionConfirmationRequiredException: added
- DuplicateOrganizationIdentifierException: added
- EmailNotVerifiedException: added
- InsufficientAdministrativePrivilegesException: added
- InsufficientPermissionsException: added
- InvalidCredentialsException: added
- InvalidOwnershipRecipientException: added
- Invitation: changed
- InvitationExpiredException: added
- InvitationRevokedException: added
- Organization: changed
- OrganizationNotFoundException: added
- OwnerRemovalException: added
- Project: changed
- RoleAssignmentException: added
- UnauthorizedException: added

### comments_and_discussion.py

- Attachment: added
- AttachmentNotFoundException: added
- Comment: added
- CommentModerationPermissionException: added
- CommentNotFoundException: added
- CommentsAndDiscussionsManager: added
- FileTooLargeException: added
- FileUploadLimitExceededException: added
- InvalidFilePathException: added
- StorageFailureException: added
- UnauthorizedAttachmentAccessException: added
- UnsafeContentException: added

### notification_management.py

- NotificationNotFoundException: added
- _deduplicate_event: changed
- _enqueue_email: changed
- _now_utc: changed
- _resolve_user_email: changed
- _send_email: changed
- create_invitation: changed
- create_notification: changed
- generate_assignment_notification: changed
- generate_comment_notification: changed
- generate_mention_notification: changed
- get_unread_notifications: changed
- mark_notification_as_read: changed
- send_transactional_email: changed
- set_notification_preference: changed
- verify_invitation_token: changed

### project_membership.py

- CrossOrganizationAccessException: added
- InvalidPriorityException: added
- InvalidStatusTransitionException: added
- InvalidWorkItemStateException: added
- LastProjectOwnerRemovalException: added
- MalformedIdentifierException: added
- Project: added
- ProjectAccessDeniedException: added
- ProjectDeletionConstraintException: added
- ProjectMembershipManager: added
- ProjectMembershipNotFoundException: added
- ProjectNotFoundException: added
- WorkItem: added
- WorkItemNotFoundException: added

### search_management.py

- ActivityLogImmutableException: added
- DashboardManager: changed
- SearchManager: changed
- SearchQueryFormatException: added
- UnauthorizedAccessDeniedException: added

## Validation and testing

- Approved Python files were checked for valid syntax and matched to the reviewed candidate.
- **Automated tests were not run in this delivery workflow. The testing phase was skipped.**
- The critic is a static, model-assisted assessment; its verdict does not establish runtime correctness.
- Remaining findings are disclosed below for the pull request reviewer.

## Requirement coverage

| Requirement | Module | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| R-e04367bf23d0 | accounts_and_identity | Accounts are based around an email address, but the email address is not an organization's identity for authorization purposes. | met | Organizations use membership mappings distinct from raw emails. |
| R-f4ffe4088660 | accounts_and_identity | A person joining two organizations should continue using the same account rather than creating a second account for each organization. | met | Accounts are stored centrally by ID and email lookup. |
| R-53eda023353a | accounts_and_identity | A new user provides an email address and password and is subsequently asked to verify ownership of that address; until verification is completed, the account may exist but should not be treated as fully active. | met | New accounts start unverified and check verification during auth. |
| R-1ce760617d34 | accounts_and_identity | The account model should avoid assumptions that an account must always authenticate using a password, despite external identity providers not being required for the initial release. | met | Accounts store password_hash rather than assuming direct credentials. |
| R-d40c9e137af6 | accounts_and_identity | Email addresses are treated case-insensitively for account lookup; the displayed address may preserve original capitalization, but two differently capitalized representations must not result in separate accounts. | met | Email lowercasing used for registry lookups. |
| R-3c5d0ba29e9e | accounts_and_identity | A password reset begins from the sign-in experience and can be requested without an authenticated session. | met | Password reset triggered from request_password_reset without session. |
| R-22d23aabfe90 | accounts_and_identity | The reset mechanism must not reveal whether a particular email address belongs to an existing account to prevent the login system from becoming a user directory. | met | Request returns None for unknown emails, preventing directory harvesting. |
| R-de8fc66c05a0 | accounts_and_identity | Password-reset links are temporary, and once a reset is successfully completed, the old reset link must not remain usable. | met | Complete password reset clears tokens and invalidates sessions. |
| R-c93c2c595d22 | accounts_and_identity | Sessions must be invalidated when appropriate security-sensitive actions occur; in particular, changing a password must not leave every previously issued session permanently trusted. | met | Changing password invalidates existing sessions. |
| R-7734d522f485 | accounts_and_identity | The system should avoid storing raw passwords or password-reset secrets. | met | Passwords stored securely using pbkdf2_hmac with salt. |
| R-1e7e3aee8291 | accounts_and_identity | Users should be able to change their own profile information, and display name is used throughout the application without being forced to equal the email address. | met | Profile update supports display names independently of emails. |
| R-48acd0e8a27a | accounts_and_identity | A user may deactivate their account, but organizations must not unexpectedly lose historical references merely because the individual is no longer active. | met | Deactivation clears sessions, but historical references remain. |
| R-f0df29e55d86 | accounts_and_identity | The first user creating an organization becomes its initial owner. | met | Initial organization creator is assigned as owner. |
| R-6025eaa74e33 | accounts_and_identity | An organization has a name and may optionally have a short identifier used in URLs and integrations that must be unique enough to avoid ambiguous routing. | met | Unique constraint checked for short identifiers. |
| R-f7c32a62cfe0 | accounts_and_identity | Organizations are isolated from one another; a member of Organization A must not gain access to Organization B due to shared email addresses or known object identifiers, and API authorization must enforce the same boundary. | met | Organizations isolated via explicit organization_id checks. |
| R-e954a7827c90 | accounts_and_identity | An organization owner can invite additional people using email addresses without requiring the administrator to know if the recipient already has a Northstar account. | met | Owner can invite members via email addresses. |
| R-49bac5429e66 | accounts_and_identity | If a recipient already has an account, accepting an invitation adds the existing account to the organization without creating a duplicate identity; if not, the invitation becomes part of the registration process. | met | Invitation acceptance associates existing account or registration. |
| R-14303a167c78 | accounts_and_identity | Invitations should not remain valid indefinitely, and the administration area should provide visibility into invitations awaiting action. | unclear | No expiration timestamp checking implemented on invitations. |
| R-bb2bd8c78993 | accounts_and_identity | An invitation sent to an incorrect address may be revoked to prevent subsequent acceptance, and accepting an invitation from one organization must not consume or invalidate unrelated invitations from other organizations. | met | Invitations can be revoked and tokens are scoped properly. |
| R-141e6b71c37b | accounts_and_identity | Organizations may have their own timezone setting affecting date and scheduled event presentation, while stored timestamps remain unambiguous across different viewer locations. | met | Timezone settings stored on organization, activity timestamps use UTC. |
| R-7b06e316e49e | accounts_and_identity | The organization name may be changed later, and references in historical activity should remain understandable after such changes. | met | Organization name updates correctly and logs activity. |
| R-30dea42f1297 | accounts_and_identity | Organization administrators can configure workspace behavior, including organization name and timezone. | met | Administrators can update settings like name and timezone. |
| R-6c656016e017 | accounts_and_identity | Settings must be strictly scoped to the organization level. | met | Settings scoped to organization level. |
| R-a82017a046a4 | accounts_and_identity | Changing an organization timezone affects future display interpretation of dates/times but must not rewrite existing activity timestamps. | met | Timezone setting changes future interpretation without altering logs. |
| R-2728f00eef73 | accounts_and_identity | Setting changes must be recorded in administrative activity history. | met | Setting changes recorded in activity log. |
| R-482adbb354f5 | accounts_and_identity | Sensible defaults must be maintained when settings are unconfigured, distinguishing unconfigured settings from explicitly chosen defaults. | met | Default timezone set to UTC when unconfigured. |
| R-873e20ef8417 | accounts_and_identity | Provides controls for membership management, pending invitations, organization settings, and security info. | unclear | API controls present, but UI layer not supplied. |
| R-cc357122e61c | accounts_and_identity | Administrators can inspect current members and roles. | met | Administrators can inspect roles via member dictionaries. |
| R-5da7579226f7 | accounts_and_identity | Administrative pages must enforce active privilege checks on every operation rather than relying on URL secrecy. | met | Administrative operations enforce privilege checks. |
| R-abea98e7cfed | accounts_and_identity | If administrative privileges are revoked during an active session, the user must immediately be blocked from performing further administrative operations. | unclear | Session privilege revocation checks are not explicitly implemented. |
| R-e300b2173f9c | accounts_and_identity | Destructive operations (removing members, deleting projects, transferring ownership) require extra confirmation. | met | Destructive operations accept explicit confirmation parameter. |
| R-0d166bffda3b | accounts_and_identity | The interface must clearly distinguish between removing a user from a project versus removing a user from the organization. | unclear | UI layer distinguishing project vs org removal not supplied. |
| R-ba53c343954b | accounts_and_identity | The initial product has three broad levels of access: owner, administrator, and member. | met | Three distinct roles supported: owner, administrator, member. |
| R-6f4fa01336d0 | accounts_and_identity | The owner is responsible for organization-level control, normally one at a time, and ownership can be transferred. | met | Owner manages controls and ownership can be transferred. |
| R-5796d94f1b67 | accounts_and_identity | Administrators can manage many operational aspects but cannot perform actions reserved exclusively for the owner. | met | Administrators can manage operations but cannot perform owner actions. |
| R-8ce3acf0b47b | accounts_and_identity | Ordinary members can participate in projects and work but cannot access organization-wide controls based solely on URL knowledge. | met | Ordinary members participate in projects without org-wide controls. |
| R-58e8a813a379 | accounts_and_identity | Authorization requires server-side checks rather than purely hiding UI buttons. | met | Server-side privilege checks enforce authorization. |
| R-2afa6a7abff9 | accounts_and_identity | Removing a member from an organization immediately prevents them from accessing organization data through normal authenticated requests, but must not rewrite old activity or make historical associations and assignments disappear. | met | Member removal prevents access while keeping historical references. |
| R-475779151bae | accounts_and_identity | An administrator may change a member's role, subject to restrictions around ownership, and a member cannot elevate their own permissions by modifying a server request. | met | Role changes restricted and self-elevation prevented. |
| R-e95301024ca5 | accounts_and_identity | The organization member list should make it possible to distinguish active members from pending invitations without a large arbitrary permission matrix. | met | Members and invitations are stored in separate collections. |
| R-60b9e6ea0889 | accounts_and_identity | A current owner can designate another active organization member as owner. | met | Current owner can designate another member as owner. |
| R-a966e5de68d4 | accounts_and_identity | The recipient of ownership must already belong to the organization. | met | New owner must be an existing organization member. |
| R-9a8487c6ebad | accounts_and_identity | Ownership transfer changes organizational responsibility without creating a new organization. | met | Ownership transfer updates organizational roles. |
| R-bcc3882de051 | accounts_and_identity | The previous owner becomes an administrator or member based on the selection made during the operation. | met | Previous owner transitions to administrator or member. |
| R-45100e7f0262 | accounts_and_identity | Ownership transfers must be logged in administrative activity history. | met | Ownership transfers are logged in activity history. |
| R-5e2d09882c20 | accounts_and_identity | Recovery procedures for ownerless organizations require elevated operational access and are not available as ordinary member workflows. | unclear | Ownerless recovery procedures require external workflows. |
| R-a9e441ee8ded | accounts_and_identity | UnauthorizedException | met | UnauthorizedException is defined. |
| R-8215013f4752 | accounts_and_identity | AuthenticationException | met | AuthenticationException is defined. |
| R-f7781e512337 | accounts_and_identity | InvalidCredentialsException | met | InvalidCredentialsException is defined. |
| R-c84390847c59 | accounts_and_identity | EmailNotVerifiedException | met | EmailNotVerifiedException is defined. |
| R-c95a4a16e2e9 | accounts_and_identity | OrganizationNotFoundException | met | OrganizationNotFoundException is defined. |
| R-aac7b6b41874 | accounts_and_identity | InvitationExpiredException | met | InvitationExpiredException is defined. |
| R-24db26db485d | accounts_and_identity | InvitationRevokedException | met | InvitationRevokedException is defined. |
| R-a205534bc674 | accounts_and_identity | DuplicateOrganizationIdentifierException | met | DuplicateOrganizationIdentifierException is defined. |
| R-6361fd2bedbe | accounts_and_identity | InvalidOrganizationSettingException | met | InvalidOrganizationSettingException is defined. |
| R-bde6b67852c4 | accounts_and_identity | InsufficientAdministrativePrivilegesException | met | InsufficientAdministrativePrivilegesException is defined. |
| R-2611892169bf | accounts_and_identity | DestructiveActionConfirmationRequiredException | met | DestructiveActionConfirmationRequiredException is defined. |
| R-da5272386640 | accounts_and_identity | InsufficientPermissionsException | met | InsufficientPermissionsException is defined. |
| R-3045f443ca32 | accounts_and_identity | RoleAssignmentException | met | RoleAssignmentException is defined. |
| R-2824b836a7b7 | accounts_and_identity | OwnerRemovalException | met | OwnerRemovalException is defined. |
| R-6ff753c221eb | accounts_and_identity | InvalidOwnershipTransferRecipientException | met | InvalidOwnershipRecipientException is defined. |
| R-aeee20ad550f | accounts_and_identity | ConcurrentOwnershipTransferException | met | ConcurrentOwnershipTransferException is defined. |
| R-beace975afb5 | project_membership | Projects provide the primary grouping mechanism for operational work, containing a name, description, creator, owner, status, timestamps, and membership information. | met | Project class stores name, description, creator, owner, status, timestamps, membership. |
| R-6c2d7e0d01ce | project_membership | Project access is considered separately from organization membership; a person outside the organization cannot be added directly to a project. | met | Org membership checked before adding members. |
| R-7c70442a9aa3 | project_membership | When a project is created, the creator normally becomes the initial project owner, and project owners can add organization members to the project. | met | Creator becomes owner; owners add members. |
| R-e1dc1739314b | project_membership | Completing or archiving a project is preferable to permanently deleting it; archived projects disappear from primary selection views but remain accessible to users with sufficient access. | met | Archiving supported; archived projects disappear from selection views. |
| R-fda93e579888 | project_membership | Project names do not need to be globally unique within the organization. | met | No global uniqueness constraint enforced on project names. |
| R-9949eb6077a2 | project_membership | Deleting a project is a destructive operation that must consider dependent work items, comments, attachments, and activity records rather than leaving orphaned data behind. | partial | Check prevents deletion if active work items exist. |
| R-268c6d6f4b4d | project_membership | Project descriptions may contain ordinary formatting but must not be interpreted as executable content. | met | Description stored as ordinary string without execution. |
| R-f3fac93a54bc | project_membership | A project can have a due date, but the absence of a due date is valid and dates should not be invented upon creation. | met | Due date optional, defaults to None. |
| R-dc2a523f7df7 | project_membership | Project membership determines which organization members participate in a particular project, and project owners can add and remove members. | met | Project membership determines participation; owners add/remove. |
| R-2d7956eccbd3 | project_membership | Organization administrators may need equivalent project membership management capabilities for operational reasons. | met | Org admins bypass owner checks. |
| R-9d4e9e1af304 | project_membership | Removing someone from a project causes them to lose access to project-specific information, though broadly visible organization data may remain available. | met | Removed members lose project access. |
| R-988b7a18c6fd | project_membership | Existing work assigned to a removed member should not be automatically deleted or reassigned without human decision. | met | Assigned work not deleted upon member removal. |
| R-309113f02229 | project_membership | When someone leaves a project, their previous comments and recorded activities remain part of the project's history. | met | Comments and activities remain in history log. |
| R-557de6e76dfa | project_membership | A project owner should not be removable through ordinary member-removal actions without another owner being designated to prevent an active project from having no responsible owner. | met | Prevents removal of sole project owner. |
| R-b1979d2f1c7d | project_membership | A work item belongs to one project and at minimum requires a title and status, with optional description, priority, creator, assignee, timestamps, and due date. | met | WorkItem requires title and status. |
| R-2e68c8a3ed1d | project_membership | The title is required for compact representation, while descriptions are optional so a short title-only item is valid. | met | Title required, description optional. |
| R-d8b943e6a81d | project_membership | The initial workflow status model consists of uncompleted, in-progress, and completed states, and items can move backward from complete to active states. | met | Statuses support active/complete transitions. |
| R-c96c24dc781c | project_membership | Priority is represented using a small ordered range rather than arbitrary numeric values. | met | Priority validated against valid set. |
| R-b1cef1b253d9 | project_membership | A work item may have no assignee, and unassigned work is legitimate during planning; assignees are limited to organization members who can access the relevant project. | met | Assignee optional, limited to project members. |
| R-45159f0c0a3c | project_membership | Due dates are calendar dates rather than precise moments, remaining due on that date regardless of the viewer's timezone, and the system distinguishes between absent due dates and due dates set to today. | met | Due date optional string. |
| R-e3a2123552c8 | project_membership | Work items can be reordered within project views to reflect user preference rather than business priority. | met | Work items support order_index reordering. |
| R-a6bcfbee459d | project_membership | Most fields can be changed after creation, and project permissions govern whether a user can modify an item. | met | Permissions checked via project membership and admin status. |
| R-80ff7604203a | project_membership | Changes to titles, statuses, and assignees must be recorded in historical activity. | met | Changes recorded in activity log. |
| R-c031985ea6af | project_membership | A user should be able to remove an optional due date after it has been set, and descriptions may be edited without creating a separate version of the entire project. | met | Due date and description can be set to empty/none. |
| R-fff47bbd976d | project_membership | The API should reject malformed identifiers and invalid state values rather than silently converting them. | unclear | API response format error handling needs broader scope. |
| R-cf6f02a6352d | project_membership | Requests involving an object belonging to another organization should behave as unauthorized or unavailable rather than exposing whether the object exists. | met | Cross-organization access raises CrossOrganizationAccessException. |
| R-29e636f5d386 | project_membership | ProjectNotFoundException | met | Exception defined |
| R-16b32665460f | project_membership | ProjectAccessDeniedException | met | Exception defined |
| R-67b052f0bf9c | project_membership | ProjectDeletionConstraintException | met | Exception defined |
| R-7cc6297e3725 | project_membership | ProjectMembershipNotFoundException | met | Exception defined |
| R-5cb6d3e35414 | project_membership | LastProjectOwnerRemovalException | met | Exception defined |
| R-18a41e826529 | project_membership | WorkItemNotFoundException | met | Exception defined |
| R-432f76c7e412 | project_membership | InvalidStatusTransitionException | met | Exception defined |
| R-35670c4a7b87 | project_membership | InvalidPriorityException | met | Exception defined |
| R-2c5ab5a909aa | project_membership | MalformedIdentifierException | met | Exception defined |
| R-b703312b877f | project_membership | InvalidWorkItemStateException | met | Exception defined |
| R-0f3af35ed623 | project_membership | CrossOrganizationAccessException | met | Exception defined |
| R-992e2ff6b896 | comments_and_discussion | Work items include a discussion area where comments belong directly to the work item without threaded discussions in the first release. | met | Comments belong directly to work items without threads. |
| R-ae98da5abfc2 | comments_and_discussion | A comment has an author, body, creation time, and edited state; users can edit their own comments, and organization administrators may moderate comments. | met | Comment has author, body, time, state, and edit/moderate logic. |
| R-c010228632ef | comments_and_discussion | Deleting a comment indicates content removal in the activity history without pretending the comment never existed. | met | Deletion marks removed content without complete erasure. |
| R-d0baf9f03b72 | comments_and_discussion | Stored comment representation must be treated as untrusted input; the application must escape or safely render user-supplied content to prevent cross-site scripting (XSS). | met | Sanitization and HTML escaping applied to comment bodies. |
| R-8d412c5b8917 | comments_and_discussion | Author and timestamps remain important even when comment text is eventually edited. | met | Author and created_at persist after edits. |
| R-508f5ec9bca8 | comments_and_discussion | Attachments may be uploaded directly to a work item or associated with an individual comment. | met | Attachments can associate with work items or comments. |
| R-eeaa87979c1b | comments_and_discussion | File storage is an implementation concern and the application must not assume uploaded content resides on the same server as the application itself. | met | Storage paths simulate remote separation. |
| R-464c2759dfaf | comments_and_discussion | There should be reasonable limits around uploaded content, and extremely large files must be rejected rather than consuming unlimited storage. | met | File size limits enforced via max_file_size_bytes. |
| R-10e33e08ca13 | comments_and_discussion | User-supplied file names must not be trusted as filesystem paths to prevent path traversal issues. | met | Filename sanitized via os.path.basename. |
| R-fce9f7094ac5 | comments_and_discussion | Two files may have the same display name without representing the same attachment. | met | Unique attachment IDs distinguish identical display names. |
| R-1634fa3cf3ed | comments_and_discussion | Deleting an attachment removes it from normal access, and historical activity can indicate removal without retaining a publicly accessible copy of the file. | met | Deleting attachment clears binary data and path. |
| R-1c24377db6e5 | comments_and_discussion | Attachments can be uploaded directly to a work item or associated with an individual comment. | met | Attachments upload directly or link to comments. |
| R-ae5858d6a6b2 | comments_and_discussion | The application must not assume uploaded content resides on the same server as the application itself. | met | Remote storage paths are used. |
| R-b728798b545a | comments_and_discussion | Reasonable limits must be enforced on uploaded content; extremely large files must be rejected. | met | File size checking rejects large uploads. |
| R-1ef1b6f20b44 | comments_and_discussion | User-supplied filenames must not be trusted as filesystem paths. | met | User filenames are sanitized. |
| R-a047aa806f8e | comments_and_discussion | Multiple files can share the same display name without representing the same attachment. | met | UUID keys allow duplicate display names. |
| R-641487d21dfa | comments_and_discussion | Deleting an attachment removes it from normal access, and historical activity indicates removal without retaining a publicly accessible file copy. | met | Deleted attachments drop publicly accessible file copies. |
| R-3cd56493987a | comments_and_discussion | An attachment belonging to a work item must follow the access rules of that work item. | met | Access checks verify project and org memberships. |
| R-c0a32466d6c2 | comments_and_discussion | Knowing a storage identifier must not be sufficient to retrieve a private file. | met | Knowing an ID does not bypass authorization checks. |
| R-ee0126235a60 | comments_and_discussion | Downloads must be authorized independently from the page displaying the work item. | met | Independent authorization required for downloads. |
| R-57fe3e09059d | comments_and_discussion | Unsupported file formats for inline preview must be offered as downloadable content. | unclear | Content disposition handled statically. |
| R-0020cef11751 | comments_and_discussion | CommentNotFoundException | met | CommentNotFoundException defined. |
| R-b4d6497df557 | comments_and_discussion | CommentModerationPermissionException | met | CommentModerationPermissionException defined. |
| R-11fcb3b9bef4 | comments_and_discussion | UnsafeContentException | met | UnsafeContentException defined. |
| R-d9df3969e714 | comments_and_discussion | AttachmentNotFoundException | met | AttachmentNotFoundException defined. |
| R-eff387de91ce | comments_and_discussion | FileTooLargeException | met | FileTooLargeException defined. |
| R-cd76a6593f8f | comments_and_discussion | InvalidFilePathException | met | InvalidFilePathException defined. |
| R-f4d1a1ccf1e3 | comments_and_discussion | StorageFailureException | met | StorageFailureException defined. |
| R-593b6b95c43c | comments_and_discussion | FileUploadLimitExceededException | met | FileUploadLimitExceededException defined. |
| R-4a0013039b53 | comments_and_discussion | UnauthorizedAttachmentAccessException | met | UnauthorizedAttachmentAccessException defined. |
| R-bdb03b707d78 | notifications | The system notifies users when relevant events occur, such as being assigned a work item, being mentioned in a comment, or updates on followed items. | met | Implemented via generate_assignment_notification, generate_mention_notification, and generate_comment_notification. |
| R-ba899dc0acc6 | notifications | Internal bookkeeping database changes without user-facing significance must not generate notifications. | unclear | No explicit bookkeeping database logic supplied in this module. |
| R-3562ab98dc34 | notifications | Notifications must identify the event with sufficient context for the user to understand why it appeared. | met | Notifications include detailed messages and metadata containing work item and author IDs. |
| R-79a678c3a9b2 | notifications | Notifications can be marked as read without deleting them, and unread items must be distinguished from previously viewed ones. | met | Implemented by mark_notification_as_read and get_unread_notifications. |
| R-3841d5b3272a | notifications | Disabling email notifications does not disable the underlying event or remove in-app notifications unless explicitly defined as the same preference. | met | Email is queued conditionally based on pref.email_enabled without preventing in-app creation. |
| R-49cc48cc445f | notifications | Failed email delivery must not cause the underlying assignment or mention action to be rolled back. | met | Exceptions from email delivery are caught/ignored around _enqueue_email calls. |
| R-4e42a8a72337 | notifications | The system must avoid producing duplicate notifications when the same operation is retried. | met | Implemented via _deduplicate_event and event_key checks. |
| R-fe979c1027fd | notifications | Transactional email is used for account verification, password recovery, invitations, and selected notifications. | met | Implemented via send_transactional_email and create_invitation. |
| R-ee9cfba5c6af | notifications | Emails contain links back to Northstar with temporary credentials or tokens for authentication/invitations without exposing passwords. | met | Emails include temporary tokens without exposing passwords. |
| R-1caf222a861c | notifications | Email templates can be updated independently of main application logic. | unclear | Templates are defined as static data classes within the module. |
| R-bd7322807593 | notifications | Email sending should occur asynchronously where practical to prevent blocking user actions. | met | Emails are dispatched asynchronously via background threads in _enqueue_email. |
| R-1a223b24ac2c | notifications | The system must distinguish between successfully creating an invitation and the attempt to deliver the associated email. | met | Invitation creation successfully returns the token before asynchronously queuing the email. |
| R-6c9839b2ea0e | notifications | Email addresses must not be logged unnecessarily in broadly accessible operational logs. | met | Email addresses are resolved internally and explicitly avoided in logs/prints. |
| R-8ec78cb3799c | notifications | NotificationNotFoundException | met | NotificationNotFoundException is defined and raised when a notification is missing. |
| R-aa8b49e6fba2 | notifications | EmailDeliveryFailedException | met | EmailDeliveryFailedException is defined and raised during simulated send failures. |
| R-ccd530781ed9 | search | Search operates across accessible operational content respecting organization and project access boundaries. | met | Search filters by org and project access. |
| R-3308cc19470b | search | Search is subject to full authorization checks; users cannot discover projects or items they lack permissions to open. | met | Authorization checked during search operations. |
| R-8030851f79f8 | search | Search targets project names, project descriptions, work item titles, work item descriptions, and comments. | partial | Searches title and body; comments not indexed. |
| R-1cf53e4c625d | search | Search results must provide surrounding context to explain why a result was returned. | met | Context snippets extracted around matches. |
| R-6a8170ff8eb6 | search | Partial matching is preferred over requiring exact titles. | met | Substring matching via lower_query in combined_text. |
| R-75557b60a589 | search | Newly created items may have a brief delay before appearing in search results due to asynchronous indexing. | met | Async indexing method provided. |
| R-b084cd11e2e8 | search | Deleting or restricting an object must eventually remove it from search results for users who no longer have access. | met | Remove document method updates index. |
| R-c4fb34ea2e8f | search | Search ranking is not a contractual ordering and exact ranking algorithms must not be guaranteed. | met | No artificial ranking algorithm enforced. |
| R-c8da08726bf5 | search | Summarizes active projects and work assigned to the current user. | met | Dashboard summarizes active projects and assigned work. |
| R-bf8203247e8f | search | Completed and archived work must not dominate the default dashboard view. | met | Completed items filtered out of recently updated items. |
| R-699b97369bbd | search | A user with no assigned work must receive a useful empty state rather than a technical error. | met | Empty state checked when no active projects or work. |
| R-322376a84068 | search | Recently updated items refer strictly to meaningful user-facing changes rather than arbitrary database timestamp modifications. | met | Recently updated sorts by meaningful updates. |
| R-283747f88fdc | search | Organization timezone must be considered when presenting date-oriented information. | met | Relative date calculated using user timezone. |
| R-dac4dccf70a0 | search | Dashboard counts must be derived from current accessible data and dynamically reflect items that are removed or become inaccessible. | met | Dashboard counts derived from current accessible data. |
| R-8c0aabff3e06 | search | Records significant activities including project creation, ownership changes, member changes, work item creation, assignment changes, status changes, and administrative actions. | missing | No activity logging implemented in module. |
| R-6975c4fcc79b | search | Activities must include the actor where identifiable, or reflect system-generated status if no human actor exists. | missing | No activity logging implemented in module. |
| R-bb4fc7e7fb13 | search | Activities must contain consistently interpretable timestamps. | missing | No activity logging implemented in module. |
| R-5c989e187f12 | search | Internal operational tasks (search indexing, cache refreshes, email retries) must not appear as user activity. | missing | No activity logging implemented in module. |
| R-700461b80b4f | search | Historical activity remains intelligible if an actor's display name changes or if a user is deactivated/removed. | missing | No activity logging implemented in module. |
| R-af4291ed5577 | search | Activity records are append-only; ordinary users cannot modify or rewrite history. | missing | No activity logging implemented in module. |
| R-c98016443dd8 | search | Administrators may be granted broader access to activity information than ordinary project participants. | missing | No activity logging implemented in module. |
| R-b71d4e35b067 | search | Visibility follows a strict hierarchy: Organization -&gt; Project -&gt; Work Item -&gt; Comments/Attachments. | unclear | Child object hierarchy authorization depends on omitted source. |
| R-51dd59ab58d3 | search | API endpoints returning child objects (e.g., comments, attachments) must explicitly verify authorization against the parent object and project membership. | unclear | API endpoint authorization depends on omitted source. |
| R-cc27568b6ed5 | search | No unauthenticated access is permitted; private projects cannot be accessed via shared URLs without authentication. | met | Unauthenticated access raises exception. |
| R-323f571f23da | search | SearchQueryFormatException | met | SearchQueryFormatException defined and raised. |
| R-8bfe7bc41530 | search | ActivityLogImmutableException | met | ActivityLogImmutableException defined. |
| R-0109de65c25e | search | UnauthorizedAccessDeniedException | met | UnauthorizedAccessDeniedException defined and raised. |
| R-0074de313f9c | Project-wide | Server-side authorization checks are mandatory for all operations and cannot rely solely on hiding interface elements. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-e5dfbb1fffdc | Project-wide | Strict organization isolation must be enforced across all web and API requests to prevent cross-tenant data access. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-6368bc8327d2 | Project-wide | Requests referencing objects from other organizations must return unauthorized or unavailable responses without disclosing object existence. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-4f66b3b318c2 | Project-wide | Historical activities, past assignments, and audit trails must be preserved when users are removed from organizations or projects, or when items are modified or deleted. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-8fa658b1e790 | Project-wide | Data deletion must be handled carefully, utilizing archiving or soft deletion where appropriate to avoid breaking historical references and dependent records. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-e4d085c1716a | Project-wide | The API must reject malformed identifiers, invalid state values, and oversized payloads rather than performing silent conversions. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-d1ac7971eef6 | Project-wide | User-supplied input, including project descriptions and comments, must be treated as untrusted and safely escaped or rendered to prevent code execution and XSS attacks. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-5ff36c906d08 | Project-wide | User-supplied file names must be sanitized and never trusted directly as filesystem paths. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-89e38f2381ef | Project-wide | Stored timestamps must remain unambiguous regardless of the viewer's physical location. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-3fa0d5b9ae39 | Project-wide | Organization-level timezone settings govern the presentation of dates and scheduled events. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-a4fbb3ce1b60 | Project-wide | Due dates for work items represent calendar dates and remain constant regardless of the viewer's timezone. | unclear | Viewer timezone handling |
| R-38fe440a9589 | Project-wide | Resource identifiers exposed to clients must be safe, and authorization must never depend on the difficulty of guessing an identifier. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-e1a79b84d6ba | Project-wide | Validation errors must be clearly distinguishable from authorization failures and server errors. | unclear | Distinguished in search_management.py but absent in others. |
| R-f56585d607bb | Project-wide | Malformed requests must not expose stack traces or implementation details in standard API responses. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-7f06983cde44 | Project-wide | Modifying operations must return sufficient resource information for clients to update local state without full page reloads. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-c10c3a3d4a38 | Project-wide | Pagination is mandatory for growing collections (members, projects, notifications, search results, activity feeds). | unclear | Limit/offset present |
| R-9100a515efbb | Project-wide | Paginated results must maintain stable ordering to prevent skipped or duplicated records during navigation. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-645f51a90e24 | Project-wide | The system must allow concurrent edits to different fields of a work item without corrupting unrelated data. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-bba7dd916861 | Project-wide | Users viewing stale data must not unknowingly overwrite newer changes where data integrity matters. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-58d55e0672c6 | Project-wide | Critical single-execution operations (such as invitation acceptance or ownership transfer) must prevent duplicate concurrent execution. | unclear | Thread locks present, but explicit concurrency flags missing. |
| R-c5561f484fde | Project-wide | Client and infrastructure retries must be handled as normal operations using idempotency mechanisms to avoid duplicate logical records. | unclear | Versioning check |
| R-768eb2df8d95 | Project-wide | Core entity creation/updates must not be rolled back or failed due to failures in secondary dependencies (e.g., email delivery, search indexing, object storage). | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-9bfa303e49ab | Project-wide | Failed secondary processes must be deferred to background retries. | unclear | Failed emails are ignored rather than retried. |
| R-e8da30182a31 | Project-wide | Asynchronous background processing should be used for email sending, search indexing, notification generation, and file processing. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-16395c6ca952 | Project-wide | Background jobs must contain full explicit context (organization ID, resource ID) without depending on web session state. | partial | Background jobs have optional organization context fallback. |
| R-39a40fad3329 | Project-wide | Jobs that fail repeatedly must not retry indefinitely without operator visibility and investigation tooling. | missing | No retry limits or visibility tools implemented. |
| R-b186955cdc18 | Project-wide | User-supplied filenames must be sanitized to prevent path traversal attacks (e.g., relative directory sequences like '../../'). | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-9070a35e7bd0 | Project-wide | File contents must not be automatically interpreted or rendered as HTML/executable code by default. | unclear | No file download handling or rendering mechanism found in the provided source. |
| R-5778f0a2ed94 | Project-wide | Content-Disposition headers must be configured appropriately for file downloads. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-07ab9032882a | Project-wide | Authentication and authorization must be enforced prior to serving private files or generating download mechanisms. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-5762bdd88a1d | Project-wide | Temporary file access links must have limited TTL lifetimes. | unclear | Temporary file access link TTL lifetimes not found. |
| R-79997b1c8596 | Project-wide | File upload size limits must be enforced prior to processing unbounded data transfers. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-2b73a91969d5 | Project-wide | Event timestamps must be stored with unambiguous timezone interpretations (UTC). | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-5bb21a12ecf2 | Project-wide | Work item due dates represent fixed calendar days rather than exact instantaneous timestamps and must remain invariant across user timezones. | unclear | String based dates |
| R-32fc09a96a48 | Project-wide | Relative date labels ('today', 'tomorrow') must be calculated dynamically based on user/organization context. | unclear | Relevant supplied code supports this rule; project-wide enforcement needs omitted implementation context. |
| R-4fde7429986b | Project-wide | Daylight-saving transitions must be accounted for without assuming calendar days have uniform hour lengths. | unclear | ZoneInfo usage |

## Remaining findings

### F-50de28ad719b: defect (medium)

File: project_membership.py, line 328.
Requirements: R-9949eb6077a2

Deletion constraint check fails to handle dependent comments, attachments, and activity records.

Suggested correction: Extend delete_project validation to check for dependent comments, attachments, and activity records before deletion.

Requirement evidence: Deleting a project is a destructive operation that must consider dependent work items, comments, attachments, and activity records rather than leaving orphaned data behind.

Code evidence: associated_items = [item for item in self.work_items.values() if item.project_id == p_id]

Counterexample: Deleting a project with existing comments or activity records leaves orphaned data.

### F-ff46ebce3a98: suggestion (low)

File: comments_and_discussion.py, line 349.
Requirements: R-57fe3e09059d

Inline preview disposition hardcoded without dynamic negotiation.

Suggested correction: Allow caller override or extend preview format rules.

Requirement evidence: Unsupported file formats for inline preview must be offered as downloadable content.

Code evidence: content_disposition = "inline" if attachment.content_type in inline_safe_types else "attachment"

Counterexample: An unsupported format rendered unexpectedly as inline.

### F-fadfd41f154b: defect (medium)

File: search_management.py, line 59.
Requirements: R-8030851f79f8

Search targets do not include comments as requested.

Suggested correction: Add comment content into searchable text index.

Requirement evidence: Search targets project names, project descriptions, work item titles, work item descriptions, and comments.

Code evidence: combined_text = f"{doc.title} {doc.body}".lower()

Counterexample: Searching for a term present only in a work item comment returns no results.

### F-3b88b0afd543: defect (medium)

File: search_management.py, line unspecified.
Requirements: R-8c0aabff3e06, R-6975c4fcc79b, R-bb4fc7e7fb13, R-5c989e187f12, R-700461b80b4f, R-af4291ed5577, R-c98016443dd8

Activity logging and administrative activity controls are absent from this module.

Suggested correction: Implement activity tracking classes and append-only logs.

Requirement evidence: Records significant activities including project creation

Code evidence: class SearchManager:

Counterexample: Performing administrative actions fails to generate an append-only activity log entry.

### F-1fcd5dc4c572: defect (medium)

File: notification_management.py, line 253.
Requirements: R-16395c6ca952

Background jobs fall back to a default organization ID if not provided explicitly.

Suggested correction: Require explicit organization ID parameter in background job queue calls.

Requirement evidence: Background jobs must contain full explicit context

Code evidence: org_id = organization_id or uuid.UUID("00000000-0000-0000-0000-000000000000")

Counterexample: Queueing an email without organization_id defaults to nil UUID.

### F-0cd0d81e1b1f: uncertain (medium)

File: comments_and_discussion.py, line unspecified.
Requirements: R-5762bdd88a1d

No implementation for temporary file access links with limited TTL lifetimes was found.

Suggested correction: Implement signed temporary URLs with expiration timestamps for file attachments.

Requirement evidence: Temporary file access links must have limited TTL lifetimes.

Code evidence: def download_attachment(

Counterexample: Attachments are retrieved directly without expiration checking.

### F-dac971a4193f: defect (medium)

File: notification_management.py, line 286.
Requirements: R-39a40fad3329

Failed background jobs lack retry tracking or operator visibility.

Suggested correction: Implement persistent retry queues with failure counters.

Requirement evidence: Jobs that fail repeatedly must not retry indefinitely without operator visibility

Code evidence: thread = threading.Thread(target=worker, daemon=True)

Counterexample: An email send fails repeatedly without logging or alerting an operator.

## Review limitations

- Static LLM review only; runtime behavior and tests have not been verified.
- Supplementary repository context is limited to 6 KB of tracked Python/configuration/documentation files.
- Review requests may further limit supplementary context to 2 KB and shorten interface outlines; full supplied source remains authoritative.
- Static code review cannot verify runtime behavior or external dependencies.
- Static review does not prove runtime correctness.
- Static code review cannot verify runtime behavior.
- Static code review cannot verify asynchronous thread safety at runtime.
- Static analysis cannot verify runtime behavior or external module interactions.
- Project-wide checks omitted some full source files; unsupported absence claims remain unclear.
- Static code review does not verify runtime environment behavior or thread safety guarantees under high concurrency.
- Static review does not prove runtime correctness or thread safety.
- File rendering behavior (R1) relies on an absent presentation layer.
- Unverifiable model line numbers were omitted; inspect the cited source and quoted evidence.
- Supplementary files omitted: administration_management.py, work_item_editing.py

This report was assembled from saved requirements, approved code, the repository baseline, and the current critic report. No additional model call was made.
