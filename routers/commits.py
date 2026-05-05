from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from database import db
from models import CommitList, Commit

router = APIRouter(prefix="/commits", tags=["commits"])


@router.get(
    "",
    summary="List commits",
    description=(
        "Returns commits from the master commit index, sorted newest-first. "
        "Optionally filter to a single `repo`."
    ),
    response_model=CommitList,
)
def list_commits(
    repo: Optional[str] = Query(None, description="Filter to a specific repository slug"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=500, description="Results per page (max 500)"),
):
    offset = (page - 1) * per_page
    filters = []
    params: list = []

    if repo:
        filters.append("repo = ?")
        params.append(repo)

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM master_commit_index {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM master_commit_index
            {where}
            ORDER BY committed_date DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "commits": [dict(r) for r in rows],
    }


@router.get(
    "/{sha}",
    summary="Get a single commit",
    description="Returns the commit record for the given full 40-character SHA.",
    response_model=Commit,
)
def get_commit(sha: str):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM master_commit_index WHERE sha = ?", (sha,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Commit not found")
    return dict(row)
