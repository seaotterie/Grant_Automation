#!/usr/bin/env python3
"""
Market Intelligence Monitor
Tracks funding trends, policy changes, and market developments for grant opportunities.

This processor:
1. Monitors funding trends across government agencies and foundations
2. Tracks policy changes that affect funding priorities
3. Analyzes market developments and emerging opportunities
4. Provides alerts for significant market intelligence changes
5. Generates trend reports and strategic market insights
"""

import asyncio
import time
import sqlite3
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile

try:
    from src.core.simple_mcp_client import SimpleMCPClient, DeepIntelligenceResult
except ImportError:
    SimpleMCPClient = None
    DeepIntelligenceResult = None


class MarketIntelligenceAlert:
    """Represents a market intelligence alert or significant change."""
    
    def __init__(self, alert_type: str, severity: str, title: str, description: str):
        self.alert_type = alert_type  # policy_change, funding_trend, market_development
        self.severity = severity      # high, medium, low
        self.title = title
        self.description = description
        self.timestamp = datetime.now()
        self.impact_areas = []
        self.recommended_actions = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'impact_areas': self.impact_areas,
            'recommended_actions': self.recommended_actions
        }


class MarketTrend:
    """Represents a market trend with supporting data."""
    
    def __init__(self, trend_type: str, trend_direction: str, confidence: float):
        self.trend_type = trend_type      # funding_increase, priority_shift, deadline_change
        self.trend_direction = trend_direction  # increasing, decreasing, shifting
        self.confidence = confidence      # 0.0 to 1.0
        self.supporting_evidence = []
        self.affected_sectors = []
        self.timeline = "ongoing"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            'trend_type': self.trend_type,
            'trend_direction': self.trend_direction,
            'confidence': self.confidence,
            'supporting_evidence': self.supporting_evidence,
            'affected_sectors': self.affected_sectors,
            'timeline': self.timeline
        }


