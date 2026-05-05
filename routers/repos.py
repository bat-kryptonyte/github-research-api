from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from database import db

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("")
def list_repos(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    offset = (page - 1) * per_page
    with db() as conn:
        total = conn.execute("SELECT COUNT(DISTINCT repo) FROM pr_analysis").fetchone()[0]
        rows = conn.execute(
            """
            SELECT repo,
                   COUNT(*) AS total_prs,
                   SUM(merged_detected) AS merged_prs,
                   ROUND(AVG(num_comments), 2) AS avg_comments,
                   ROUND(AVG(time_to_decision_mins), 2) AS avg_time_to_decision_mins
            FROM pr_analysis
            GROUP BY repo
            ORDER BY repo
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        ).fetchall()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "repos": [dict(r) for r in rows],
    }


@router.get("/{repo:path}/prs")
def list_prs(
    repo: str,
    author: Optional[str] = None,
    merged: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    offset = (page - 1) * per_page
    filters = ["repo = ?"]
    params: list = [repo]

    if author:
        filters.append("author = ?")
        params.append(author)
    if merged is not None:
        filters.append("merged_detected = ?")
        params.append(int(merged))

    where = " AND ".join(filters)

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM pr_analysis WHERE {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM pr_analysis
            WHERE {where}
            ORDER BY pr_number
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "prs": [dict(r) for r in rows],
    }


@router.get("/{repo:path}/prs/{pr_number}")
def get_pr(repo: str, pr_number: int):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM pr_analysis WHERE repo = ? AND pr_number = ?",
            (repo, pr_number),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="PR not found")
    return dict(row)


@router.get("/{repo:path}/contributors")
def list_repo_contributors(
    repo: str,
    is_core: Optional[bool] = None,
    is_newcomer: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    offset = (page - 1) * per_page
    filters = ["repo = ?"]
    params: list = [repo]

    if is_core is not None:
        filters.append("is_core = ?")
        params.append(int(is_core))
    if is_newcomer is not None:
        filters.append("is_newcomer = ?")
        params.append(int(is_newcomer))

    where = " AND ".join(filters)

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM contributor_lifecycle WHERE {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM contributor_lifecycle
            WHERE {where}
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


@router.get("/{repo:path}/monthly-activity")
def repo_monthly_activity(
    repo: str,
    user_login: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
):
    offset = (page - 1) * per_page
    filters = ["repo = ?"]
    params: list = [repo]

    if user_login:
        filters.append("user_login = ?")
        params.append(user_login)

    where = " AND ".join(filters)

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM bq_4_month_level_aggregation WHERE {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM bq_4_month_level_aggregation
            WHERE {where}
            ORDER BY user_login
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


@router.get("/{repo:path}/status-history")
def repo_status_history(
    repo: str,
    user_login: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
):
    offset = (page - 1) * per_page
    filters = ["repo = ?"]
    params: list = [repo]

    if user_login:
        filters.append("user_login = ?")
        params.append(user_login)
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
            ORDER BY month_year, user_login
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
