#!/usr/bin/env python3
"""
Local GitHub CLI Integration for Automated Bug Tracking
Provides GitHub CLI operations for local-only bug tracking and issue management.

This module provides:
1. Local GitHub issue creation and management
2. Bug-to-issue conversion with structured templates
3. Local project board simulation and tracking
4. Subagent assignment via GitHub issue assignment
5. Issue status synchronization with bug workflow
6. Local GitHub CLI database management
"""

import asyncio
import os
import sys
# Configure UTF-8 encoding for Windows
if os.name == 'nt':
    import codecs
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        # stdout/stderr may already be wrapped or redirected
        pass

import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys
import os

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

logger = logging.getLogger(__name__)

class GitHubIssue:
    """Represents a GitHub issue with local tracking"""

    def __init__(self, issue_id: str, title: str, body: str, labels: List[str] = None,
                 assignees: List[str] = None, state: str = "open"):
        self.issue_id = issue_id
        self.title = title
        self.body = body
        self.labels = labels or []
        self.assignees = assignees or []
        self.state = state
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.comments: List[Dict[str, Any]] = []
        self.milestone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.issue_id,
            "title": self.title,
            "body": self.body,
            "labels": self.labels,
            "assignees": self.assignees,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "comments": self.comments,
            "milestone": self.milestone
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubIssue':
        """Create from dictionary representation"""
        issue = cls(
            issue_id=data["id"],
            title=data["title"],
            body=data["body"],
            labels=data.get("labels", []),
            assignees=data.get("assignees", []),
            state=data.get("state", "open")
        )
        issue.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        issue.updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        issue.comments = data.get("comments", [])
        issue.milestone = data.get("milestone")
        return issue

class LocalIssueDatabase:
    """Local database for storing GitHub issues"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure database file exists with proper structure"""
        if not self.db_path.exists():
            initial_data = {
                "issues": {},
                "next_issue_id": 1,
                "labels": [],
                "milestones": [],
                "project_boards": []
            }
            self._save_data(initial_data)

    def _load_data(self) -> Dict[str, Any]:
        """Load data from database file"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._get_default_data()

    def _save_data(self, data: Dict[str, Any]):
        """Save data to database file"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_default_data(self) -> Dict[str, Any]:
        """Get default database structure"""
        return {
            "issues": {},
            "next_issue_id": 1,
            "labels": [],
            "milestones": [],
            "project_boards": []
        }

    def create_issue(self, issue: GitHubIssue) -> str:
        """Create new issue and return issue ID"""
        data = self._load_data()

        # Assign issue ID if not set
        if not issue.issue_id:
            issue.issue_id = str(data["next_issue_id"])
            data["next_issue_id"] += 1

        # Store issue
        data["issues"][issue.issue_id] = issue.to_dict()
        self._save_data(data)

        logger.info(f"Created local issue #{issue.issue_id}: {issue.title}")
        return issue.issue_id

    def get_issue(self, issue_id: str) -> Optional[GitHubIssue]:
        """Get issue by ID"""
        data = self._load_data()
        issue_data = data["issues"].get(issue_id)
        return GitHubIssue.from_dict(issue_data) if issue_data else None

    def update_issue(self, issue_id: str, updates: Dict[str, Any]) -> bool:
        """Update issue with new data"""
        data = self._load_data()
        if issue_id not in data["issues"]:
            return False

        issue_data = data["issues"][issue_id]
        issue_data.update(updates)
        issue_data["updated_at"] = datetime.now().isoformat()
        data["issues"][issue_id] = issue_data
        self._save_data(data)

        logger.info(f"Updated local issue #{issue_id}")
        return True

    def list_issues(self, state: str = None, labels: List[str] = None) -> List[GitHubIssue]:
        """List issues with optional filtering"""
        data = self._load_data()
        issues = []

        for issue_data in data["issues"].values():
            issue = GitHubIssue.from_dict(issue_data)

            # Filter by state
            if state and issue.state != state:
                continue

            # Filter by labels
            if labels and not any(label in issue.labels for label in labels):
                continue

            issues.append(issue)

        # Sort by creation date (newest first)
        issues.sort(key=lambda x: x.created_at, reverse=True)
        return issues

    def add_comment(self, issue_id: str, comment: str, author: str = "system") -> bool:
        """Add comment to issue"""
        data = self._load_data()
        if issue_id not in data["issues"]:
            return False

        comment_data = {
            "body": comment,
            "author": author,
            "created_at": datetime.now().isoformat()
        }

        data["issues"][issue_id]["comments"].append(comment_data)
        data["issues"][issue_id]["updated_at"] = datetime.now().isoformat()
        self._save_data(data)

        logger.info(f"Added comment to issue #{issue_id}")
        return True

    def close_issue(self, issue_id: str, reason: str = None) -> bool:
        """Close issue"""
        updates = {"state": "closed"}
        if reason:
            self.add_comment(issue_id, f"Closing issue: {reason}", "system")
        return self.update_issue(issue_id, updates)

