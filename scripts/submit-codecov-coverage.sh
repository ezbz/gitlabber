#!/bin/bash
# Submit code coverage to Codecov
#
# This script automatically detects:
# - Latest commit SHA from git
# - Latest PR number from GitHub API (if running in PR context)
# - Current branch name
#
# Environment variables:
#   CODECOV_TOKEN: Codecov upload token (required)
#   GITHUB_TOKEN: GitHub token for API access (optional, for PR detection)
#   GITHUB_REPOSITORY: Repository in format owner/repo (optional, defaults to git remote)
#   COVERAGE_FILE: Coverage file path (defaults to coverage.xml)

set -euo pipefail

# Default values
COVERAGE_FILE="${COVERAGE_FILE:-coverage.xml}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"

# Check required environment variable
if [ -z "${CODECOV_TOKEN:-}" ]; then
    echo "Error: CODECOV_TOKEN environment variable is required" >&2
    exit 1
fi

# Check if coverage file exists
if [ ! -f "$COVERAGE_FILE" ]; then
    echo "Error: Coverage file '$COVERAGE_FILE' not found" >&2
    exit 1
fi

# Get latest commit SHA
COMMIT_SHA=$(git rev-parse HEAD)
if [ -z "$COMMIT_SHA" ]; then
    echo "Error: Could not determine commit SHA" >&2
    exit 1
fi

# Get current branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ -z "$BRANCH" ]; then
    echo "Error: Could not determine branch name" >&2
    exit 1
fi

# Get repository name (owner/repo)
if [ -z "$GITHUB_REPOSITORY" ]; then
    # Try to get from git remote
    GITHUB_REPOSITORY=$(git remote get-url origin 2>/dev/null | sed -E 's|.*github.com[:/]([^/]+/[^/]+)(\.git)?$|\1|' || echo "")
    if [ -z "$GITHUB_REPOSITORY" ]; then
        echo "Warning: Could not determine repository name. Set GITHUB_REPOSITORY environment variable." >&2
    fi
fi

# Try to get PR number from GitHub API if GITHUB_TOKEN is available
PR_NUMBER=""
if [ -n "${GITHUB_TOKEN:-}" ] && [ -n "$GITHUB_REPOSITORY" ]; then
    # Get PR number from GitHub API (latest PR for this branch)
    PR_NUMBER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$GITHUB_REPOSITORY/pulls?head=${GITHUB_REPOSITORY%%/*}:$BRANCH&state=open" \
        | jq -r '.[0].number // empty' 2>/dev/null || echo "")
    
    # If no open PR found, try closed PRs
    if [ -z "$PR_NUMBER" ]; then
        PR_NUMBER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "https://api.github.com/repos/$GITHUB_REPOSITORY/pulls?head=${GITHUB_REPOSITORY%%/*}:$BRANCH&state=all" \
            | jq -r '.[0].number // empty' 2>/dev/null || echo "")
    fi
fi

# Build codecov command
CODECOV_CMD="codecovcli upload-coverage"
CODECOV_CMD="$CODECOV_CMD -t $CODECOV_TOKEN"
CODECOV_CMD="$CODECOV_CMD --file $COVERAGE_FILE"
CODECOV_CMD="$CODECOV_CMD --branch $BRANCH"
CODECOV_CMD="$CODECOV_CMD --sha $COMMIT_SHA"
CODECOV_CMD="$CODECOV_CMD --report-type coverage"

# Add PR number if available
if [ -n "$PR_NUMBER" ]; then
    CODECOV_CMD="$CODECOV_CMD --pr $PR_NUMBER"
    echo "Detected PR #$PR_NUMBER for branch $BRANCH"
fi

# Add repository if available
if [ -n "$GITHUB_REPOSITORY" ]; then
    CODECOV_CMD="$CODECOV_CMD -r $GITHUB_REPOSITORY"
fi

# Display information
echo "Submitting coverage to Codecov:"
echo "  Repository: ${GITHUB_REPOSITORY:-<unknown>}"
echo "  Branch: $BRANCH"
echo "  Commit: $COMMIT_SHA"
echo "  PR: ${PR_NUMBER:-<none>}"
echo "  Coverage file: $COVERAGE_FILE"
echo ""

# Execute codecov command
eval "$CODECOV_CMD"

