#!/usr/bin/env python3
"""
Local Project Management System with GitHub CLI Integration

Provides comprehensive project management capabilities using local GitHub CLI:
1. Milestone tracking and management
2. Issue board visualization and organization
3. Progress monitoring and reporting
4. Sprint planning and task coordination
5. Release management and version control
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import sys

# Import GitHub integration
try:
    from .local_github_integration import LocalGitHubIntegration
    GITHUB_INTEGRATION_AVAILABLE = True
except ImportError:
    try:
        from local_github_integration import LocalGitHubIntegration
        GITHUB_INTEGRATION_AVAILABLE = True
    except ImportError:
        GITHUB_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class ProjectPhase(Enum):
    """Project development phases"""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    RELEASE = "release"
    MAINTENANCE = "maintenance"

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ProjectMilestone:
    """Project milestone definition"""
    id: str
    title: str
    description: str
    due_date: datetime
    phase: ProjectPhase
    completion_percentage: float = 0.0
    issues_total: int = 0
    issues_closed: int = 0
    github_milestone_id: Optional[int] = None

@dataclass
class TaskProgress:
    """Individual task progress tracking"""
    task_id: str
    title: str
    assignee: str
    status: str
    priority: TaskPriority
    estimated_hours: int
    actual_hours: int = 0
    github_issue_number: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None

class LocalProjectManager:
    """Local project management system with GitHub CLI integration"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.project_data_dir = self.project_root / ".github" / "project"
        self.project_data_dir.mkdir(exist_ok=True)

        # Initialize GitHub integration
        self.github_integration = None
        if GITHUB_INTEGRATION_AVAILABLE:
            try:
                self.github_integration = LocalGitHubIntegration()
                logger.info("GitHub CLI integration initialized for project management")
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub integration: {e}")

        # Load project data
        self.milestones = self._load_milestones()
        self.task_progress = self._load_task_progress()

    def _load_milestones(self) -> Dict[str, ProjectMilestone]:
        """Load project milestones from local storage"""
        milestones_file = self.project_data_dir / "milestones.json"

        if milestones_file.exists():
            try:
                with open(milestones_file, 'r') as f:
                    data = json.load(f)
                    return {
                        mid: ProjectMilestone(
                            id=mid,
                            title=mdata["title"],
                            description=mdata["description"],
                            due_date=datetime.fromisoformat(mdata["due_date"]),
                            phase=ProjectPhase(mdata["phase"]),
                            completion_percentage=mdata.get("completion_percentage", 0.0),
                            issues_total=mdata.get("issues_total", 0),
                            issues_closed=mdata.get("issues_closed", 0),
                            github_milestone_id=mdata.get("github_milestone_id")
                        )
                        for mid, mdata in data.items()
                    }
            except Exception as e:
                logger.error(f"Error loading milestones: {e}")

        # Return default milestones for Catalynx Version 1
        return self._create_default_milestones()

    def _create_default_milestones(self) -> Dict[str, ProjectMilestone]:
        """Create default milestones for Catalynx Version 1"""
        milestones = {
            "version-1-testing": ProjectMilestone(
                id="version-1-testing",
                title="Version 1 Testing Phase",
                description="Complete testing framework implementation and bug resolution",
                due_date=datetime.now() + timedelta(days=7),
                phase=ProjectPhase.TESTING
            ),
            "version-1-release": ProjectMilestone(
                id="version-1-release",
                title="Version 1 Production Release",
                description="Deploy production-ready Version 1 with all features tested",
                due_date=datetime.now() + timedelta(days=14),
                phase=ProjectPhase.RELEASE
            ),
            "integration-complete": ProjectMilestone(
                id="integration-complete",
                title="Integration Testing Complete",
                description="All integrated testing frameworks operational with real data",
                due_date=datetime.now() + timedelta(days=3),
                phase=ProjectPhase.TESTING
            )
        }

        self._save_milestones(milestones)
        return milestones

    def _load_task_progress(self) -> Dict[str, TaskProgress]:
        """Load task progress from local storage"""
        progress_file = self.project_data_dir / "task_progress.json"

        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    return {
                        tid: TaskProgress(
                            task_id=tid,
                            title=tdata["title"],
                            assignee=tdata["assignee"],
                            status=tdata["status"],
                            priority=TaskPriority(tdata["priority"]),
                            estimated_hours=tdata["estimated_hours"],
                            actual_hours=tdata.get("actual_hours", 0),
                            github_issue_number=tdata.get("github_issue_number"),
                            created_at=datetime.fromisoformat(tdata["created_at"]) if tdata.get("created_at") else None,
                            updated_at=datetime.fromisoformat(tdata["updated_at"]) if tdata.get("updated_at") else None
                        )
                        for tid, tdata in data.items()
                    }
            except Exception as e:
                logger.error(f"Error loading task progress: {e}")

        return {}

    def _save_milestones(self, milestones: Dict[str, ProjectMilestone]):
        """Save milestones to local storage"""
        milestones_file = self.project_data_dir / "milestones.json"

        try:
            data = {
                mid: {
                    "title": milestone.title,
                    "description": milestone.description,
                    "due_date": milestone.due_date.isoformat(),
                    "phase": milestone.phase.value,
                    "completion_percentage": milestone.completion_percentage,
                    "issues_total": milestone.issues_total,
                    "issues_closed": milestone.issues_closed,
                    "github_milestone_id": milestone.github_milestone_id
                }
                for mid, milestone in milestones.items()
            }

            with open(milestones_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving milestones: {e}")

    def _save_task_progress(self, progress: Dict[str, TaskProgress]):
        """Save task progress to local storage"""
        progress_file = self.project_data_dir / "task_progress.json"

        try:
            data = {
                tid: {
                    "title": task.title,
                    "assignee": task.assignee,
                    "status": task.status,
                    "priority": task.priority.value,
                    "estimated_hours": task.estimated_hours,
                    "actual_hours": task.actual_hours,
                    "github_issue_number": task.github_issue_number,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
                for tid, task in progress.items()
            }

            with open(progress_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving task progress: {e}")

    async def sync_with_github(self):
        """Synchronize local project data with GitHub CLI"""
        if not self.github_integration:
            logger.warning("GitHub integration not available for sync")
            return

        try:
            logger.info("Synchronizing project data with GitHub...")

            # Sync milestones
            await self._sync_milestones_with_github()

            # Sync task progress from GitHub issues
            await self._sync_task_progress_with_github()

            logger.info("✅ Project data synchronized with GitHub")

        except Exception as e:
            logger.error(f"Error synchronizing with GitHub: {e}")

    async def _sync_milestones_with_github(self):
        """Sync milestones with GitHub milestones"""
        try:
            # Get existing GitHub milestones
            github_milestones = await self.github_integration.list_milestones()

            # Create missing milestones in GitHub
            for milestone in self.milestones.values():
                if not milestone.github_milestone_id:
                    # Create milestone in GitHub
                    result = await self.github_integration.create_milestone(
                        title=milestone.title,
                        description=milestone.description,
                        due_date=milestone.due_date
                    )

                    if result.get("success"):
                        milestone.github_milestone_id = result.get("milestone_id")
                        logger.info(f"Created GitHub milestone: {milestone.title}")

            # Update local milestone data with GitHub info
            for gh_milestone in github_milestones:
                milestone_title = gh_milestone.get("title")
                for milestone in self.milestones.values():
                    if milestone.title == milestone_title:
                        milestone.issues_total = gh_milestone.get("open_issues", 0) + gh_milestone.get("closed_issues", 0)
                        milestone.issues_closed = gh_milestone.get("closed_issues", 0)
                        if milestone.issues_total > 0:
                            milestone.completion_percentage = (milestone.issues_closed / milestone.issues_total) * 100

            self._save_milestones(self.milestones)

        except Exception as e:
            logger.error(f"Error syncing milestones: {e}")

    async def _sync_task_progress_with_github(self):
        """Sync task progress with GitHub issues"""
        try:
            # Get GitHub issues
            github_issues = await self.github_integration.list_issues()

            # Update task progress from GitHub issues
            for issue in github_issues:
                issue_number = issue.get("number")
                issue_title = issue.get("title")
                issue_state = issue.get("state")  # open/closed
                issue_assignees = issue.get("assignees", [])

                # Find or create task progress entry
                task_id = f"github-{issue_number}"
                if task_id not in self.task_progress:
                    self.task_progress[task_id] = TaskProgress(
                        task_id=task_id,
                        title=issue_title,
                        assignee=issue_assignees[0] if issue_assignees else "unassigned",
                        status=issue_state,
                        priority=TaskPriority.MEDIUM,  # Default priority
                        estimated_hours=4,  # Default estimate
                        github_issue_number=issue_number,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                else:
                    # Update existing task
                    task = self.task_progress[task_id]
                    task.status = issue_state
                    task.assignee = issue_assignees[0] if issue_assignees else task.assignee
                    task.updated_at = datetime.now()

            self._save_task_progress(self.task_progress)

        except Exception as e:
            logger.error(f"Error syncing task progress: {e}")

    def generate_project_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive project dashboard"""
        dashboard = {
            "project_overview": {
                "name": "Catalynx Version 1 Release",
                "phase": self._get_current_project_phase(),
                "overall_progress": self._calculate_overall_progress(),
                "days_to_release": self._calculate_days_to_release(),
                "last_updated": datetime.now().isoformat()
            },
            "milestones": self._generate_milestone_summary(),
            "task_progress": self._generate_task_summary(),
            "team_workload": self._generate_team_workload(),
            "risk_assessment": self._generate_risk_assessment(),
            "next_actions": self._generate_next_actions()
        }

        return dashboard

    def _get_current_project_phase(self) -> str:
        """Determine current project phase based on milestone progress"""
        # Check which phase has the most active milestones
        phase_counts = {}
        for milestone in self.milestones.values():
            if milestone.completion_percentage < 100:
                phase = milestone.phase.value
                phase_counts[phase] = phase_counts.get(phase, 0) + 1

        if not phase_counts:
            return ProjectPhase.MAINTENANCE.value

        return max(phase_counts, key=phase_counts.get)

    def _calculate_overall_progress(self) -> float:
        """Calculate overall project progress percentage"""
        if not self.milestones:
            return 0.0

        total_progress = sum(m.completion_percentage for m in self.milestones.values())
        return total_progress / len(self.milestones)

    def _calculate_days_to_release(self) -> int:
        """Calculate days until Version 1 release"""
        release_milestone = self.milestones.get("version-1-release")
        if release_milestone:
            delta = release_milestone.due_date - datetime.now()
            return max(0, delta.days)
        return 0

    def _generate_milestone_summary(self) -> List[Dict[str, Any]]:
        """Generate milestone summary for dashboard"""
        return [
            {
                "id": milestone.id,
                "title": milestone.title,
                "phase": milestone.phase.value,
                "completion_percentage": milestone.completion_percentage,
                "due_date": milestone.due_date.isoformat(),
                "days_remaining": max(0, (milestone.due_date - datetime.now()).days),
                "issues_progress": f"{milestone.issues_closed}/{milestone.issues_total}",
                "status": "on_track" if milestone.completion_percentage >= 50 else "at_risk"
            }
            for milestone in sorted(self.milestones.values(), key=lambda m: m.due_date)
        ]

    def _generate_task_summary(self) -> Dict[str, Any]:
        """Generate task summary for dashboard"""
        total_tasks = len(self.task_progress)
        completed_tasks = sum(1 for task in self.task_progress.values() if task.status == "closed")
        in_progress_tasks = sum(1 for task in self.task_progress.values() if task.status == "open")

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "estimated_hours_remaining": sum(
                task.estimated_hours - task.actual_hours
                for task in self.task_progress.values()
                if task.status == "open" and task.estimated_hours > task.actual_hours
            )
        }

    def _generate_team_workload(self) -> Dict[str, Any]:
        """Generate team workload analysis"""
        workload = {}
        for task in self.task_progress.values():
            if task.status == "open":
                assignee = task.assignee
                if assignee not in workload:
                    workload[assignee] = {
                        "tasks_assigned": 0,
                        "estimated_hours": 0,
                        "high_priority_tasks": 0
                    }

                workload[assignee]["tasks_assigned"] += 1
                workload[assignee]["estimated_hours"] += task.estimated_hours - task.actual_hours
                if task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
                    workload[assignee]["high_priority_tasks"] += 1

        return workload

    def _generate_risk_assessment(self) -> Dict[str, Any]:
        """Generate project risk assessment"""
        risks = []

        # Check for overdue milestones
        overdue_milestones = [
            m for m in self.milestones.values()
            if m.due_date < datetime.now() and m.completion_percentage < 100
        ]

        if overdue_milestones:
            risks.append({
                "type": "schedule",
                "level": "high",
                "description": f"{len(overdue_milestones)} milestone(s) overdue",
                "impact": "Release schedule at risk"
            })

        # Check for high-priority tasks without assignees
        unassigned_critical = sum(
            1 for task in self.task_progress.values()
            if task.assignee == "unassigned" and task.priority == TaskPriority.CRITICAL
        )

        if unassigned_critical > 0:
            risks.append({
                "type": "resource",
                "level": "medium",
                "description": f"{unassigned_critical} critical task(s) unassigned",
                "impact": "Quality and timeline impact"
            })

        return {
            "total_risks": len(risks),
            "high_risks": sum(1 for r in risks if r["level"] == "high"),
            "risks": risks
        }

    def _generate_next_actions(self) -> List[str]:
        """Generate recommended next actions"""
        actions = []

        # Check for critical tasks
        critical_tasks = [
            task for task in self.task_progress.values()
            if task.priority == TaskPriority.CRITICAL and task.status == "open"
        ]

        if critical_tasks:
            actions.append(f"Address {len(critical_tasks)} critical task(s) immediately")

        # Check for upcoming milestones
        upcoming_milestones = [
            m for m in self.milestones.values()
            if 0 <= (m.due_date - datetime.now()).days <= 3 and m.completion_percentage < 100
        ]

        if upcoming_milestones:
            actions.append(f"Focus on {len(upcoming_milestones)} milestone(s) due within 3 days")

        # Check for GitHub sync
        if self.github_integration:
            actions.append("Sync with GitHub to get latest issue status")

        if not actions:
            actions.append("Continue with planned development and testing activities")

        return actions

    async def export_project_report(self, format: str = "html") -> str:
        """Export comprehensive project report"""
        dashboard = self.generate_project_dashboard()

        if format == "html":
            return await self._export_html_report(dashboard)
        elif format == "json":
            return await self._export_json_report(dashboard)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def _export_html_report(self, dashboard: Dict[str, Any]) -> str:
        """Export HTML project report"""
        report_file = self.project_data_dir / f"project_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Catalynx Version 1 Project Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .milestone {{ background: #e7f3ff; margin: 10px 0; padding: 10px; border-radius: 3px; }}
                .risk-high {{ color: #d73027; }}
                .risk-medium {{ color: #fc8d59; }}
                .progress-bar {{ width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; }}
                .progress-fill {{ height: 100%; background: #4daf4a; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Catalynx Version 1 Project Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Overall Progress: {dashboard['project_overview']['overall_progress']:.1f}%</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {dashboard['project_overview']['overall_progress']:.1f}%"></div>
                </div>
            </div>

            <div class="section">
                <h2>Project Overview</h2>
                <p><strong>Current Phase:</strong> {dashboard['project_overview']['phase']}</p>
                <p><strong>Days to Release:</strong> {dashboard['project_overview']['days_to_release']}</p>
            </div>

            <div class="section">
                <h2>Milestones</h2>
        """

        for milestone in dashboard['milestones']:
            html_content += f"""
                <div class="milestone">
                    <h3>{milestone['title']}</h3>
                    <p>{milestone['completion_percentage']:.1f}% complete - {milestone['days_remaining']} days remaining</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {milestone['completion_percentage']:.1f}%"></div>
                    </div>
                </div>
            """

        html_content += f"""
            </div>

            <div class="section">
                <h2>Task Summary</h2>
                <p><strong>Total Tasks:</strong> {dashboard['task_progress']['total_tasks']}</p>
                <p><strong>Completed:</strong> {dashboard['task_progress']['completed_tasks']}</p>
                <p><strong>In Progress:</strong> {dashboard['task_progress']['in_progress_tasks']}</p>
                <p><strong>Completion Rate:</strong> {dashboard['task_progress']['completion_rate']:.1f}%</p>
            </div>

            <div class="section">
                <h2>Risk Assessment</h2>
                <p><strong>Total Risks:</strong> {dashboard['risk_assessment']['total_risks']}</p>
                <p><strong>High Risks:</strong> {dashboard['risk_assessment']['high_risks']}</p>
        """

        for risk in dashboard['risk_assessment']['risks']:
            risk_class = f"risk-{risk['level']}"
            html_content += f"""
                <p class="{risk_class}"><strong>{risk['type'].upper()}:</strong> {risk['description']} - {risk['impact']}</p>
            """

        html_content += f"""
            </div>

            <div class="section">
                <h2>Next Actions</h2>
                <ul>
        """

        for action in dashboard['next_actions']:
            html_content += f"<li>{action}</li>"

        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """

        with open(report_file, 'w') as f:
            f.write(html_content)

        return str(report_file)

    async def _export_json_report(self, dashboard: Dict[str, Any]) -> str:
        """Export JSON project report"""
        report_file = self.project_data_dir / f"project_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        return str(report_file)

async def main():
    """Main execution for project management system"""
    print("Catalynx Local Project Management System")
    print("GitHub CLI Integration for Project Tracking")
    print("=" * 60)

    manager = LocalProjectManager()

    try:
        # Sync with GitHub if available
        if manager.github_integration:
            print("Synchronizing with GitHub...")
            await manager.sync_with_github()

        # Generate and display dashboard
        print("Generating project dashboard...")
        dashboard = manager.generate_project_dashboard()

        print("\n" + "=" * 60)
        print("PROJECT DASHBOARD")
        print("=" * 60)
        print(f"Project: {dashboard['project_overview']['name']}")
        print(f"Phase: {dashboard['project_overview']['phase']}")
        print(f"Progress: {dashboard['project_overview']['overall_progress']:.1f}%")
        print(f"Days to Release: {dashboard['project_overview']['days_to_release']}")

        print(f"\nMilestones: {len(dashboard['milestones'])}")
        for milestone in dashboard['milestones']:
            print(f"  - {milestone['title']}: {milestone['completion_percentage']:.1f}% ({milestone['days_remaining']} days)")

        print(f"\nTasks: {dashboard['task_progress']['total_tasks']} total, {dashboard['task_progress']['completed_tasks']} completed")
        print(f"Risks: {dashboard['risk_assessment']['total_risks']} total, {dashboard['risk_assessment']['high_risks']} high")

        # Export reports
        print("\nExporting project reports...")
        html_report = await manager.export_project_report("html")
        json_report = await manager.export_project_report("json")

        print(f"HTML Report: {html_report}")
        print(f"JSON Report: {json_report}")

        print("\n🎯 Project management system ready!")

    except KeyboardInterrupt:
        print("\n⏹️ Project management interrupted by user")
    except Exception as e:
        print(f"\n💥 Project management error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())