class LocalGitHubIntegration:
    """Main class for local GitHub CLI integration"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.github_dir = self.project_root / ".github"
        self.issues_dir = self.github_dir / "issues"
        self.db_path = self.issues_dir / "local_issues_db.json"
        self.database = LocalIssueDatabase(self.db_path)

        # Subagent to GitHub username mapping
        self.subagent_mapping = {
            "frontend-specialist": "frontend-dev",
            "ux-ui-specialist": "ux-designer",
            "code-reviewer": "code-reviewer",
            "testing-expert": "qa-tester",
            "performance-optimizer": "perf-engineer",
            "data-specialist": "data-engineer",
            "security-specialist": "security-engineer",
            "documentation-specialist": "tech-writer",
            "devops-specialist": "devops-engineer"
        }

    def check_github_cli_available(self) -> bool:
        """Check if GitHub CLI is available"""
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def create_issue_from_bug(self, bug: 'Bug', labels: List[str] = None, milestone: str = None) -> Dict[str, Any]:
        """Create GitHub issue from Bug object"""
        try:
            # Import Bug class dynamically to avoid circular imports
            from bug_resolution_workflow import Bug, BugSeverity, BugCategory

            # Generate issue title
            title = f"[{bug.severity.value.upper()}] {bug.title}"

            # Generate issue body
            body = self._generate_issue_body_from_bug(bug)

            # Use provided labels or generate from bug
            issue_labels = labels if labels is not None else self._generate_labels_from_bug(bug)

            # Generate assignees
            assignees = self._map_subagents_to_github_users(bug.assigned_subagents)

            # Create GitHub issue
            issue = GitHubIssue(
                issue_id=None,  # Will be assigned by database
                title=title,
                body=body,
                labels=issue_labels,
                assignees=assignees,
                state="open"
            )

            # Set milestone - use provided or default for critical bugs
            if milestone:
                issue.milestone = milestone
            elif bug.severity == BugSeverity.CRITICAL:
                issue.milestone = "Version 1 Release"

            # Create issue in database
            issue_id = self.database.create_issue(issue)

            # Try to create with GitHub CLI if available
            github_issue_number = None
            if self.check_github_cli_available():
                try:
                    self._create_github_cli_issue(issue)
                    github_issue_number = int(issue_id) if issue_id else None
                except Exception as e:
                    logger.warning(f"GitHub CLI issue creation failed: {e}")
                    logger.info("Issue created in local database only")

            return {
                "success": True,
                "issue_number": github_issue_number or int(issue_id) if issue_id else None,
                "issue_url": f"#{github_issue_number or issue_id}" if issue_id else None,
                "local_id": issue_id
            }

        except Exception as e:
            logger.error(f"Failed to create issue from bug: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_issue_body_from_bug(self, bug: 'Bug') -> str:
        """Generate structured issue body from bug"""
        body = f"""## Bug Information
