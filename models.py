from pydantic import BaseModel, Field
from typing import Optional, List


class Page(BaseModel):
    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="Current page (1-indexed)")
    per_page: int = Field(..., description="Records returned per page")


# ── PR Analysis ───────────────────────────────────────────────────────────────

class PR(BaseModel):
    repo: str = Field(..., description="Repository slug (e.g. huggingface/transformers)")
    pr_number: int = Field(..., description="GitHub PR number")
    author: Optional[str] = Field(None, description="GitHub username of the PR author")
    merged_detected: Optional[bool] = Field(None, description="True if the PR was merged")
    method: Optional[str] = Field(None, description="Merge method (merge, squash, rebase, or closed)")
    num_comments: Optional[int] = Field(None, description="Total comment count on the PR")
    num_users: Optional[int] = Field(None, description="Number of unique users who commented")
    size_commits: Optional[int] = Field(None, description="Number of commits in the PR")
    size_sloc: Optional[int] = Field(None, description="Lines of code changed")
    size_files: Optional[int] = Field(None, description="Number of files changed")
    first_response_mins: Optional[float] = Field(None, description="Minutes from PR open to first response (any)")
    first_human_response_mins: Optional[float] = Field(None, description="Minutes from PR open to first human response")
    time_to_decision_mins: Optional[float] = Field(None, description="Minutes from PR open to merge or close")
    at_tag: Optional[bool] = Field(None, description="True if the PR body contains an @-mention")
    created_at: Optional[str] = Field(None, description="ISO-8601 creation timestamp")


class PRList(Page):
    prs: List[PR]


# ── Repos ─────────────────────────────────────────────────────────────────────

class RepoSummary(BaseModel):
    repo: str = Field(..., description="Repository slug")
    total_prs: int = Field(..., description="Total PRs observed for this repo")
    merged_prs: Optional[int] = Field(None, description="Number of merged PRs")
    avg_comments: Optional[float] = Field(None, description="Average comment count per PR")
    avg_time_to_decision_mins: Optional[float] = Field(None, description="Average minutes to merge or close")


class RepoList(Page):
    repos: List[RepoSummary]


# ── Contributors ──────────────────────────────────────────────────────────────

class ContributorLifecycle(BaseModel):
    repo: str = Field(..., description="Repository slug")
    user_login: str = Field(..., description="GitHub username")
    first_ever_activity: Optional[str] = Field(None, description="ISO-8601 date of first activity in this repo")
    is_newcomer: Optional[int] = Field(None, description="1 if classified as a newcomer (≤3 months tenure), else 0")
    tenure_days: Optional[int] = Field(None, description="Days since first-ever activity in the repo")
    total_event_count: Optional[int] = Field(None, description="Lifetime event count (commits + issues + PRs)")
    is_core: Optional[int] = Field(None, description="1 if classified as a core contributor, else 0")


class ContributorList(Page):
    contributors: List[ContributorLifecycle]


class ContributorDetail(BaseModel):
    username: str
    repos: List[ContributorLifecycle]


class ContributorEvent(BaseModel):
    repo: str = Field(..., description="Repository slug")
    event_type: str = Field(..., description="One of: issues, prs, commits")
    username: str = Field(..., description="GitHub username")
    timestamp: str = Field(..., description="ISO-8601 event timestamp")


class EventList(Page):
    events: List[ContributorEvent]


class StatusHistoryEntry(BaseModel):
    repo: str = Field(..., description="Repository slug")
    user_login: str = Field(..., description="GitHub username")
    month_year: str = Field(..., description="Month label (YYYY-MM)")
    current_status: str = Field(..., description="One of: active, at-risk, disengaged, returning")
    cumulative_contributions: Optional[int] = Field(None, description="Running total of contributions through this month")


class StatusHistoryList(Page):
    history: List[StatusHistoryEntry]


class MonthlyActivityEntry(BaseModel):
    repo: str = Field(..., description="Repository slug")
    user_login: str = Field(..., description="GitHub username")
    month_user_commits: Optional[int] = Field(None, description="Commits authored this month")
    month_user_issues: Optional[int] = Field(None, description="Issues opened this month")
    month_user_issue_comments: Optional[int] = Field(None, description="Issue comments made this month")
    month_user_issue_events: Optional[int] = Field(None, description="Issue events (labels, closes, etc.) this month")
    month_user_pull_requests: Optional[int] = Field(None, description="PRs opened this month")
    month_user_pull_requests_comments: Optional[int] = Field(None, description="PR review comments made this month")
    month_user_pull_request_history: Optional[int] = Field(None, description="PRs closed/merged (opened in prior months) this month")
    month_user_pull_request_history_merged: Optional[int] = Field(None, description="Subset of history PRs that were merged")
    month_user_pull_request_history_closed: Optional[int] = Field(None, description="Subset of history PRs that were closed without merge")


