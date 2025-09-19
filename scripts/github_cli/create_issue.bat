@echo off
REM Helper script for creating issues with GitHub CLI
REM Usage: create_issue.bat "Title" "Body" "labels"

set TITLE=%1
set BODY=%2
set LABELS=%3

if "%TITLE%"=="" (
    echo Usage: %0 "Issue Title" "Issue Body" "label1,label2"
    exit /b 1
)

REM Create issue using GitHub CLI
gh issue create --title %TITLE% --body %BODY% --label %LABELS% --assignee "@me"

echo Issue created successfully
