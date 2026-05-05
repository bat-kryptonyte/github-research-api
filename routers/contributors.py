from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from database import db
from models import ContributorList, ContributorDetail, EventList, StatusHistoryList, MonthlyActivityList

router = APIRouter(prefix="/contributors", tags=["contributors"])


@router.get(
    "",
    summary="List all contributors",
    description=(
        "Returns contributor lifecycle records across all repos. "
        "Filter by `repo`, `is_core`, and/or `is_newcomer`. "
        "Sorted by total event count descending."
    ),
    response_model=ContributorList,
)
def list_contributors(
    repo: Optional[str] = Query(None, description="Filter to a specific repository slug"),
    is_core: Optional[bool] = Query(None, description="Filter to core contributors only"),
    is_newcomer: Optional[bool] = Query(None, description="Filter to newcomers only"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
):
    offset = (page - 1) * per_page
    filters = []
    params: list = []

    if repo:
        filters.append("repo = ?")
        params.append(repo)
    if is_core is not None:
        filters.append("is_core = ?")
        params.append(int(is_core))
    if is_newcomer is not None:
        filters.append("is_newcomer = ?")
        params.append(int(is_newcomer))

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM contributor_lifecycle {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM contributor_lifecycle
            {where}
            ORDER BY total_event_count DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "contributors": [dict(r) for r in rows],
    }


@router.get(
    "/{username}",
    summary="Get a contributor's profile",
    description=(
        "Returns lifecycle records for the given GitHub username across all repos they appear in. "
        "Optionally scope to a single `repo`."
    ),
    response_model=ContributorDetail,
)
def get_contributor(
    username: str,
    repo: Optional[str] = Query(None, description="Scope to a specific repository slug"),
):
    filters = ["user_login = ?"]
    params: list = [username]

    if repo:
        filters.append("repo = ?")
        params.append(repo)

    where = " AND ".join(filters)

    with db() as conn:
        rows = conn.execute(
            f"SELECT * FROM contributor_lifecycle WHERE {where} ORDER BY repo",
            params,
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Contributor not found")

    return {"username": username, "repos": [dict(r) for r in rows]}


@router.get(
    "/{username}/events",
    summary="Get events for a contributor",
    description=(
        "Returns raw timestamped events (commits, issues, PRs) for the given username. "
        "Filter by `repo` and/or `event_type` (one of: issues, prs, commits)."
    ),
    response_model=EventList,
)
def get_contributor_events(
    username: str,
    repo: Optional[str] = Query(None, description="Filter to a specific repository slug"),
    event_type: Optional[str] = Query(
        None, description="Filter by event type. One of: issues, prs, commits"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=500, description="Results per page (max 500)"),
):
    offset = (page - 1) * per_page
    filters = ["username = ?"]
    params: list = [username]

    if repo:
        filters.append("repo = ?")
        params.append(repo)
    if event_type:
        filters.append("event_type = ?")
        params.append(event_type)

    where = " AND ".join(filters)

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM contributor_events WHERE {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM contributor_events
            WHERE {where}
            ORDER BY timestamp
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "events": [dict(r) for r in rows],
    }


@router.get(
    "/{username}/status-history",
    summary="Get status history for a contributor",
    description=(
        "Returns the month-by-month contributor status (active, at-risk, disengaged, returning) "
        "for the given username. Filter by `repo` and/or `status`."
    ),
    response_model=StatusHistoryList,
)
def get_contributor_status_history(
    username: str,
    repo: Optional[str] = Query(None, description="Filter to a specific repository slug"),
    status: Optional[str] = Query(
        None,
        description="Filter by status. One of: active, at-risk, disengaged, returning",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=500, description="Results per page (max 500)"),
):
    offset = (page - 1) * per_page
    filters = ["user_login = ?"]
    params: list = [username]

    if repo:
        filters.append("repo = ?")
        params.append(repo)
    if status:
        filters.append("current_status = ?")
        params.append(status)

    where = " AND ".join(filters)

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM contributor_status_history WHERE {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM contributor_status_history
            WHERE {where}
            ORDER BY month_year
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "history": [dict(r) for r in rows],
    }


@router.get(
    "/{username}/monthly-activity",
    summary="Get monthly activity for a contributor",
    description=(
        "Returns per-month activity counts (commits, issues, PRs, etc.) "
        "for the given username. Optionally scope to a single `repo`."
    ),
    response_model=MonthlyActivityList,
)
def get_contributor_monthly_activity(
    username: str,
    repo: Optional[str] = Query(None, description="Filter to a specific repository slug"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=500, description="Results per page (max 500)"),
):
    offset = (page - 1) * per_page
    filters = ["user_login = ?"]
    params: list = [username]

    if repo:
        filters.append("repo = ?")
        params.append(repo)

    where = " AND ".join(filters)

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM bq_4_month_level_aggregation WHERE {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM bq_4_month_level_aggregation
            WHERE {where}
            ORDER BY repo
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "activity": [dict(r) for r in rows],
    }
