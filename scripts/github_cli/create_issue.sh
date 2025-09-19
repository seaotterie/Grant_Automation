#!/bin/bash
# Helper script for creating issues with GitHub CLI
# Usage: ./create_issue.sh "Title" "Body" "labels"

TITLE="$1"
BODY="$2"
LABELS="$3"

if [ -z "$TITLE" ]; then
    echo "Usage: $0 'Issue Title' 'Issue Body' 'label1,label2'"
    exit 1
fi

# Create issue using GitHub CLI
gh issue create \
    --title "$TITLE" \
    --body "$BODY" \
    --label "$LABELS" \
    --assignee "@me"

echo "Issue created successfully"
