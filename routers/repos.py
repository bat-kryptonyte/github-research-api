from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from database import db
from models import RepoList, PRList, PR, ContributorList, MonthlyActivityList, StatusHistoryList

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get(
    "",
    summary="List all repositories",
    description=(
        "Returns one row per repository with aggregated PR statistics: "
        "total PRs, merged count, average comment count, and average time-to-decision."
    ),
    response_model=RepoList,
)
def list_repos(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
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


@router.get(
    "/{repo:path}/prs",
    summary="List PRs for a repository",
    description=(
        "Returns pull requests for the given repo. "
        "Filter by `author` (GitHub username) and/or `merged` (true/false). "
        "Repo names with slashes must be URL-encoded (e.g. `huggingface%2Ftransformers`)."
    ),
    response_model=PRList,
)
def list_prs(
    repo: str,
    author: Optional[str] = Query(None, description="Filter by PR author username"),
    merged: Optional[bool] = Query(None, description="Filter by merge status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
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


@router.get(
    "/{repo:path}/prs/{pr_number}",
    summary="Get a single PR",
    description="Returns the full PR record for the given repo and PR number.",
    response_model=PR,
)
def get_pr(repo: str, pr_number: int):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM pr_analysis WHERE repo = ? AND pr_number = ?",
            (repo, pr_number),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="PR not found")
    return dict(row)


@router.get(
    "/{repo:path}/contributors",
    summary="List contributors for a repository",
    description=(
        "Returns contributor lifecycle records for the given repo. "
        "Filter by `is_core` or `is_newcomer` to narrow to a classification tier."
    ),
    response_model=ContributorList,
)
def list_repo_contributors(
    repo: str,
    is_core: Optional[bool] = Query(None, description="Filter to core contributors only"),
    is_newcomer: Optional[bool] = Query(None, description="Filter to newcomers only"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
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


@router.get(
    "/{repo:path}/monthly-activity",
    summary="Monthly activity for a repository",
    description=(
        "Returns per-user monthly activity counts (commits, issues, PRs, etc.) "
        "for the given repo. Optionally filter to a single `user_login`."
    ),
    response_model=MonthlyActivityList,
)
def repo_monthly_activity(
    repo: str,
    user_login: Optional[str] = Query(None, description="Filter to a specific GitHub username"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=500, description="Results per page (max 500)"),
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


@router.get(
    "/{repo:path}/status-history",
    summary="Contributor status history for a repository",
    description=(
        "Returns the month-by-month contributor status (active, at-risk, disengaged, returning) "
        "for all users in the given repo. Filter by `user_login` and/or `status`."
    ),
    response_model=StatusHistoryList,
)
def repo_status_history(
    repo: str,
    user_login: Optional[str] = Query(None, description="Filter to a specific GitHub username"),
    status: Optional[str] = Query(
        None,
        description="Filter by status. One of: active, at-risk, disengaged, returning",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=500, description="Results per page (max 500)"),
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