class MonthlyActivityList(Page):
    activity: List[MonthlyActivityEntry]


# ── Commits ───────────────────────────────────────────────────────────────────

class Commit(BaseModel):
    repo: str = Field(..., description="Repository slug")
    sha: str = Field(..., description="Full 40-character git SHA")
    committed_date: Optional[str] = Field(None, description="ISO-8601 commit timestamp")


class CommitList(Page):
    commits: List[Commit]


# ── ML Features ───────────────────────────────────────────────────────────────

class FeatureRow(BaseModel):
    repo: str = Field(..., description="Repository slug")
    author: str = Field(..., description="GitHub username")
    # PR-level log-averages
    log_avg_num_comments: Optional[float] = Field(None, description="log(1 + avg PR comment count)")
    log_avg_num_users: Optional[float] = Field(None, description="log(1 + avg unique commenters per PR)")
    log_avg_size_commits: Optional[float] = Field(None, description="log(1 + avg commits per PR)")
    log_avg_size_sloc: Optional[float] = Field(None, description="log(1 + avg lines changed per PR)")
    log_avg_size_files: Optional[float] = Field(None, description="log(1 + avg files changed per PR)")
    log_avg_first_response_mins: Optional[float] = Field(None, description="log(1 + avg first-response latency in minutes)")
    log_avg_first_human_response_mins: Optional[float] = Field(None, description="log(1 + avg first-human-response latency in minutes)")
    log_avg_time_to_decision_mins: Optional[float] = Field(None, description="log(1 + avg time-to-decision in minutes)")
    # Author-level signals
    mention_ratio_3: Optional[float] = Field(None, description="Fraction of PRs that contain an @-mention (trailing 3-month window)")
    contribution_success_rate_3: Optional[float] = Field(None, description="Fraction of PRs merged (trailing 3-month window)")
    global_repo_merge_rate: Optional[float] = Field(None, description="Repo-wide merge rate across all authors")
    repo_name: Optional[str] = Field(None, description="Redundant repo label used for joining")
    join_date: Optional[str] = Field(None, description="Author's first-ever activity date in this repo")
    log_user_owns_repos: Optional[float] = Field(None, description="log(1 + repos owned by user at join time)")
    log_user_watch_repos: Optional[float] = Field(None, description="log(1 + repos watched by user at join time)")
    log_user_contribute_repos: Optional[float] = Field(None, description="log(1 + repos contributed to at join time)")
    log_user_history_commits: Optional[float] = Field(None, description="log(1 + lifetime commits before join)")
    log_user_history_issues: Optional[float] = Field(None, description="log(1 + lifetime issues before join)")
    log_user_history_pull_requests: Optional[float] = Field(None, description="log(1 + lifetime PRs before join)")
    log_month_user_commits: Optional[float] = Field(None, description="log(1 + commits in the month of the PR)")
    log_month_user_issues: Optional[float] = Field(None, description="log(1 + issues opened in the month of the PR)")
    log_month_user_issue_comments: Optional[float] = Field(None, description="log(1 + issue comments in the month of the PR)")
    log_month_user_issue_events: Optional[float] = Field(None, description="log(1 + issue events in the month of the PR)")
    log_month_user_pull_requests: Optional[float] = Field(None, description="log(1 + PRs opened in the month of the PR)")
    log_month_user_pull_requests_comments: Optional[float] = Field(None, description="log(1 + PR review comments in the month of the PR)")
    log_month_user_pull_request_history: Optional[float] = Field(None, description="log(1 + historical PRs resolved in the month)")
    log_month_user_pull_request_history_merged: Optional[float] = Field(None, description="log(1 + historical PRs merged in the month)")
    log_month_user_pull_request_history_closed: Optional[float] = Field(None, description="log(1 + historical PRs closed without merge in the month)")
    # Contributor classification
    is_newcomer: Optional[int] = Field(None, description="1 if classified as a newcomer, else 0")
    tenure_days: Optional[float] = Field(None, description="Days since first activity (raw or z-scored in /standardized)")
    total_event_count: Optional[int] = Field(None, description="Lifetime event count")
    is_core: Optional[int] = Field(None, description="1 if classified as a core contributor, else 0")


class FeatureList(Page):
    features: List[FeatureRow]


# ── Meta ──────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="Always 'ok' when the service is healthy")


class StatsResponse(BaseModel):
    repo_count: int = Field(..., description="Number of distinct repositories in the dataset")
    row_counts: dict = Field(..., description="Row count per table")
