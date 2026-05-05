from fastapi import APIRouter, Query
from typing import Optional
from database import db
from models import FeatureList

router = APIRouter(prefix="/features", tags=["features"])


def _query_features(
    table: str,
    repo: Optional[str],
    author: Optional[str],
    is_core: Optional[bool],
    is_newcomer: Optional[bool],
    page: int,
    per_page: int,
):
    offset = (page - 1) * per_page
    filters = []
    params: list = []

    if repo:
        filters.append("repo = ?")
        params.append(repo)
    if author:
        filters.append("author = ?")
        params.append(author)
    if is_core is not None:
        filters.append("is_core = ?")
        params.append(int(is_core))
    if is_newcomer is not None:
        filters.append("is_newcomer = ?")
        params.append(int(is_newcomer))

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM {table} {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM {table} {where} ORDER BY repo, author LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "features": [dict(r) for r in rows],
    }


@router.get(
    "",
    summary="Raw ML features",
    description=(
        "Returns log-transformed ML features per author×repo combination. "
        "Features include PR-level averages, author history signals, and monthly activity counts. "
        "Filter by `repo`, `author`, `is_core`, or `is_newcomer`."
    ),
    response_model=FeatureList,
)
def get_features(
    repo: Optional[str] = Query(None, description="Filter to a specific repository slug"),
    author: Optional[str] = Query(None, description="Filter to a specific GitHub username"),
    is_core: Optional[bool] = Query(None, description="Filter to core contributors only"),
    is_newcomer: Optional[bool] = Query(None, description="Filter to newcomers only"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
):
    return _query_features("features", repo, author, is_core, is_newcomer, page, per_page)


@router.get(
    "/standardized",
    summary="Z-score-standardized ML features",
    description=(
        "Returns the same features as `/features` but with continuous columns "
        "z-score-standardized (mean 0, std 1) across the full dataset. "
        "Intended for direct use in ML models. Supports the same filters."
    ),
    response_model=FeatureList,
)
def get_features_standardized(
    repo: Optional[str] = Query(None, description="Filter to a specific repository slug"),
    author: Optional[str] = Query(None, description="Filter to a specific GitHub username"),
    is_core: Optional[bool] = Query(None, description="Filter to core contributors only"),
    is_newcomer: Optional[bool] = Query(None, description="Filter to newcomers only"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
):
    return _query_features("features_standardized", repo, author, is_core, is_newcomer, page, per_page)
