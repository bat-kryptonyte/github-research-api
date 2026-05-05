# GitHub Research API

REST API over the `github_research_v1` dataset — pull requests, contributor lifecycle, events, status history, commits, and ML features across 200 open-source repos.

## Setup

```bash
pip install -r requirements.txt
```

Set `DB_PATH` to point at your `github_research_v1.db` (defaults to `../badvibes/github_research_v1.db`):

```bash
DB_PATH=/path/to/github_research_v1.db uvicorn main:app --reload
```

Interactive docs at `http://localhost:8000/docs`.

## Endpoints

### Meta
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | Row counts for all major tables |

### Repos
| Method | Path | Description |
|--------|------|-------------|
| GET | `/repos` | List all repos with PR summary stats |
| GET | `/repos/{repo}/prs` | PRs for a repo (filter: `author`, `merged`) |
| GET | `/repos/{repo}/prs/{pr_number}` | Single PR |
| GET | `/repos/{repo}/contributors` | Contributors (filter: `is_core`, `is_newcomer`) |
| GET | `/repos/{repo}/monthly-activity` | Monthly activity stats (filter: `user_login`) |
| GET | `/repos/{repo}/status-history` | Contributor status history (filter: `user_login`, `status`) |

### Contributors
| Method | Path | Description |
|--------|------|-------------|
| GET | `/contributors` | List contributors (filter: `repo`, `is_core`, `is_newcomer`) |
| GET | `/contributors/{username}` | Contributor summary across repos |
| GET | `/contributors/{username}/events` | Events (filter: `repo`, `event_type`) |
| GET | `/contributors/{username}/status-history` | Status history (filter: `repo`, `status`) |
| GET | `/contributors/{username}/monthly-activity` | Monthly activity (filter: `repo`) |

### Features (ML)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/features` | Raw ML features (filter: `repo`, `author`, `is_core`, `is_newcomer`) |
| GET | `/features/standardized` | Standardized ML features (same filters) |

### Commits
| Method | Path | Description |
|--------|------|-------------|
| GET | `/commits` | Commit index (filter: `repo`) |
| GET | `/commits/{sha}` | Single commit |

## Query Parameters

All list endpoints support pagination:
- `page` (default: 1)
- `per_page` (default varies; max 200–500 depending on endpoint)

Valid values for `status` filter: `active`, `at-risk`, `disengaged`, `returning`  
Valid values for `event_type` filter: `issues`, `prs`, `commits`

Repo names contain slashes (e.g. `huggingface/transformers`) — URL-encode them as `huggingface%2Ftransformers` in path segments.
