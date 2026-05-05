from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from database import db

router = APIRouter(prefix="/contributors", tags=["contributors"])


@router.get("")
def list_contributors(
    repo: Optional[str] = None,
    is_core: Optional[bool] = None,
    is_newcomer: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
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


@router.get("/{username}")
def get_contributor(username: str, repo: Optional[str] = None):
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


@router.get("/{username}/events")
def get_contributor_events(
    username: str,
    repo: Optional[str] = None,
    event_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
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


@router.get("/{username}/status-history")
def get_contributor_status_history(
    username: str,
    repo: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
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


@router.get("/{username}/monthly-activity")
def get_contributor_monthly_activity(
    username: str,
    repo: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
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
