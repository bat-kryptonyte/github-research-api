from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import repos, contributors, features, commits
from database import db

app = FastAPI(
    title="GitHub Research API",
    description="REST API over the github_research_v1 dataset — PRs, contributors, lifecycle, and ML features across 200 open-source repos.",
    version="1.0.0",
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


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/stats", tags=["meta"])
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
