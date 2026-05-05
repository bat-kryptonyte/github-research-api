from fastapi import APIRouter, Query
from typing import Optional
from database import db

router = APIRouter(prefix="/commits", tags=["commits"])


@router.get("")
def list_commits(
    repo: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
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


@router.get("/{sha}")
def get_commit(sha: str):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM master_commit_index WHERE sha = ?", (sha,)
        ).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Commit not found")
    return dict(row)
