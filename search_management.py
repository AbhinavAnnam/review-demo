class SearchAuthorizationException(Exception):
    """Raised when a user attempts to search across resources or organizations they lack access to."""
    pass


class SearchIndexingException(Exception):
    """Raised when there is a failure in processing or indexing search documents asynchronously."""
    pass


class DashboardDataUnavailableException(Exception):
    """Raised when dashboard summaries cannot be compiled due to dependent data or timezone issues."""
    pass


class SearchQueryFormatException(Exception):
    """Raised when the search query is malformed or improperly structured."""
    pass


class ActivityLogImmutableException(Exception):
    """Raised when an attempt is made to mutate or rewrite immutable activity log records."""
    pass


class UnauthorizedAccessDeniedException(Exception):
    """Raised when unauthenticated or unauthorized access is attempted on protected search or dashboard resources."""
    pass


import datetime
from typing import List, Dict, Any, Optional, Set
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class SearchIndexDocument:
    def __init__(self, doc_id: str, org_id: str, project_id: Optional[str], content_type: str, title: str, body: str):
        self.doc_id = doc_id
        self.org_id = org_id
        self.project_id = project_id
        self.content_type = content_type
        self.title = title
        self.body = body


class SearchManager:
    def __init__(self):
        self.index: List[SearchIndexDocument] = []

    def async_index_document(self, document: SearchIndexDocument) -> None:
        try:
            self.index = [doc for doc in self.index if doc.doc_id != document.doc_id]
            self.index.append(document)
        except Exception as e:
            raise SearchIndexingException(f"Failed to asynchronously index document {document.doc_id}: {str(e)}")

    def remove_document(self, doc_id: str) -> None:
        try:
            self.index = [doc for doc in self.index if doc.doc_id != doc_id]
        except Exception as e:
            raise SearchIndexingException(f"Failed to remove document {doc_id} from index: {str(e)}")

    def search(self, user_org_id: str, accessible_project_ids: List[str], query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not user_id:
            raise UnauthorizedAccessDeniedException("Unauthenticated access is strictly prohibited for search operations.")
        if not user_org_id:
            raise SearchAuthorizationException("Organization context is mandatory for executing searches.")
        if not query or not isinstance(query, str):
            raise SearchQueryFormatException("Search query must be a valid non-empty string.")

        results: List[Dict[str, Any]] = []
        lower_query = query.lower().strip()
        if not lower_query:
            raise SearchQueryFormatException("Search query cannot be empty or whitespace only.")

        accessible_project_set = set(accessible_project_ids)

        for doc in self.index:
            if doc.org_id != user_org_id:
                continue

            if doc.project_id is not None and doc.project_id not in accessible_project_set:
                continue

            combined_text = f"{doc.title} {doc.body}".lower()
            if lower_query in combined_text:
                snippet = self._extract_context_snippet(doc.body, lower_query)
                results.append({
                    "doc_id": doc.doc_id,
                    "org_id": doc.org_id,
                    "project_id": doc.project_id,
                    "content_type": doc.content_type,
                    "title": doc.title,
                    "matched_context": snippet
                })

        return results

    def _extract_context_snippet(self, body: str, lower_query: str) -> str:
        lower_body = body.lower()
        idx = lower_body.find(lower_query)
        if idx == -1:
            return body[:100] + ("..." if len(body) > 100 else "")

        start = max(0, idx - 40)
        end = min(len(body), idx + len(lower_query) + 40)
        snippet = body[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(body):
            snippet = snippet + "..."
        return snippet


class DashboardManager:
    def __init__(self, search_manager: SearchManager):
        self.search_manager = search_manager

    def _calculate_relative_date(self, due_date_str: Optional[str], user_timezone: str) -> Optional[str]:
        if not due_date_str:
            return None
        try:
            try:
                tz = ZoneInfo(user_timezone)
            except (ZoneInfoNotFoundError, Exception):
                tz = datetime.timezone.utc

            now_local = datetime.datetime.now(tz).date()

            parsed_date = None
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    parsed_date = datetime.datetime.strptime(due_date_str[:19], fmt).date()
                    break
                except ValueError:
                    continue

            if not parsed_date:
                try:
                    parsed_date = datetime.date.fromisoformat(due_date_str[:10])
                except ValueError:
                    return due_date_str

            delta_days = (parsed_date - now_local).days
            if delta_days == 0:
                return "today"
            elif delta_days == 1:
                return "tomorrow"
            elif delta_days == -1:
                return "yesterday"
            elif delta_days > 1:
                return f"in {delta_days} days"
            else:
                return f"{abs(delta_days)} days ago"
        except Exception:
            return due_date_str

    def get_user_dashboard(self, user_id: str, org_id: str, user_timezone: str, projects: List[Dict[str, Any]], work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not user_id:
            raise UnauthorizedAccessDeniedException("Unauthenticated access to dashboard views is forbidden.")
        if not org_id:
            raise SearchAuthorizationException("Organization identifier is required to load the dashboard.")

        try:
            accessible_projects = [p for p in projects if p.get("org_id") == org_id and not p.get("archived", False)]
            accessible_project_ids = {p.get("project_id") for p in accessible_projects}

            active_projects = [
                {
                    "project_id": p.get("project_id"),
                    "name": p.get("name"),
                    "description": p.get("description")
                }
                for p in accessible_projects
            ]

            assigned_work = []
            for item in work_items:
                if item.get("org_id") != org_id:
                    continue
                if item.get("assignee_id") != user_id:
                    continue
                if item.get("project_id") not in accessible_project_ids:
                    continue
                if item.get("status") in ["completed", "archived", "closed"]:
                    continue
                
                due_date_str = item.get("due_date")
                relative_due_date = self._calculate_relative_date(due_date_str, user_timezone)

                assigned_work.append({
                    "work_item_id": item.get("work_item_id"),
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "due_date": due_date_str,
                    "relative_due_date": relative_due_date,
                    "status": item.get("status")
                })

            recently_updated = []
            sorted_items = sorted(
                [i for i in work_items if i.get("org_id") == org_id and i.get("project_id") in accessible_project_ids and i.get("status") not in ["completed", "archived", "closed"]],
                key=lambda x: x.get("last_meaningful_update", x.get("updated_at", "")),
                reverse=True
            )
            for item in sorted_items[:5]:
                recently_updated.append({
                    "work_item_id": item.get("work_item_id"),
                    "title": item.get("title"),
                    "last_meaningful_update": item.get("last_meaningful_update", item.get("updated_at"))
                })

            empty_state = False
            if not assigned_work and not active_projects:
                empty_state = True

            return {
                "organization_timezone": user_timezone,
                "active_projects": active_projects,
                "assigned_work": assigned_work,
                "recently_updated_items": recently_updated,
                "summary_counts": {
                    "active_projects_count": len(active_projects),
                    "assigned_work_count": len(assigned_work)
                },
                "is_empty_state": empty_state,
                "empty_state_message": "You have no active projects or assigned work items at this time." if empty_state else None
            }
        except Exception as e:
            raise DashboardDataUnavailableException(f"Unable to compile dashboard data for user {user_id}: {str(e)}")