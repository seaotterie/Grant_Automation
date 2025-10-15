"""
Report Generator Tool
12-Factor compliant tool for professional report generation.

Purpose: Generate masters thesis-level intelligence reports
Cost: $0.00 per report (no AI calls - template-based)
Replaces: N/A (new capability)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional, Dict, Any, List
import time
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
import json
import uuid

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext

try:
    from .report_models import (
        ReportInput,
        ReportOutput,
        ReportSection,
        ReportMetadata,
        ReportTemplate,
        OutputFormat,
        SectionType,
        TEMPLATE_SECTIONS,
        REPORT_GENERATOR_COST
    )
except ImportError:
    from report_models import (
        ReportInput,
        ReportOutput,
        ReportSection,
        ReportMetadata,
        ReportTemplate,
        OutputFormat,
        SectionType,
        TEMPLATE_SECTIONS,
        REPORT_GENERATOR_COST
    )


class ReportGeneratorTool(BaseTool[ReportOutput]):
    """
    12-Factor Report Generator Tool

    Factor 4: Returns structured ReportOutput
    Factor 6: Stateless - pure function rendering
    Factor 10: Single responsibility - report generation only
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize report generator tool."""
        super().__init__(config)

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

        # Output directory
        self.output_dir = Path(config.get("output_dir", "data/reports")) if config else Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_tool_name(self) -> str:
        return "Report Generator Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Professional report generation with masters thesis-level templates"

    async def _execute(
        self,
        context: ToolExecutionContext,
        report_input: ReportInput
    ) -> ReportOutput:
        """Execute report generation."""
        start_time = time.time()

        self.logger.info(
            f"Starting report generation: template={report_input.template_type.value}, "
            f"format={report_input.output_format.value}"
        )

        # Generate report ID
        report_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get sections to include
        sections_to_include = report_input.include_sections or TEMPLATE_SECTIONS.get(
            report_input.template_type, []
        )

        # Generate sections
        sections_generated = self._generate_sections(
            report_input,
            sections_to_include
        )

        # Render report
        report_content = self._render_report(
            report_input,
            sections_generated
        )

        # Determine output path
        if report_input.output_path:
            output_path = Path(report_input.output_path)
        else:
            filename = f"report_{report_input.template_type.value}_{timestamp}_{report_id}.{report_input.output_format.value}"
            output_path = self.output_dir / filename

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content, encoding='utf-8')

        # Calculate metrics
        generation_time = time.time() - start_time
        file_size = output_path.stat().st_size

        # Extract key findings and recommendations
        key_findings, recommendations = self._extract_insights(report_input, sections_generated)

        # Create metadata
        metadata = ReportMetadata(
            generation_timestamp=datetime.now().isoformat(),
            template_used=report_input.template_type.value,
            output_format=report_input.output_format.value,
            sections_count=len(sections_generated),
            total_pages_estimated=self._estimate_pages(sections_generated),
            data_sources_used=self._collect_data_sources(sections_generated),
            generation_time_seconds=generation_time,
            completeness_score=self._calculate_completeness(report_input, sections_generated),
            data_quality_score=self._calculate_data_quality(report_input)
        )

        # Create output
        output = ReportOutput(
            report_id=report_id,
            template_used=report_input.template_type.value,
            file_path=str(output_path),
            format=report_input.output_format.value,
            sections_generated=sections_generated,
            generation_time_seconds=generation_time,
            file_size_bytes=file_size,
            metadata=metadata,
            executive_summary=self._generate_executive_summary(report_input),
            key_findings=key_findings,
            recommendations=recommendations
        )

        self.logger.info(
            f"Completed report generation: file={output_path.name}, "
            f"size={file_size:,} bytes, time={generation_time:.2f}s"
        )

        return output

    def _generate_sections(
        self,
        report_input: ReportInput,
        sections_to_include: List[str]
    ) -> List[ReportSection]:
        """Generate report sections based on template."""
        sections = []

        for section_id in sections_to_include:
            section = self._generate_section(section_id, report_input)
            if section:
                sections.append(section)

        return sections

    def _generate_section(
        self,
        section_id: str,
        report_input: ReportInput
    ) -> Optional[ReportSection]:
        """Generate individual section."""

        # Section generators map
        generators = {
            "executive_summary": self._generate_executive_summary_section,
            "opportunity_overview": self._generate_opportunity_overview,
            "organization_analysis": self._generate_organization_analysis,
            "grantor_intelligence": self._generate_grantor_intelligence,
            "strategic_fit": self._generate_strategic_fit,
            "opportunity_deep_dive": self._generate_opportunity_deep_dive,
            "funding_history": self._generate_funding_history,
            "strategic_approach": self._generate_strategic_approach,
            "network_intelligence": self._generate_network_intelligence,
            "scoring_analysis": self._generate_scoring_analysis,
            "winning_strategy": self._generate_winning_strategy,
            "discover_tab": self._generate_discover_tab,
            "plan_tab": self._generate_plan_tab,
            "analyze_tab": self._generate_analyze_tab,
            "examine_tab": self._generate_examine_tab,
            "approach_tab": self._generate_approach_tab,
            "tier_analysis": self._generate_tier_analysis,
            "system_architecture": self._generate_system_architecture,
            "data_sources": self._generate_data_sources,
            "quality_assurance": self._generate_quality_assurance,
            "key_findings": self._generate_key_findings_section,
            "strategic_recommendation": self._generate_strategic_recommendation,
            "risk_summary": self._generate_risk_summary,
            "next_steps": self._generate_next_steps,
            "risk_assessment_matrix": self._generate_risk_matrix,
            "risk_breakdown": self._generate_risk_breakdown,
            "mitigation_strategies": self._generate_mitigation_strategies,
            "probability_analysis": self._generate_probability_analysis,
            "impact_analysis": self._generate_impact_analysis,
            "recommendations": self._generate_recommendations_section,
            "implementation_timeline": self._generate_implementation_timeline,
            "resource_requirements": self._generate_resource_requirements,
            "key_milestones": self._generate_key_milestones,
            "success_metrics": self._generate_success_metrics,
            "risk_mitigation": self._generate_risk_mitigation,
            "action_plan": self._generate_action_plan
        }

        generator = generators.get(section_id)
        if generator:
            return generator(report_input)

        return None

    # Section generators (comprehensive template)

    def _generate_executive_summary_section(self, report_input: ReportInput) -> ReportSection:
        """Generate executive summary section."""
        content = f"""
        <div class="section" id="executive-summary">
            <h2>Executive Summary</h2>
            <div class="summary-content">
                <h3>Opportunity Overview</h3>
                <p><strong>{report_input.opportunity_data.get('title', 'N/A')}</strong></p>
                <p>{report_input.opportunity_data.get('description', 'No description available')}</p>

                <h3>Overall Assessment</h3>
                {self._render_overall_assessment(report_input)}

                <h3>Recommendation</h3>
                {self._render_recommendation(report_input)}
            </div>
        </div>
        """

        return ReportSection(
            section_id="executive_summary",
            section_title="Executive Summary",
            content_type=SectionType.TEXT,
            content=content,
            data_sources=["opportunity_data", "scoring_results"]
        )

    def _generate_opportunity_overview(self, report_input: ReportInput) -> ReportSection:
        """Generate opportunity overview section."""
        opp = report_input.opportunity_data

        content = f"""
        <div class="section" id="opportunity-overview">
            <h2>Opportunity Overview</h2>
            <table class="data-table">
                <tr><th>Title</th><td>{opp.get('title', 'N/A')}</td></tr>
                <tr><th>Award Amount</th><td>${opp.get('award_amount', 0):,}</td></tr>
                <tr><th>Deadline</th><td>{opp.get('deadline', 'N/A')}</td></tr>
                <tr><th>Location</th><td>{opp.get('location', 'N/A')}</td></tr>
                <tr><th>Opportunity ID</th><td>{opp.get('opportunity_id', 'N/A')}</td></tr>
            </table>
        </div>
        """

        return ReportSection(
            section_id="opportunity_overview",
            section_title="Opportunity Overview",
            content_type=SectionType.TABLE,
            content=content,
            data_sources=["opportunity_data"]
        )

    def _generate_organization_analysis(self, report_input: ReportInput) -> ReportSection:
        """Generate organization analysis section."""
        org = report_input.organization_data

        content = f"""
        <div class="section" id="organization-analysis">
            <h2>Organization Analysis</h2>
            <table class="data-table">
                <tr><th>Organization</th><td>{org.get('name', 'N/A')}</td></tr>
                <tr><th>EIN</th><td>{org.get('ein', 'N/A')}</td></tr>
                <tr><th>Location</th><td>{org.get('location', 'N/A')}</td></tr>
                <tr><th>Revenue</th><td>${org.get('revenue', 0):,}</td></tr>
                <tr><th>Type</th><td>{org.get('organization_type', 'N/A')}</td></tr>
                <tr><th>Years Operating</th><td>{org.get('years_operating', 'N/A')}</td></tr>
            </table>

            <h3>Mission</h3>
            <p>{org.get('mission', 'No mission statement available')}</p>
        </div>
        """

        return ReportSection(
            section_id="organization_analysis",
            section_title="Organization Analysis",
            content_type=SectionType.TABLE,
            content=content,
            data_sources=["organization_data"]
        )

    def _generate_scoring_analysis(self, report_input: ReportInput) -> ReportSection:
        """Generate scoring analysis section."""
        if not report_input.scoring_results:
            content = "<p>No scoring data available</p>"
        else:
            content = "<div class='section' id='scoring-analysis'><h2>Scoring Analysis</h2>"

            for score_data in report_input.scoring_results:
                content += f"""
                <h3>{score_data.get('stage', 'Unknown Stage').title()} Stage</h3>
                <p><strong>Overall Score:</strong> {score_data.get('overall_score', 0):.1%}</p>
                <p><strong>Confidence:</strong> {score_data.get('confidence', 0):.1%}</p>

                <h4>Dimensional Breakdown:</h4>
                <table class='data-table'>
                    <tr><th>Dimension</th><th>Score</th><th>Weight</th></tr>
                """

                for dim in score_data.get('dimensional_scores', []):
                    content += f"""
                    <tr>
                        <td>{dim.get('dimension_name', 'N/A').replace('_', ' ').title()}</td>
                        <td>{dim.get('raw_score', 0):.1%}</td>
                        <td>{dim.get('weight', 0):.2f}</td>
                    </tr>
                    """

                content += "</table>"

            content += "</div>"

        return ReportSection(
            section_id="scoring_analysis",
            section_title="Scoring Analysis",
            content_type=SectionType.TABLE,
            content=content,
            data_sources=["scoring_results"]
        )

    def _generate_network_intelligence(self, report_input: ReportInput) -> ReportSection:
        """Generate network intelligence section."""
        network_data = report_input.network_data or {}

        content = f"""
        <div class="section" id="network-intelligence">
            <h2>Network Intelligence</h2>
            <p>Board Size: {network_data.get('board_size', 'N/A')}</p>
            <p>Key Connections: {network_data.get('key_connections', 'N/A')}</p>
        </div>
        """

        return ReportSection(
            section_id="network_intelligence",
            section_title="Network Intelligence",
            content_type=SectionType.TEXT,
            content=content,
            data_sources=["network_data"]
        )

    # Placeholder generators for other sections
    def _generate_grantor_intelligence(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("grantor_intelligence", "Grantor Intelligence", SectionType.TEXT,
                           "<div class='section'><h2>Grantor Intelligence</h2><p>Analysis pending</p></div>", ["intelligence_data"])

    def _generate_strategic_fit(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("strategic_fit", "Strategic Fit", SectionType.TEXT,
                           "<div class='section'><h2>Strategic Fit</h2><p>Analysis pending</p></div>", ["scoring_results"])

    def _generate_opportunity_deep_dive(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("opportunity_deep_dive", "Opportunity Deep Dive", SectionType.TEXT,
                           "<div class='section'><h2>Opportunity Deep Dive</h2><p>Analysis pending</p></div>", ["intelligence_data"])

    def _generate_funding_history(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("funding_history", "Funding History", SectionType.TABLE,
                           "<div class='section'><h2>Funding History</h2><p>Analysis pending</p></div>", ["financial_data"])

    def _generate_strategic_approach(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("strategic_approach", "Strategic Approach", SectionType.TEXT,
                           "<div class='section'><h2>Strategic Approach</h2><p>Recommendations pending</p></div>", ["scoring_results"])

    def _generate_winning_strategy(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("winning_strategy", "Winning Strategy", SectionType.LIST,
                           "<div class='section'><h2>Winning Strategy</h2><p>Strategy pending</p></div>", ["intelligence_data"])

    def _generate_discover_tab(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("discover_tab", "DISCOVER Tab Analysis", SectionType.TEXT,
                           "<div class='section'><h2>DISCOVER Tab Analysis</h2><p>Analysis pending</p></div>", ["scoring_results"])

    def _generate_plan_tab(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("plan_tab", "PLAN Tab Analysis", SectionType.TEXT,
                           "<div class='section'><h2>PLAN Tab Analysis</h2><p>Analysis pending</p></div>", ["scoring_results"])

    def _generate_analyze_tab(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("analyze_tab", "ANALYZE Tab Analysis", SectionType.TEXT,
                           "<div class='section'><h2>ANALYZE Tab Analysis</h2><p>Analysis pending</p></div>", ["scoring_results"])

    def _generate_examine_tab(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("examine_tab", "EXAMINE Tab Analysis", SectionType.TEXT,
                           "<div class='section'><h2>EXAMINE Tab Analysis</h2><p>Analysis pending</p></div>", ["intelligence_data"])

    def _generate_approach_tab(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("approach_tab", "APPROACH Tab Analysis", SectionType.TEXT,
                           "<div class='section'><h2>APPROACH Tab Analysis</h2><p>Recommendations pending</p></div>", ["scoring_results"])

    def _generate_tier_analysis(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("tier_analysis", "Tier Analysis", SectionType.TABLE,
                           "<div class='section'><h2>Tier Analysis</h2><p>Analysis pending</p></div>", ["intelligence_data"])

    def _generate_system_architecture(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("system_architecture", "System Architecture", SectionType.TEXT,
                           "<div class='section'><h2>System Architecture</h2><p>Documentation pending</p></div>", [])

    def _generate_data_sources(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("data_sources", "Data Sources", SectionType.LIST,
                           "<div class='section'><h2>Data Sources</h2><p>Documentation pending</p></div>", [])

    def _generate_quality_assurance(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("quality_assurance", "Quality Assurance", SectionType.TEXT,
                           "<div class='section'><h2>Quality Assurance</h2><p>Metrics pending</p></div>", [])

    # Executive template sections
    def _generate_key_findings_section(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("key_findings", "Key Findings", SectionType.LIST,
                           "<div class='section'><h2>Key Findings</h2><p>Findings pending</p></div>", ["scoring_results"])

    def _generate_strategic_recommendation(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("strategic_recommendation", "Strategic Recommendation", SectionType.TEXT,
                           "<div class='section'><h2>Strategic Recommendation</h2><p>Recommendation pending</p></div>", ["scoring_results"])

    def _generate_risk_summary(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("risk_summary", "Risk Summary", SectionType.TEXT,
                           "<div class='section'><h2>Risk Summary</h2><p>Summary pending</p></div>", ["risk_data"])

    def _generate_next_steps(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("next_steps", "Next Steps", SectionType.LIST,
                           "<div class='section'><h2>Next Steps</h2><p>Steps pending</p></div>", ["scoring_results"])

    # Risk template sections
    def _generate_risk_matrix(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("risk_assessment_matrix", "Risk Assessment Matrix", SectionType.MATRIX,
                           "<div class='section'><h2>Risk Assessment Matrix</h2><p>Matrix pending</p></div>", ["risk_data"])

    def _generate_risk_breakdown(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("risk_breakdown", "Risk Breakdown", SectionType.TABLE,
                           "<div class='section'><h2>Risk Breakdown</h2><p>Breakdown pending</p></div>", ["risk_data"])

    def _generate_mitigation_strategies(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("mitigation_strategies", "Mitigation Strategies", SectionType.LIST,
                           "<div class='section'><h2>Mitigation Strategies</h2><p>Strategies pending</p></div>", ["risk_data"])

    def _generate_probability_analysis(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("probability_analysis", "Probability Analysis", SectionType.CHART,
                           "<div class='section'><h2>Probability Analysis</h2><p>Analysis pending</p></div>", ["risk_data"])

    def _generate_impact_analysis(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("impact_analysis", "Impact Analysis", SectionType.CHART,
                           "<div class='section'><h2>Impact Analysis</h2><p>Analysis pending</p></div>", ["risk_data"])

    def _generate_recommendations_section(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("recommendations", "Recommendations", SectionType.LIST,
                           "<div class='section'><h2>Recommendations</h2><p>Recommendations pending</p></div>", ["risk_data"])

    # Implementation template sections
    def _generate_implementation_timeline(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("implementation_timeline", "Implementation Timeline", SectionType.CHART,
                           "<div class='section'><h2>Implementation Timeline</h2><p>Timeline pending</p></div>", [])

    def _generate_resource_requirements(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("resource_requirements", "Resource Requirements", SectionType.TABLE,
                           "<div class='section'><h2>Resource Requirements</h2><p>Requirements pending</p></div>", [])

    def _generate_key_milestones(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("key_milestones", "Key Milestones", SectionType.LIST,
                           "<div class='section'><h2>Key Milestones</h2><p>Milestones pending</p></div>", [])

    def _generate_success_metrics(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("success_metrics", "Success Metrics", SectionType.TABLE,
                           "<div class='section'><h2>Success Metrics</h2><p>Metrics pending</p></div>", [])

    def _generate_risk_mitigation(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("risk_mitigation", "Risk Mitigation", SectionType.LIST,
                           "<div class='section'><h2>Risk Mitigation</h2><p>Mitigation pending</p></div>", ["risk_data"])

    def _generate_action_plan(self, report_input: ReportInput) -> ReportSection:
        return ReportSection("action_plan", "Action Plan", SectionType.LIST,
                           "<div class='section'><h2>Action Plan</h2><p>Plan pending</p></div>", [])

    # Helper methods

    def _render_report(
        self,
        report_input: ReportInput,
        sections: List[ReportSection]
    ) -> str:
        """Render complete report using template."""
        try:
            template = self.jinja_env.get_template(f"{report_input.template_type.value}.html")
        except:
            # Fallback to basic template
            template = self._get_basic_template()

        return template.render(
            title=report_input.custom_title or f"{report_input.template_type.value.title()} Report",
            subtitle=report_input.custom_subtitle or "Grant Intelligence Analysis",
            opportunity=report_input.opportunity_data,
            organization=report_input.organization_data,
            sections=sections,
            generation_date=datetime.now().strftime("%B %d, %Y")
        )

    def _get_basic_template(self) -> Template:
        """Get basic HTML template as fallback."""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #2c3e50; }
        .section { margin: 30px 0; page-break-inside: avoid; }
        table.data-table { width: 100%; border-collapse: collapse; }
        table.data-table th, table.data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        table.data-table th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p><em>{{ subtitle }}</em></p>
    <p>Generated: {{ generation_date }}</p>

    {% for section in sections %}
        {{ section.content | safe }}
    {% endfor %}
</body>
</html>
        """
        return self.jinja_env.from_string(template_str)

    def _render_overall_assessment(self, report_input: ReportInput) -> str:
        """Render overall assessment from scoring data."""
        if not report_input.scoring_results:
            return "<p>No assessment data available</p>"

        latest_score = report_input.scoring_results[-1] if report_input.scoring_results else {}
        overall = latest_score.get('overall_score', 0)

        return f"<p>Overall Score: <strong>{overall:.1%}</strong></p>"

    def _render_recommendation(self, report_input: ReportInput) -> str:
        """Render recommendation from scoring data."""
        if not report_input.scoring_results:
            return "<p>No recommendation available</p>"

        latest_score = report_input.scoring_results[-1] if report_input.scoring_results else {}
        proceed = latest_score.get('proceed_recommendation', False)

        if proceed:
            return "<p><strong>PROCEED</strong> - This opportunity is recommended for pursuit</p>"
        else:
            return "<p><strong>REVIEW</strong> - Additional analysis recommended before proceeding</p>"

    def _generate_executive_summary(self, report_input: ReportInput) -> Optional[str]:
        """Generate executive summary text."""
        opp_title = report_input.opportunity_data.get('title', 'Unknown Opportunity')
        org_name = report_input.organization_data.get('name', 'Unknown Organization')

        return f"Analysis of {opp_title} for {org_name}"

    def _extract_insights(
        self,
        report_input: ReportInput,
        sections: List[ReportSection]
    ) -> tuple[List[str], List[str]]:
        """Extract key findings and recommendations."""
        findings = []
        recommendations = []

        if report_input.scoring_results:
            for score in report_input.scoring_results:
                findings.extend(score.get('key_strengths', []))
                recommendations.extend(score.get('recommended_actions', []))

        return findings[:5], recommendations[:5]

    def _estimate_pages(self, sections: List[ReportSection]) -> int:
        """Estimate number of pages in report."""
        return max(1, len(sections) // 3)

    def _collect_data_sources(self, sections: List[ReportSection]) -> List[str]:
        """Collect all data sources used."""
        sources = set()
        for section in sections:
            sources.update(section.data_sources)
        return sorted(list(sources))

    def _calculate_completeness(
        self,
        report_input: ReportInput,
        sections: List[ReportSection]
    ) -> float:
        """Calculate report completeness score."""
        expected_sections = TEMPLATE_SECTIONS.get(report_input.template_type, [])
        if not expected_sections:
            return 1.0

        return len(sections) / len(expected_sections)

    def _calculate_data_quality(self, report_input: ReportInput) -> float:
        """Calculate data quality score."""
        score = 0.6  # Base score

        if report_input.scoring_results:
            score += 0.1
        if report_input.intelligence_data:
            score += 0.1
        if report_input.financial_data:
            score += 0.1
        if report_input.network_data:
            score += 0.1

        return min(1.0, score)

    def get_cost_estimate(self) -> Optional[float]:
        return REPORT_GENERATOR_COST

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate tool inputs."""
        report_input = kwargs.get("report_input")

        if not report_input:
            return False, "report_input is required"

        if not isinstance(report_input, ReportInput):
            return False, "report_input must be ReportInput instance"

        if not report_input.opportunity_data:
            return False, "opportunity_data is required"

        if not report_input.organization_data:
            return False, "organization_data is required"

        return True, None


# Convenience function
async def generate_report(
    template_type: str,
    opportunity_data: Dict[str, Any],
    organization_data: Dict[str, Any],
    scoring_results: Optional[List[Dict[str, Any]]] = None,
    intelligence_data: Optional[Dict[str, Any]] = None,
    financial_data: Optional[Dict[str, Any]] = None,
    network_data: Optional[Dict[str, Any]] = None,
    risk_data: Optional[Dict[str, Any]] = None,
    output_format: str = "html",
    config: Optional[dict] = None
) -> ToolResult[ReportOutput]:
    """Generate a professional intelligence report."""

    tool = ReportGeneratorTool(config)

    template_enum = ReportTemplate(template_type)
    format_enum = OutputFormat(output_format)

    report_input = ReportInput(
        template_type=template_enum,
        opportunity_data=opportunity_data,
        organization_data=organization_data,
        scoring_results=scoring_results,
        intelligence_data=intelligence_data,
        financial_data=financial_data,
        network_data=network_data,
        risk_data=risk_data,
        output_format=format_enum
    )

    return await tool.execute(report_input=report_input)