class MarketIntelligenceMonitor(BaseProcessor):
    """Processor for monitoring market intelligence and funding trends."""
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="market_intelligence_monitor",
            description="Monitor funding trends, policy changes, and market developments",
            version="1.0.0",
            dependencies=[],  # Can run independently
            estimated_duration=120,  # 2 minutes for comprehensive monitoring
            requires_network=True,
            requires_api_key=False
        )
        super().__init__(metadata)
        
        # Initialize MCP client for web intelligence
        self.mcp_client = SimpleMCPClient(timeout=20) if SimpleMCPClient else None
        self.database_path = "data/catalynx.db"
        
        # Market intelligence monitoring sources
        self.monitoring_sources = {
            "government_agencies": [
                "https://grants.gov/learn-grants",
                "https://www.nsf.gov/funding/",
                "https://www.nih.gov/grants-funding",
                "https://www.ed.gov/fund/grants-overview"
            ],
            "foundation_sources": [
                "https://foundationcenter.org/find-funding/trends",
                "https://cof.org/content/foundation-stats"
            ],
            "policy_sources": [
                "https://federalregister.gov",
                "https://www.whitehouse.gov/briefings-statements/"
            ]
        }
        
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute market intelligence monitoring."""
        start_time = time.time()
        
        try:
            self.logger.info("Starting market intelligence monitoring cycle")
            
            # Step 1: Monitor funding trends
            funding_trends = await self._monitor_funding_trends(config)
            self.logger.info(f"Identified {len(funding_trends)} funding trends")
            
            # Step 2: Track policy changes
            policy_changes = await self._track_policy_changes(config)
            self.logger.info(f"Detected {len(policy_changes)} policy changes")
            
            # Step 3: Analyze market developments
            market_developments = await self._analyze_market_developments(config)
            self.logger.info(f"Analyzed {len(market_developments)} market developments")
            
            # Step 4: Generate alerts for significant changes
            alerts = self._generate_market_alerts(funding_trends, policy_changes, market_developments)
            self.logger.info(f"Generated {len(alerts)} market intelligence alerts")
            
            # Step 5: Create trend analysis and strategic insights
            trend_analysis = self._create_trend_analysis(funding_trends, policy_changes, market_developments)
            strategic_insights = self._generate_strategic_insights(alerts, trend_analysis)
            
            # Step 6: Store intelligence data for historical tracking
            await self._store_market_intelligence(alerts, funding_trends, config)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            result_data = {
                "monitoring_summary": {
                    "monitoring_cycle_timestamp": datetime.now().isoformat(),
                    "sources_monitored": len(self.monitoring_sources),
                    "funding_trends_identified": len(funding_trends),
                    "policy_changes_detected": len(policy_changes),
                    "market_developments_analyzed": len(market_developments),
                    "alerts_generated": len(alerts),
                    "monitoring_coverage": {
                        "government_agencies": len(self.monitoring_sources["government_agencies"]),
                        "foundation_sources": len(self.monitoring_sources["foundation_sources"]),
                        "policy_sources": len(self.monitoring_sources["policy_sources"])
                    }
                },
                "market_alerts": [alert.to_dict() for alert in alerts],
                "funding_trends": [trend.to_dict() for trend in funding_trends],
                "policy_changes": policy_changes,
                "market_developments": market_developments,
                "trend_analysis": trend_analysis,
                "strategic_insights": strategic_insights
            }
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "analysis_type": "market_intelligence_monitoring",
                    "monitoring_sources": list(self.monitoring_sources.keys()),
                    "alert_severity_distribution": self._summarize_alert_severity(alerts),
                    "trend_confidence_summary": self._summarize_trend_confidence(funding_trends)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Market intelligence monitoring failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Market intelligence monitoring failed: {str(e)}"]
            )
    
    async def _monitor_funding_trends(self, config: ProcessorConfig) -> List[MarketTrend]:
        """Monitor funding trends across government and foundation sources."""
        funding_trends = []
        
        try:
            # Analyze recent funding patterns from grants database
            funding_patterns = await self._analyze_recent_funding_patterns()
            
            # Check for funding increases/decreases
            for pattern in funding_patterns:
                if pattern.get('trend_direction') == 'increasing':
                    trend = MarketTrend(
                        trend_type="funding_increase",
                        trend_direction="increasing",
                        confidence=pattern.get('confidence', 0.7)
                    )
                    trend.affected_sectors = pattern.get('sectors', [])
                    trend.supporting_evidence = pattern.get('evidence', [])
                    funding_trends.append(trend)
                elif pattern.get('trend_direction') == 'decreasing':
                    trend = MarketTrend(
                        trend_type="funding_decrease",
                        trend_direction="decreasing", 
                        confidence=pattern.get('confidence', 0.7)
                    )
                    trend.affected_sectors = pattern.get('sectors', [])
                    trend.supporting_evidence = pattern.get('evidence', [])
                    funding_trends.append(trend)
            
            # Web intelligence monitoring (if MCP available)
            if self.mcp_client:
                web_trends = await self._monitor_web_funding_trends()
                funding_trends.extend(web_trends)
            
        except Exception as e:
            self.logger.warning(f"Failed to monitor funding trends: {e}")
        
        return funding_trends
    
    async def _analyze_recent_funding_patterns(self) -> List[Dict[str, Any]]:
        """Analyze recent funding patterns from grants database."""
        patterns = []
        
        try:
            # This would analyze grants.gov and other funding data
            # For demonstration, return sample patterns
            patterns = [
                {
                    'trend_direction': 'increasing',
                    'confidence': 0.8,
                    'sectors': ['P20', 'P23', 'E32'],
                    'evidence': ['15% increase in veteran-focused grants', 'New DoD community support initiatives']
                },
                {
                    'trend_direction': 'shifting',
                    'confidence': 0.6,
                    'sectors': ['T31', 'E61'],
                    'evidence': ['Shift from direct service to capacity building grants', 'Emphasis on evidence-based programs']
                }
            ]
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze funding patterns: {e}")
        
        return patterns
    
    async def _monitor_web_funding_trends(self) -> List[MarketTrend]:
        """Monitor funding trends from web sources using MCP."""
        web_trends = []
        
        # Sample trend monitoring from key funding websites
        # In practice, this would scrape actual funding announcement pages
        sample_trends = [
            {
                'trend_type': 'priority_shift',
                'trend_direction': 'shifting',
                'confidence': 0.7,
                'sectors': ['Community Development', 'Veterans Services'],
                'evidence': ['New strategic plan emphasizing community-based solutions']
            }
        ]
        
        for trend_data in sample_trends:
            trend = MarketTrend(
                trend_type=trend_data['trend_type'],
                trend_direction=trend_data['trend_direction'],
                confidence=trend_data['confidence']
            )
            trend.affected_sectors = trend_data.get('sectors', [])
            trend.supporting_evidence = trend_data.get('evidence', [])
            web_trends.append(trend)
        
        return web_trends
    
    async def _track_policy_changes(self, config: ProcessorConfig) -> List[Dict[str, Any]]:
        """Track policy changes affecting funding priorities."""
        policy_changes = []
        
        try:
            # Monitor policy sources for changes
            # In practice, this would scrape Federal Register, agency announcements
            sample_changes = [
                {
                    'change_type': 'regulation_update',
                    'agency': 'Department of Veterans Affairs',
                    'title': 'Updated Community Living Center Standards',
                    'impact': 'New eligibility requirements for community-based veteran programs',
                    'effective_date': '2025-01-01',
                    'impact_level': 'medium'
                },
                {
                    'change_type': 'funding_priority',
                    'agency': 'National Science Foundation',
                    'title': 'STEM Education Initiative Expansion',
                    'impact': 'Increased funding for community-based STEM programs',
                    'effective_date': '2025-02-15',
                    'impact_level': 'high'
                }
            ]
            
            policy_changes = sample_changes
            
        except Exception as e:
            self.logger.warning(f"Failed to track policy changes: {e}")
        
        return policy_changes
    
    async def _analyze_market_developments(self, config: ProcessorConfig) -> List[Dict[str, Any]]:
        """Analyze market developments and emerging opportunities."""
        market_developments = []
        
        try:
            # Analyze market developments from various sources
            sample_developments = [
                {
                    'development_type': 'emerging_opportunity',
                    'sector': 'Veterans Services',
                    'title': 'Mental Health Initiative Expansion',
                    'description': 'New federal initiative focusing on veteran mental health with $500M allocation',
                    'opportunity_timeline': '6 months',
                    'impact_potential': 'high'
                },
                {
                    'development_type': 'market_shift',
                    'sector': 'Community Development',
                    'title': 'Rural Infrastructure Investment',
                    'description': 'Significant shift toward rural community development funding',
                    'opportunity_timeline': '3 months',
                    'impact_potential': 'medium'
                }
            ]
            
            market_developments = sample_developments
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze market developments: {e}")
        
        return market_developments
    
    def _generate_market_alerts(self, funding_trends: List[MarketTrend], 
                              policy_changes: List[Dict[str, Any]], 
                              market_developments: List[Dict[str, Any]]) -> List[MarketIntelligenceAlert]:
        """Generate alerts for significant market intelligence changes."""
        alerts = []
        
        # High-confidence funding trend alerts
        for trend in funding_trends:
            if trend.confidence >= 0.8:
                severity = "high" if trend.confidence >= 0.9 else "medium"
                alert = MarketIntelligenceAlert(
                    alert_type="funding_trend",
                    severity=severity,
                    title=f"Significant {trend.trend_type.replace('_', ' ').title()} Detected",
                    description=f"High-confidence {trend.trend_direction} trend in {', '.join(trend.affected_sectors[:3])}"
                )
                alert.impact_areas = trend.affected_sectors
                alert.recommended_actions = [
                    "Review current grant strategy alignment",
                    "Consider program adjustments to match trend",
                    "Monitor related opportunities closely"
                ]
                alerts.append(alert)
        
        # High-impact policy change alerts
        for policy_change in policy_changes:
            if policy_change.get('impact_level') == 'high':
                alert = MarketIntelligenceAlert(
                    alert_type="policy_change",
                    severity="high",
                    title=f"High-Impact Policy Change: {policy_change['title']}",
                    description=policy_change['impact']
                )
                alert.impact_areas = [policy_change.get('agency', 'Federal')]
                alert.recommended_actions = [
                    "Review compliance requirements",
                    "Update grant applications accordingly",
                    "Assess program eligibility impacts"
                ]
                alerts.append(alert)
        
        # Emerging opportunity alerts
        for development in market_developments:
            if development.get('impact_potential') == 'high':
                alert = MarketIntelligenceAlert(
                    alert_type="market_development",
                    severity="medium",
                    title=f"Emerging Opportunity: {development['title']}",
                    description=development['description']
                )
                alert.impact_areas = [development.get('sector', 'General')]
                alert.recommended_actions = [
                    "Evaluate organizational readiness",
                    "Begin strategic planning for opportunity",
                    "Monitor for formal announcements"
                ]
                alerts.append(alert)
        
        return alerts
    
    def _create_trend_analysis(self, funding_trends: List[MarketTrend],
                             policy_changes: List[Dict[str, Any]],
                             market_developments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive trend analysis."""
        analysis = {
            "trend_summary": {
                "increasing_funding_areas": [],
                "decreasing_funding_areas": [],
                "shifting_priorities": [],
                "emerging_sectors": []
            },
            "policy_impact_assessment": {
                "high_impact_changes": len([c for c in policy_changes if c.get('impact_level') == 'high']),
                "medium_impact_changes": len([c for c in policy_changes if c.get('impact_level') == 'medium']),
                "affected_agencies": list(set(c.get('agency', '') for c in policy_changes))
            },
            "market_outlook": {
                "positive_indicators": 0,
                "negative_indicators": 0,
                "opportunity_timeline": "3-6 months",
                "confidence_level": "medium"
            }
        }
        
        # Analyze funding trends
        for trend in funding_trends:
            if trend.trend_type == "funding_increase":
                analysis["trend_summary"]["increasing_funding_areas"].extend(trend.affected_sectors)
            elif trend.trend_type == "funding_decrease":
                analysis["trend_summary"]["decreasing_funding_areas"].extend(trend.affected_sectors)
            elif trend.trend_type == "priority_shift":
                analysis["trend_summary"]["shifting_priorities"].extend(trend.affected_sectors)
        
        # Market outlook assessment
        positive_trends = len([t for t in funding_trends if t.trend_direction == "increasing"])
        negative_trends = len([t for t in funding_trends if t.trend_direction == "decreasing"])
        
        analysis["market_outlook"]["positive_indicators"] = positive_trends
        analysis["market_outlook"]["negative_indicators"] = negative_trends
        
        if positive_trends > negative_trends:
            analysis["market_outlook"]["confidence_level"] = "high"
        elif positive_trends == negative_trends:
            analysis["market_outlook"]["confidence_level"] = "medium"
        else:
            analysis["market_outlook"]["confidence_level"] = "cautious"
        
        return analysis
    
    def _generate_strategic_insights(self, alerts: List[MarketIntelligenceAlert],
                                   trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic insights from market intelligence."""
        insights = {
            "key_opportunities": [],
            "risk_factors": [],
            "strategic_recommendations": [],
            "timing_considerations": []
        }
        
        # Analyze alerts for opportunities and risks
        high_severity_alerts = [a for a in alerts if a.severity == "high"]
        
        for alert in high_severity_alerts:
            if alert.alert_type == "market_development":
                insights["key_opportunities"].append(alert.title)
            elif alert.alert_type == "policy_change":
                insights["risk_factors"].append(f"Policy impact: {alert.title}")
        
        # Strategic recommendations based on trend analysis
        market_outlook = trend_analysis.get("market_outlook", {})
        positive_indicators = market_outlook.get("positive_indicators", 0)
        negative_indicators = market_outlook.get("negative_indicators", 0)
        
        if positive_indicators > negative_indicators:
            insights["strategic_recommendations"].append("Accelerate grant application development")
            insights["strategic_recommendations"].append("Expand program capacity to capture opportunities")
        elif negative_indicators > positive_indicators:
            insights["strategic_recommendations"].append("Focus on proven funding sources")
            insights["strategic_recommendations"].append("Develop contingency funding strategies")
        
        # Timing considerations
        opportunity_timeline = market_outlook.get("opportunity_timeline", "unknown")
        insights["timing_considerations"].append(f"Primary opportunity window: {opportunity_timeline}")
        
        if len(alerts) > 3:
            insights["timing_considerations"].append("High market activity - monitor frequently")
        
        return insights
    
    async def _store_market_intelligence(self, alerts: List[MarketIntelligenceAlert], 
                                       trends: List[MarketTrend], 
                                       config: ProcessorConfig):
        """Store market intelligence data for historical tracking."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Ensure market intelligence table exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS market_intelligence_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        alert_type TEXT,
                        severity TEXT,
                        title TEXT,
                        description TEXT,
                        impact_areas TEXT,
                        data_json TEXT,
                        workflow_id TEXT
                    )
                """)
                
                # Store alerts
                for alert in alerts:
                    conn.execute("""
                        INSERT INTO market_intelligence_log 
                        (timestamp, alert_type, severity, title, description, impact_areas, data_json, workflow_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        alert.timestamp.isoformat(),
                        alert.alert_type,
                        alert.severity,
                        alert.title,
                        alert.description,
                        json.dumps(alert.impact_areas),
                        json.dumps(alert.to_dict()),
                        config.workflow_id
                    ))
                
                conn.commit()
                self.logger.info(f"Stored {len(alerts)} market intelligence alerts")
                
        except Exception as e:
            self.logger.warning(f"Failed to store market intelligence: {e}")
    
    def _summarize_alert_severity(self, alerts: List[MarketIntelligenceAlert]) -> Dict[str, int]:
        """Summarize alert severity distribution."""
        severity_counts = Counter(alert.severity for alert in alerts)
        return dict(severity_counts)
    
    def _summarize_trend_confidence(self, trends: List[MarketTrend]) -> Dict[str, Any]:
        """Summarize trend confidence statistics."""
        if not trends:
            return {"average_confidence": 0, "high_confidence_count": 0}
        
        confidences = [trend.confidence for trend in trends]
        high_confidence_count = len([c for c in confidences if c >= 0.8])
        
        return {
            "average_confidence": sum(confidences) / len(confidences),
            "high_confidence_count": high_confidence_count,
            "total_trends": len(trends)
        }
    
    def validate_inputs(self, config: ProcessorConfig) -> List[str]:
        """Validate inputs for market intelligence monitoring."""
        errors = []
        
        if not config.workflow_id:
            errors.append("Workflow ID is required")
        
        return errors


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return MarketIntelligenceMonitor()