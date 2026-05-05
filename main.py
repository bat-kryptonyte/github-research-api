from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import repos, contributors, features, commits
from database import db
from models import HealthResponse, StatsResponse

app = FastAPI(
    title="GitHub Research API",
    description="""
REST API over the **github_research_v1** dataset — pull requests, contributor lifecycle,
events, status history, commits, and ML features across **200 open-source GitHub repositories**.

## Data coverage
| Table | Description |
|---|---|
| `pr_analysis` | Per-PR metadata: merge status, timing, size, author |
| `contributor_lifecycle` | Newcomer/core classification, tenure, event counts |
| `contributor_events` | Raw timestamped events (commits, issues, PRs) |
| `contributor_status_history` | Monthly contributor status (active / at-risk / disengaged / returning) |
| `master_commit_index` | Full commit index with SHAs and timestamps |
| `features` / `features_standardized` | Log-transformed (and z-scored) ML features per author×repo |
| `bq_4_month_level_aggregation` | Monthly activity counts per user×repo |

## Pagination
All list endpoints support `page` (default 1) and `per_page` query parameters.

## Repo name encoding
Repository names contain slashes (e.g. `huggingface/transformers`).
URL-encode them as `huggingface%2Ftransformers` when used in **path segments**.
""",
    version="1.0.0",
    contact={
        "name": "cdeng65",
        "url": "https://github.com/cdeng65",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "meta",
            "description": "Health check and dataset-wide row counts.",
        },
        {
            "name": "repos",
            "description": (
                "Per-repository PR summaries, contributor lists, monthly activity, "
                "and contributor status history."
            ),
        },
        {
            "name": "contributors",
            "description": (
                "Cross-repo contributor profiles, raw events, monthly activity "
                "aggregations, and status history."
            ),
        },
        {
            "name": "features",
            "description": (
                "Log-transformed ML features and their z-score-standardized counterparts "
                "for PR-success prediction models."
            ),
        },
        {
            "name": "commits",
            "description": "Master commit index — lookup by SHA or filter by repo.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(repos.router)
app.include_router(contributors.router)
app.include_router(features.router)
app.include_router(commits.router)


@app.get(
    "/health",
    tags=["meta"],
    summary="Health check",
    response_model=HealthResponse,
)
def health():
    return {"status": "ok"}


@app.get(
    "/stats",
    tags=["meta"],
    summary="Dataset statistics",
    description="Returns the row count for each major table and the number of distinct repositories.",
    response_model=StatsResponse,
)
def stats():
    counts = {}
    tables = [
        "pr_analysis",
        "contributor_lifecycle",
        "contributor_events",
        "contributor_status_history",
        "master_commit_index",
        "features",
        "bq_4_month_level_aggregation",
        "bq_5_user_level_aggregation",
    ]
    with db() as conn:
        for t in tables:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        repo_count = conn.execute(
            "SELECT COUNT(DISTINCT repo) FROM pr_analysis"
        ).fetchone()[0]

    return {"repo_count": repo_count, "row_counts": counts}
