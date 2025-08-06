#!/usr/bin/env python3
"""
Grant Research Automation - Main Entry Point
Command-line interface and application launcher.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import click
import logging
from datetime import datetime

from src.auth.config_manager import get_config
from src.core.workflow_engine import get_workflow_engine
from src.core.data_models import WorkflowConfig
from src.processors.registry import register_all_processors


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config-env', '-e', help='Configuration environment (dev/test/prod)')
def cli(verbose: bool, config_env: str):
    """Grant Research Automation - Main CLI."""
    # Load configuration
    config = get_config()
    if config_env:
        from src.auth.config_manager import reload_config
        config = reload_config(config_env)
    
    # Set up logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Auto-register all processors
    try:
        registered_count = register_all_processors()
        logging.getLogger(__name__).info(f"Auto-registered {registered_count} processors")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to auto-register processors: {e}")


@cli.command()
@click.option('--target-ein', help='Target EIN for similarity analysis')
@click.option('--states', help='Comma-separated list of states (e.g., VA,MD,DC)')
@click.option('--ntee-codes', help='Comma-separated NTEE codes (e.g., P81,E31)')
@click.option('--min-revenue', type=int, default=100000, help='Minimum revenue threshold')
@click.option('--max-results', type=int, default=100, help='Maximum results to process')
@click.option('--output-dir', help='Output directory for results')
@click.option('--name', help='Workflow name')
@click.option('--include-classified', is_flag=True, help='Include organizations classified by intelligent classifier')
@click.option('--classification-score-threshold', type=float, default=0.5, help='Minimum classification score for included organizations (default: 0.5)')
def run_workflow(target_ein: str, states: str, ntee_codes: str, min_revenue: int, 
                max_results: int, output_dir: str, name: str, include_classified: bool, classification_score_threshold: float):
    """Run a complete grant research workflow."""
    click.echo("Starting Grant Research Workflow...")
    
    # Parse input parameters
    state_list = states.split(',') if states else ['VA']
    ntee_list = ntee_codes.split(',') if ntee_codes else ['P81', 'E31', 'W70']
    
    # Create workflow configuration
    config = WorkflowConfig(
        workflow_id=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=name or "CLI Workflow",
        target_ein=target_ein,
        states=state_list,
        ntee_codes=ntee_list,
        min_revenue=min_revenue,
        max_results=max_results,
        include_classified_organizations=include_classified,
        classification_score_threshold=classification_score_threshold
    )
    
    click.echo(f"Workflow ID: {config.workflow_id}")
    click.echo(f"Target EIN: {config.target_ein or 'None'}")
    click.echo(f"States: {', '.join(state_list)}")
    click.echo(f"NTEE Codes: {', '.join(ntee_list)}")
    click.echo(f"Min Revenue: ${config.min_revenue:,}")
    click.echo(f"Max Results: {config.max_results}")
    
    if include_classified:
        click.echo(f"Include Classified Orgs: Yes (score >= {classification_score_threshold})")
    else:
        click.echo("Include Classified Orgs: No (NTEE-coded only)")
    
    # Run workflow
    async def run():
        engine = get_workflow_engine()
        
        # Add progress callback
        def progress_callback(workflow_id: str, progress: float, message: str):
            click.echo(f"Progress: {progress:.1f}% - {message}")
        
        engine.add_progress_callback(progress_callback)
        
        try:
            workflow_state = await engine.run_workflow(config)
            
            if workflow_state.status.value == "completed":
                click.echo("SUCCESS: Workflow completed successfully!")
                click.echo(f"Organizations processed: {workflow_state.organizations_processed}")
                click.echo(f"Execution time: {workflow_state.get_execution_time():.2f} seconds")
            else:
                click.echo(f"FAILED: Workflow failed with status: {workflow_state.status.value}")
                if workflow_state.errors:
                    click.echo("Errors:")
                    for error in workflow_state.errors:
                        click.echo(f"  - {error}")
        
        except Exception as e:
            click.echo(f"ERROR: Workflow execution failed: {e}")
            sys.exit(1)
    
    # Run the async workflow
    asyncio.run(run())


@cli.command()
def list_workflows():
    """List all workflows."""
    engine = get_workflow_engine()
    workflows = engine.list_workflows()
    
    if not workflows:
        click.echo("No workflows found.")
        return
    
    click.echo(f"Found {len(workflows)} workflows:")
    click.echo()
    
    for workflow in workflows:
        status_emoji = {
            "pending": "⏳",
            "running": "🔄", 
            "completed": "✅",
            "failed": "❌",
            "paused": "⏸️",
            "cancelled": "🚫"
        }
        
        emoji = status_emoji.get(workflow.status.value, "❓")
        click.echo(f"{emoji} {workflow.workflow_id}")
        click.echo(f"   Status: {workflow.status.value}")
        click.echo(f"   Created: {workflow.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if workflow.start_time:
            click.echo(f"   Started: {workflow.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if workflow.end_time:
            click.echo(f"   Ended: {workflow.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if workflow.get_execution_time():
                click.echo(f"   Duration: {workflow.get_execution_time():.2f} seconds")
        
        if workflow.organizations_processed:
            click.echo(f"   Organizations: {workflow.organizations_processed}")
        
        if workflow.progress_percentage:
            click.echo(f"   Progress: {workflow.progress_percentage:.1f}%")
        
        click.echo()


@cli.command()
@click.argument('workflow_id')
def workflow_status(workflow_id: str):
    """Get detailed status of a specific workflow."""
    engine = get_workflow_engine()
    workflow = engine.get_workflow_state(workflow_id)
    
    if not workflow:
        click.echo(f"Workflow not found: {workflow_id}")
        sys.exit(1)
    
    click.echo(f"Workflow: {workflow_id}")
    click.echo(f"Status: {workflow.status.value}")
    click.echo(f"Created: {workflow.created_at}")
    
    if workflow.start_time:
        click.echo(f"Started: {workflow.start_time}")
    if workflow.end_time:
        click.echo(f"Ended: {workflow.end_time}")
    
    execution_time = workflow.get_execution_time()
    if execution_time:
        click.echo(f"Execution time: {execution_time:.2f} seconds")
    
    click.echo(f"Progress: {workflow.progress_percentage:.1f}%")
    click.echo(f"Current processor: {workflow.current_processor or 'None'}")
    
    click.echo(f"Completed processors: {len(workflow.completed_processors)}")
    for processor in workflow.completed_processors:
        click.echo(f"  ✅ {processor}")
    
    if workflow.failed_processors:
        click.echo(f"Failed processors: {len(workflow.failed_processors)}")
        for processor in workflow.failed_processors:
            click.echo(f"  ❌ {processor}")
    
    if workflow.errors:
        click.echo("Errors:")
        for error in workflow.errors:
            click.echo(f"  - {error}")
    
    if workflow.warnings:
        click.echo("Warnings:")
        for warning in workflow.warnings:
            click.echo(f"  - {warning}")


@cli.command()
@click.option('--state', default='VA', help='State to analyze (default: VA)')
@click.option('--min-score', type=float, default=0.3, help='Minimum composite score threshold (default: 0.3)')
@click.option('--max-results', type=int, help='Maximum promising candidates to display')
@click.option('--export', is_flag=True, help='Export results to CSV file')
@click.option('--detailed', is_flag=True, help='Show detailed breakdown for top candidates')
def classify_organizations(state: str, min_score: float, max_results: int, export: bool, detailed: bool):
    """Run intelligent classification on organizations without NTEE codes."""
    click.echo("Starting Intelligent Classification Analysis...")
    click.echo("=" * 50)
    
    # Create configuration
    config = WorkflowConfig(
        workflow_id=f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name="Intelligent Classification",
        states=[state],
        max_results=50000  # Process all available
    )
    
    click.echo(f"State: {state}")
    click.echo(f"Score threshold: {min_score}")
    click.echo()
    
    async def run_classification():
        from src.processors.analysis.intelligent_classifier import IntelligentClassifier
        from src.core.data_models import ProcessorConfig
        
        # Create processor config
        processor_config = ProcessorConfig(
            workflow_id=config.workflow_id,
            processor_name="intelligent_classifier",
            workflow_config=config
        )
        
        # Initialize and run classifier
        classifier = IntelligentClassifier()
        
        try:
            click.echo("Loading unclassified organizations...")
            result = await classifier.execute(processor_config)
            
            if not result.success:
                click.echo("FAILED: Classification failed")
                for error in result.errors:
                    click.echo(f"  Error: {error}")
                return
            
            # Extract results
            classified_orgs = result.data.get('classified_organizations', [])
            promising_candidates = result.data.get('promising_candidates', [])
            total_unclassified = result.data.get('total_unclassified', 0)
            
            # Apply score filter
            promising_candidates = [
                org for org in promising_candidates 
                if org['composite_score'] >= min_score
            ]
            
            # Apply result limit
            if max_results and len(promising_candidates) > max_results:
                promising_candidates = promising_candidates[:max_results]
            
            click.echo("SUCCESS: Classification completed!")
            click.echo()
            
            # Summary statistics
            click.echo("Classification Results:")
            click.echo(f"  Total unclassified organizations: {total_unclassified:,}")
            click.echo(f"  Promising candidates (score >= {min_score}): {len(promising_candidates):,}")
            click.echo(f"  Success rate: {len(promising_candidates)/total_unclassified*100:.1f}%")
            click.echo()
            
            # Category breakdown
            category_breakdown = result.metadata.get('category_breakdown', {})
            click.echo("Category Breakdown:")
            for category, count in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
                percentage = count / len(promising_candidates) * 100 if promising_candidates else 0
                click.echo(f"  {category.title()}: {count:,} ({percentage:.1f}%)")
            click.echo()
            
            # NEW: Qualification factor analysis
            if promising_candidates:
                qualification_breakdown = {}
                strength_breakdown = {}
                
                for org in promising_candidates:
                    if 'primary_qualification_reason' in org:
                        # Extract primary factor type
                        reason = org['primary_qualification_reason']
                        if 'keyword match' in reason.lower():
                            primary_factor = 'Keyword Match'
                        elif 'financial capacity' in reason.lower():
                            primary_factor = 'Financial Strength'
                        elif 'foundation type' in reason.lower():
                            primary_factor = 'Foundation Type'
                        elif 'geographic' in reason.lower():
                            primary_factor = 'Geographic Match'
                        else:
                            primary_factor = 'Other'
                        
                        qualification_breakdown[primary_factor] = qualification_breakdown.get(primary_factor, 0) + 1
                        
                        # Track strength distribution
                        strength = org.get('qualification_strength', 'Unknown')
                        strength_breakdown[strength] = strength_breakdown.get(strength, 0) + 1
                
                click.echo("Qualification Factor Breakdown:")
                for factor, count in sorted(qualification_breakdown.items(), key=lambda x: x[1], reverse=True):
                    percentage = count / len(promising_candidates) * 100
                    click.echo(f"  {factor}: {count:,} ({percentage:.1f}%)")
                click.echo()
                
                click.echo("Qualification Strength Distribution:")
                for strength, count in sorted(strength_breakdown.items(), key=lambda x: x[1], reverse=True):
                    percentage = count / len(promising_candidates) * 100
                    click.echo(f"  {strength}: {count:,} ({percentage:.1f}%)")
                click.echo()
            
            # Top candidates
            display_count = min(20, len(promising_candidates))
            click.echo(f"Top {display_count} Candidates:")
            click.echo("Rank | Score | Category  | EIN       | Organization Name")
            click.echo("-" * 80)
            
            for i, org in enumerate(promising_candidates[:display_count]):
                score = org['composite_score']
                category = org['predicted_category']
                ein = org['ein']
                name = org['name'][:40]
                click.echo(f"{i+1:4d} | {score:.3f} | {category:9s} | {ein} | {name}")
            
            # Detailed breakdown if requested
            if detailed and promising_candidates:
                click.echo()
                click.echo("Detailed Analysis - Top 5 Candidates:")
                for i, org in enumerate(promising_candidates[:5]):
                    click.echo(f"\n{i+1}. {org['name']} (EIN: {org['ein']})")
                    click.echo(f"   Composite Score: {org['composite_score']:.3f}")
                    click.echo(f"   Predicted Category: {org['predicted_category']}")
                    
                    # NEW: Show qualification analysis
                    if 'primary_qualification_reason' in org:
                        click.echo(f"   Primary Qualification: {org['primary_qualification_reason']}")
                        click.echo(f"   Qualification Strength: {org['qualification_strength']}")
                        if org.get('qualification_factors', {}).get('qualification_details'):
                            click.echo(f"   Details: {'; '.join(org['qualification_factors']['qualification_details'])}")
                    
                    click.echo(f"   Keyword Scores: Health={org['keyword_scores']['health']:.2f}, "
                              f"Nutrition={org['keyword_scores']['nutrition']:.2f}, "
                              f"Safety={org['keyword_scores']['safety']:.2f}")
                    click.echo(f"   Financial Score: {org['financial_score']:.3f}")
                    if org.get('assets'):
                        click.echo(f"   Assets: ${org['assets']:,.0f}")
                    if org.get('revenue'):
                        click.echo(f"   Revenue: ${org['revenue']:,.0f}")
                    click.echo(f"   Location: {org['city']}, {org['state']}")
            
            # Export if requested
            if export:
                import csv
                from pathlib import Path
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                export_file = Path(f"intelligent_classification_results_{timestamp}.csv")
                
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    if promising_candidates:
                        writer = csv.DictWriter(f, fieldnames=promising_candidates[0].keys())
                        writer.writeheader()
                        writer.writerows(promising_candidates)
                
                click.echo(f"\nExported {len(promising_candidates)} results to: {export_file}")
            
            # Score distribution
            click.echo(f"\nScore Distribution:")
            score_ranges = [(0.8, 1.0), (0.6, 0.8), (0.4, 0.6), (0.3, 0.4), (0.2, 0.3), (0.0, 0.2)]
            for min_range, max_range in score_ranges:
                count = len([org for org in classified_orgs 
                           if min_range <= org['composite_score'] < max_range])
                click.echo(f"  {min_range:.1f} - {max_range:.1f}: {count:,} organizations")
        
        except Exception as e:
            click.echo(f"ERROR: Classification failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Run the classification
    asyncio.run(run_classification())


@cli.command()
def list_processors():
    """List all available processors."""
    engine = get_workflow_engine()
    processors = engine.registry.list_processors()
    
    if not processors:
        click.echo("No processors registered.")
        click.echo("You need to create and register processors first.")
        return
    
    click.echo(f"Available processors ({len(processors)}):")
    
    for processor_name in processors:
        info = engine.registry.get_processor_info(processor_name)
        if info:
            click.echo(f"  * {processor_name}")
            click.echo(f"     Description: {info.get('description', 'No description')}")
            click.echo(f"     Version: {info.get('version', 'Unknown')}")
            click.echo(f"     Type: {info.get('processor_type', 'generic')}")
            if info.get('dependencies'):
                click.echo(f"     Dependencies: {', '.join(info['dependencies'])}")
            click.echo()


@cli.command()
def dashboard():
    """Launch the Streamlit dashboard."""
    import subprocess
    import os
    
    dashboard_path = Path(__file__).parent / "src" / "dashboard" / "app.py"
    
    if not dashboard_path.exists():
        click.echo("Dashboard not found. It will be created in the next phase.")
        sys.exit(1)
    
    click.echo("Starting Streamlit dashboard...")
    click.echo("Dashboard will open in your web browser.")
    click.echo("Press Ctrl+C to stop the dashboard.")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path)
        ], check=True)
    except KeyboardInterrupt:
        click.echo("\nDashboard stopped.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to start dashboard: {e}")
        sys.exit(1)


@cli.command()
def system_info():
    """Show system information and statistics."""
    click.echo("Grant Research Automation - System Information")
    click.echo("=" * 50)
    
    # Configuration info
    config = get_config()
    click.echo(f"App Name: {config.app_name}")
    click.echo(f"Version: {config.version}")
    click.echo(f"Environment: {config.environment}")
    click.echo(f"Debug Mode: {config.debug}")
    click.echo()
    
    # Workflow engine info
    engine = get_workflow_engine()
    stats = engine.get_workflow_statistics()
    
    click.echo("Workflow Statistics:")
    click.echo(f"  Total workflows: {stats['total_workflows']}")
    click.echo(f"  Active workflows: {stats['active_workflows']}")
    click.echo(f"  Available processors: {stats['available_processors']}")
    
    if stats['average_execution_time']:
        click.echo(f"  Average execution time: {stats['average_execution_time']:.2f}s")
    
    click.echo("\nWorkflow status counts:")
    for status, count in stats['status_counts'].items():
        if count > 0:
            click.echo(f"  {status}: {count}")
    
    click.echo()
    
    # Authentication status
    try:
        from src.auth.api_key_manager import get_api_key_manager
        from src.auth.dashboard_auth import get_dashboard_auth
        
        api_manager = get_api_key_manager()
        dashboard_auth = get_dashboard_auth()
        
        click.echo("Authentication Status:")
        click.echo(f"  API key storage: {'Found' if api_manager.storage_path.exists() else 'Not found'}")
        
        users = dashboard_auth.list_users()
        click.echo(f"  Dashboard users: {len(users)}")
        
    except Exception as e:
        click.echo(f"Authentication status: Error ({e})")


if __name__ == '__main__':
    cli()