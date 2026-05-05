#!/bin/bash
set -e

DB_PATH="${DB_PATH:-/data/github_research_v1.db}"

# Download the database if it's missing and a source URL is configured
if [ ! -f "$DB_PATH" ]; then
    if [ -z "$DB_URL" ]; then
        echo "ERROR: database not found at $DB_PATH and DB_URL is not set."
        echo "Set DB_URL to a direct download link for github_research_v1.db,"
        echo "or mount the file at $DB_PATH via a persistent volume."
        exit 1
    fi
    echo "Downloading database from \$DB_URL …"
    mkdir -p "$(dirname "$DB_PATH")"
    curl -fSL "$DB_URL" -o "$DB_PATH"
    echo "Database ready at $DB_PATH ($(du -sh "$DB_PATH" | cut -f1))"
fi

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