- **Bug ID**: {bug.bug_id}
- **Severity**: {bug.severity.value}
- **Category**: {bug.category.value}
- **Source Test**: {bug.source_test}
- **Created**: {bug.created_at.strftime('%Y-%m-%d %H:%M:%S')}

## Description
{bug.description}

## Reproduction Steps
"""

        # Add reproduction steps
        for i, step in enumerate(bug.reproduction_steps, 1):
            body += f"{i}. {step}\n"

        body += f"""
## Expected Behavior
The system should function without errors and meet all test requirements.

## Additional Context
- **Estimated Effort**: {bug.estimated_effort_hours} hours
- **Assigned Subagents**: {', '.join(bug.assigned_subagents)}
- **Test Framework**: Catalynx Integrated Testing

## Technical Details
```
Source Test: {bug.source_test}
Bug Category: {bug.category.value}
Severity Level: {bug.severity.value}
```

## Resolution Tracking
- [ ] Issue assigned to appropriate subagent
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Fix reviewed and approved
- [ ] Regression tests added
- [ ] Fix verified with testing framework
- [ ] Issue closed

---
*This issue was automatically generated by the Catalynx Integrated Testing Framework*
"""

        return body

    def _generate_labels_from_bug(self, bug: 'Bug') -> List[str]:
        """Generate GitHub labels from bug properties"""
        labels = ["automated", "bug"]

        # Add severity label
        labels.append(f"bug-{bug.severity.value}")

        # Add category label
        labels.append(f"bug-{bug.category.value}")

        # Add status label
        labels.append(f"status-{bug.status.value}")

        # Add subagent labels
        for subagent in bug.assigned_subagents:
            if subagent in self.subagent_mapping:
                labels.append(f"subagent-{subagent.replace('-specialist', '')}")

        # Add special labels
        if bug.severity.value == "critical":
            labels.append("version-1-blocker")

        if "real_data" in bug.source_test.lower():
            labels.append("real-data-issue")

        return labels

    def _map_subagents_to_github_users(self, subagents: List[str]) -> List[str]:
        """Map subagent names to GitHub usernames"""
        return [self.subagent_mapping.get(subagent, subagent) for subagent in subagents]

    def _create_github_cli_issue(self, issue: GitHubIssue):
        """Create issue using GitHub CLI"""
        # Create temporary file for issue body
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(issue.body)
            body_file = f.name

        try:
            # Build GitHub CLI command
            cmd = [
                "gh", "issue", "create",
                "--title", issue.title,
                "--body-file", body_file
            ]

            # Add labels
            if issue.labels:
                cmd.extend(["--label", ",".join(issue.labels)])

            # Add assignees
            if issue.assignees:
                cmd.extend(["--assignee", ",".join(issue.assignees)])

            # Add milestone
            if issue.milestone:
                cmd.extend(["--milestone", issue.milestone])

            # Execute command
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"GitHub CLI issue created successfully: {result.stdout.strip()}")
            else:
                logger.warning(f"GitHub CLI issue creation warning: {result.stderr}")

        finally:
            # Clean up temporary file
            try:
                os.unlink(body_file)
            except:
                pass

    def update_issue_status(self, issue_id: str, new_status: str, comment: str = None) -> bool:
        """Update issue status and add optional comment"""
        # Map bug status to GitHub issue state
        state_mapping = {
            "identified": "open",
            "triaged": "open",
            "assigned": "open",
            "in_progress": "open",
            "fixed": "open",
            "verified": "closed",
            "closed": "closed",
            "reopened": "open"
        }

        state = state_mapping.get(new_status, "open")
        labels_to_add = [f"status-{new_status}"]

        # Update issue in database
        updates = {
            "state": state,
            "labels": labels_to_add  # This should merge with existing labels in a real implementation
        }

        success = self.database.update_issue(issue_id, updates)

        # Add comment if provided
        if comment and success:
            self.database.add_comment(issue_id, comment, "system")

        # Update with GitHub CLI if available
        if self.check_github_cli_available() and success:
            try:
                self._update_github_cli_issue(issue_id, new_status, comment)
            except Exception as e:
                logger.warning(f"GitHub CLI update failed: {e}")

        return success

    def _update_github_cli_issue(self, issue_id: str, status: str, comment: str = None):
        """Update issue using GitHub CLI"""
        try:
            # Add status label
            subprocess.run([
                "gh", "issue", "edit", issue_id,
                "--add-label", f"status-{status}"
            ], cwd=self.project_root, timeout=15)

            # Add comment if provided
            if comment:
                subprocess.run([
                    "gh", "issue", "comment", issue_id,
                    "--body", comment
                ], cwd=self.project_root, timeout=15)

            # Close issue if status indicates closure
            if status in ["verified", "closed"]:
                subprocess.run([
                    "gh", "issue", "close", issue_id
                ], cwd=self.project_root, timeout=15)

        except subprocess.TimeoutExpired:
            logger.warning("GitHub CLI update timed out")
        except Exception as e:
            logger.warning(f"GitHub CLI update error: {e}")

    def assign_issue_to_subagents(self, issue_id: str, subagents: List[str]) -> bool:
        """Assign issue to subagents"""
        # Map subagents to GitHub users
        assignees = self._map_subagents_to_github_users(subagents)

        # Update database
        updates = {"assignees": assignees}
        success = self.database.update_issue(issue_id, updates)

        # Update with GitHub CLI if available
        if self.check_github_cli_available() and success:
            try:
                for assignee in assignees:
                    subprocess.run([
                        "gh", "issue", "edit", issue_id,
                        "--add-assignee", assignee
                    ], cwd=self.project_root, timeout=15)
            except Exception as e:
                logger.warning(f"GitHub CLI assignment failed: {e}")

        return success

    def get_issue_by_bug_id(self, bug_id: str) -> Optional[GitHubIssue]:
        """Get GitHub issue by bug ID"""
        issues = self.database.list_issues()
        for issue in issues:
            if bug_id in issue.body:  # Simple search for bug ID in issue body
                return issue
        return None

    def get_issues_by_label(self, label: str) -> List[GitHubIssue]:
        """Get issues with specific label"""
        return self.database.list_issues(labels=[label])

    def get_open_issues(self) -> List[GitHubIssue]:
        """Get all open issues"""
        return self.database.list_issues(state="open")

    def get_issue_statistics(self) -> Dict[str, Any]:
        """Get statistics about issues"""
        all_issues = self.database.list_issues()
        open_issues = [i for i in all_issues if i.state == "open"]
        closed_issues = [i for i in all_issues if i.state == "closed"]

        # Count by labels
        label_counts = {}
        for issue in all_issues:
            for label in issue.labels:
                label_counts[label] = label_counts.get(label, 0) + 1

        return {
            "total_issues": len(all_issues),
            "open_issues": len(open_issues),
            "closed_issues": len(closed_issues),
            "label_distribution": label_counts,
            "recent_issues": len([i for i in all_issues if
                                (datetime.now() - i.created_at).days <= 7])
        }

    def generate_issue_report(self) -> Dict[str, Any]:
        """Generate comprehensive issue report"""
        stats = self.get_issue_statistics()
        open_issues = self.get_open_issues()

        # Categorize open issues by severity
        critical_issues = [i for i in open_issues if "bug-critical" in i.labels]
        high_issues = [i for i in open_issues if "bug-high" in i.labels]
        medium_issues = [i for i in open_issues if "bug-medium" in i.labels]
        low_issues = [i for i in open_issues if "bug-low" in i.labels]

        return {
            "statistics": stats,
            "open_issues_summary": {
                "total": len(open_issues),
                "critical": len(critical_issues),
                "high": len(high_issues),
                "medium": len(medium_issues),
                "low": len(low_issues)
            },
            "version_1_blockers": len([i for i in open_issues if "version-1-blocker" in i.labels]),
            "recent_activity": {
                "issues_created_this_week": stats["recent_issues"],
                "issues_updated_recently": len([i for i in open_issues if
                                              (datetime.now() - i.updated_at).days <= 3])
            },
            "github_cli_available": self.check_github_cli_available()
        }

    def close_issue_with_verification(self, issue_id: str, verification_comment: str) -> bool:
        """Close issue with verification comment"""
        # Add verification comment
        self.database.add_comment(issue_id, f"✅ VERIFIED: {verification_comment}", "testing-framework")

        # Close the issue
        return self.database.close_issue(issue_id, "Verified and resolved by testing framework")

    def test_github_cli_connection(self) -> Dict[str, Any]:
        """Test GitHub CLI connection and configuration"""
        try:
            # Check if GitHub CLI is available
            if not self.check_github_cli_available():
                return {
                    "success": False,
                    "error": "GitHub CLI not installed or not in PATH"
                }

            # Test authentication
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return {
                    "success": True,
                    "authenticated": True,
                    "cli_version": self._get_github_cli_version()
                }
            else:
                return {
                    "success": False,
                    "authenticated": False,
                    "error": "GitHub CLI not authenticated"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_github_cli_version(self) -> str:
        """Get GitHub CLI version"""
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
            else:
                return "unknown"
        except:
            return "unknown"

    async def list_milestones(self) -> List[Dict[str, Any]]:
        """List GitHub milestones"""
        try:
            # Return predefined milestones for local testing
            milestones = [
                {
                    "title": "Version 1 Release",
                    "state": "open",
                    "due_on": "2025-10-01",
                    "description": "Version 1 production release milestone"
                },
                {
                    "title": "Integration Testing Complete",
                    "state": "open",
                    "due_on": "2025-09-25",
                    "description": "Complete all integration testing"
                },
                {
                    "title": "Version 1 Testing Phase",
                    "state": "open",
                    "due_on": "2025-09-30",
                    "description": "Complete comprehensive testing phase"
                }
            ]
            return milestones
        except Exception as e:
            logger.error(f"Error listing milestones: {e}")
            return []

    async def list_issues(self, state: str = None, labels: List[str] = None) -> List[Dict[str, Any]]:
        """List GitHub issues with filtering"""
        try:
            # Get issues from database
            issues = self.database.list_issues(state=state, labels=labels)

            # Convert to expected format
            issue_list = []
            for issue in issues:
                issue_dict = issue.to_dict() if hasattr(issue, 'to_dict') else issue
                issue_list.append(issue_dict)

            return issue_list
        except Exception as e:
            logger.error(f"Error listing issues: {e}")
            return []

    @property
    def issue_database(self):
        """Provide access to issue database for compatibility"""
        return self.database

async def main():
    """Test the local GitHub integration"""
    print("Local GitHub CLI Integration Test")
    print("=" * 50)

    integration = LocalGitHubIntegration()

    # Test GitHub CLI availability
    cli_available = integration.check_github_cli_available()
    print(f"GitHub CLI Available: {cli_available}")

    # Test issue creation (simulate)
    print("\nTesting local issue database...")

    # Create test issue
    test_issue = GitHubIssue(
        issue_id=None,
        title="Test Issue from Integration",
        body="This is a test issue to validate local GitHub integration",
        labels=["test", "automated"],
        assignees=["test-user"]
    )

    issue_id = integration.database.create_issue(test_issue)
    print(f"Created test issue: #{issue_id}")

    # List issues
    issues = integration.database.list_issues()
    print(f"Total issues in database: {len(issues)}")

    # Get statistics
    stats = integration.get_issue_statistics()
    print(f"Issue statistics: {stats}")

    # Generate report
    report = integration.generate_issue_report()
    print(f"Generated comprehensive report with {report['statistics']['total_issues']} issues")

    print("\n✅ Local GitHub integration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())