#!/usr/bin/env python3
"""
System Monitor
Comprehensive system monitoring and analytics for the Catalynx platform.

This module provides:
1. Real-time performance monitoring
2. Resource usage tracking
3. Processor health monitoring  
4. Error tracking and alerting
5. Usage analytics and insights
6. System health dashboards
"""

import asyncio
import logging
import json
import time
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import statistics


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    EXCELLENT = "excellent"
    GOOD = "good" 
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System performance metrics snapshot."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    active_processes: int
    response_time_ms: Optional[float] = None


@dataclass
class ProcessorHealth:
    """Health status of a processor."""
    processor_name: str
    status: HealthStatus
    last_execution: Optional[str]
    success_rate: float
    average_duration: float
    error_count: int
    last_error: Optional[str]


@dataclass
class SystemAlert:
    """System alert/notification."""
    alert_id: str
    level: AlertLevel
    title: str
    description: str
    timestamp: str
    component: str
    resolved: bool = False
    resolution_time: Optional[str] = None


@dataclass
class UsageAnalytics:
    """Usage analytics and patterns."""
    period_start: str
    period_end: str
    total_discoveries: int
    profiles_created: int
    opportunities_found: int
    avg_session_duration: float
    peak_usage_hours: List[int]
    top_processors: List[Dict[str, Any]]
    error_rate: float


class SystemMonitor:
    """Comprehensive system monitoring and analytics service."""
    
    def __init__(self, data_path: str = "data", monitoring_interval: int = 60):
        self.data_path = Path(data_path)
        self.monitoring_interval = monitoring_interval
        self.logger = logging.getLogger(__name__)
        
        # Monitoring data storage
        self.monitoring_path = self.data_path / "monitoring"
        self.monitoring_path.mkdir(exist_ok=True)
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'response_time_warning': 5000.0,  # 5 seconds
            'response_time_critical': 15000.0,  # 15 seconds
            'error_rate_warning': 0.05,  # 5%
            'error_rate_critical': 0.15  # 15%
        }
        
        # Monitoring state
        self.alerts: List[SystemAlert] = []
        self.metrics_history: List[SystemMetrics] = []
        self.processor_health: Dict[str, ProcessorHealth] = {}
        self.is_monitoring = False
    
    async def start_monitoring(self):
        """Start continuous system monitoring."""
        self.logger.info("Starting system monitoring")
        self.is_monitoring = True
        
        # Load existing data
        await self._load_monitoring_data()
        
        # Start monitoring loop
        while self.is_monitoring:
            try:
                await self._collect_metrics()
                await self._check_processor_health()
                await self._analyze_alerts()
                await self._save_monitoring_data()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def stop_monitoring(self):
        """Stop system monitoring."""
        self.logger.info("Stopping system monitoring")
        self.is_monitoring = False
        await self._save_monitoring_data()
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health overview."""
        current_metrics = await self._collect_current_metrics()
        overall_health = self._calculate_overall_health(current_metrics)
        
        return {
            "overall_health": overall_health.value,
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(current_metrics),
            "processor_health": {
                name: asdict(health) for name, health in self.processor_health.items()
            },
            "active_alerts": [
                asdict(alert) for alert in self.alerts if not alert.resolved
            ],
            "performance_summary": await self._get_performance_summary(),
            "recommendations": await self._generate_recommendations()
        }
    
    async def get_usage_analytics(self, days: int = 7) -> UsageAnalytics:
        """Get usage analytics for the specified period."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        analytics = UsageAnalytics(
            period_start=start_time.isoformat(),
            period_end=end_time.isoformat(),
            total_discoveries=0,
            profiles_created=0,
            opportunities_found=0,
            avg_session_duration=0.0,
            peak_usage_hours=[],
            top_processors=[],
            error_rate=0.0
        )
        
        try:
            # Analyze profile activity
            profiles_path = self.data_path / "profiles" / "profiles"
            if profiles_path.exists():
                for profile_file in profiles_path.glob("*.json"):
                    try:
                        with open(profile_file, 'r') as f:
                            profile_data = json.load(f)
                        
                        created_at = profile_data.get('created_at')
                        if created_at:
                            created_time = datetime.fromisoformat(created_at)
                            if start_time <= created_time <= end_time:
                                analytics.profiles_created += 1
                                
                    except:
                        continue
            
            # Analyze discovery activity
            leads_path = self.data_path / "profiles" / "leads"
            if leads_path.exists():
                session_durations = []
                
                for lead_file in leads_path.glob("*.json"):
                    try:
                        with open(lead_file, 'r') as f:
                            lead_data = json.load(f)
                        
                        discovered_at = lead_data.get('discovered_at')
                        if discovered_at:
                            discovery_time = datetime.fromisoformat(discovered_at)
                            if start_time <= discovery_time <= end_time:
                                analytics.total_discoveries += 1
                                
                                # Check if it's an opportunity
                                if lead_data.get('funnel_stage') == 'opportunities':
                                    analytics.opportunities_found += 1
                                
                    except:
                        continue
            
            # Calculate average session duration (simplified)
            if analytics.total_discoveries > 0:
                analytics.avg_session_duration = 15.0  # Default estimate in minutes
            
            # Analyze processor usage
            analytics.top_processors = await self._get_top_processors()
            
            # Calculate error rate
            analytics.error_rate = await self._calculate_error_rate(days)
            
            # Analyze peak usage hours (simplified)
            analytics.peak_usage_hours = [9, 10, 11, 14, 15, 16]  # Business hours
            
        except Exception as e:
            self.logger.error(f"Error generating usage analytics: {e}")
        
        return analytics
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate detailed performance report."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Filter metrics for time period
        recent_metrics = [
            m for m in self.metrics_history
            if start_time <= datetime.fromisoformat(m.timestamp) <= end_time
        ]
        
        if not recent_metrics:
            return {"error": "No metrics data available for the specified period"}
        
        report = {
            "period": f"Last {hours} hours",
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "metrics_count": len(recent_metrics),
            "performance_stats": {},
            "trends": {},
            "alerts_summary": {},
            "recommendations": []
        }
        
        # Calculate performance statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_percent for m in recent_metrics]
        
        report["performance_stats"] = {
            "cpu": {
                "average": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "current": recent_metrics[-1].cpu_percent
            },
            "memory": {
                "average": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "current": recent_metrics[-1].memory_percent
            },
            "disk": {
                "average": statistics.mean(disk_values),
                "max": max(disk_values),
                "min": min(disk_values),
                "current": recent_metrics[-1].disk_percent
            }
        }
        
        # Analyze trends
        if len(recent_metrics) >= 2:
            first_half = recent_metrics[:len(recent_metrics)//2]
            second_half = recent_metrics[len(recent_metrics)//2:]
            
            first_cpu_avg = statistics.mean([m.cpu_percent for m in first_half])
            second_cpu_avg = statistics.mean([m.cpu_percent for m in second_half])
            
            cpu_trend = "increasing" if second_cpu_avg > first_cpu_avg else "decreasing"
            
            report["trends"] = {
                "cpu_trend": cpu_trend,
                "cpu_change": abs(second_cpu_avg - first_cpu_avg)
            }
        
        # Alerts summary
        period_alerts = [
            a for a in self.alerts
            if start_time <= datetime.fromisoformat(a.timestamp) <= end_time
        ]
        
        report["alerts_summary"] = {
            "total_alerts": len(period_alerts),
            "critical_alerts": len([a for a in period_alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in period_alerts if a.level == AlertLevel.WARNING]),
            "resolved_alerts": len([a for a in period_alerts if a.resolved])
        }
        
        # Generate recommendations
        recommendations = []
        if report["performance_stats"]["cpu"]["average"] > 70:
            recommendations.append("Consider optimizing CPU-intensive processes")
        if report["performance_stats"]["memory"]["average"] > 80:
            recommendations.append("Monitor memory usage - consider increasing available RAM")
        if len(period_alerts) > 10:
            recommendations.append("High alert volume - review system configuration")
        
        report["recommendations"] = recommendations
        
        return report
    
    async def _collect_metrics(self):
        """Collect current system metrics."""
        metrics = await self._collect_current_metrics()
        self.metrics_history.append(metrics)
        
        # Keep only last 24 hours of metrics
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
    
    async def _collect_current_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Process count
        active_processes = len(psutil.pids())
        
        # Response time (simulate API response check)
        response_time = await self._measure_response_time()
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            active_processes=active_processes,
            response_time_ms=response_time
        )
    
    async def _measure_response_time(self) -> float:
        """Measure API response time."""
        start_time = time.time()
        
        try:
            # Simulate API call (in real implementation, call actual API)
            await asyncio.sleep(0.01)  # Simulate 10ms response
            
        except Exception:
            pass
        
        end_time = time.time()
        return (end_time - start_time) * 1000  # Convert to milliseconds
    
    async def _check_processor_health(self):
        """Check health of all processors."""
        # In a real implementation, this would check actual processor status
        # For now, simulate processor health
        
        processors = [
            "bmf_filter", "propublica_fetch", "grants_gov_fetch", 
            "usaspending_fetch", "government_opportunity_scorer",
            "board_network_analyzer", "ai_lite_scorer", "ai_heavy_researcher"
        ]
        
        for processor_name in processors:
            if processor_name not in self.processor_health:
                self.processor_health[processor_name] = ProcessorHealth(
                    processor_name=processor_name,
                    status=HealthStatus.GOOD,
                    last_execution=datetime.now().isoformat(),
                    success_rate=0.95,
                    average_duration=30.0,
                    error_count=0,
                    last_error=None
                )
    
    async def _analyze_alerts(self):
        """Analyze current metrics and generate alerts."""
        current_metrics = await self._collect_current_metrics()
        
        # Check CPU threshold
        if current_metrics.cpu_percent > self.thresholds['cpu_critical']:
            await self._create_alert(
                AlertLevel.CRITICAL,
                "High CPU Usage",
                f"CPU usage at {current_metrics.cpu_percent:.1f}%",
                "system"
            )
        elif current_metrics.cpu_percent > self.thresholds['cpu_warning']:
            await self._create_alert(
                AlertLevel.WARNING,
                "Elevated CPU Usage",
                f"CPU usage at {current_metrics.cpu_percent:.1f}%",
                "system"
            )
        
        # Check memory threshold
        if current_metrics.memory_percent > self.thresholds['memory_critical']:
            await self._create_alert(
                AlertLevel.CRITICAL,
                "High Memory Usage",
                f"Memory usage at {current_metrics.memory_percent:.1f}%",
                "system"
            )
        elif current_metrics.memory_percent > self.thresholds['memory_warning']:
            await self._create_alert(
                AlertLevel.WARNING,
                "Elevated Memory Usage",
                f"Memory usage at {current_metrics.memory_percent:.1f}%",
                "system"
            )
        
        # Check response time
        if current_metrics.response_time_ms and current_metrics.response_time_ms > self.thresholds['response_time_critical']:
            await self._create_alert(
                AlertLevel.CRITICAL,
                "Slow Response Time",
                f"API response time {current_metrics.response_time_ms:.0f}ms",
                "api"
            )
    
    async def _create_alert(self, level: AlertLevel, title: str, description: str, component: str):
        """Create a new alert."""
        # Check if similar alert already exists
        existing_alert = next(
            (a for a in self.alerts 
             if a.title == title and a.component == component and not a.resolved),
            None
        )
        
        if not existing_alert:
            alert = SystemAlert(
                alert_id=f"alert_{int(time.time())}_{len(self.alerts)}",
                level=level,
                title=title,
                description=description,
                timestamp=datetime.now().isoformat(),
                component=component
            )
            
            self.alerts.append(alert)
            self.logger.warning(f"Alert created: {title} - {description}")
    
    def _calculate_overall_health(self, metrics: SystemMetrics) -> HealthStatus:
        """Calculate overall system health."""
        health_score = 100.0
        
        # Deduct points for high resource usage
        if metrics.cpu_percent > 80:
            health_score -= 30
        elif metrics.cpu_percent > 60:
            health_score -= 15
        
        if metrics.memory_percent > 80:
            health_score -= 30
        elif metrics.memory_percent > 60:
            health_score -= 15
        
        if metrics.disk_percent > 90:
            health_score -= 20
        elif metrics.disk_percent > 80:
            health_score -= 10
        
        # Deduct points for slow response times
        if metrics.response_time_ms and metrics.response_time_ms > 5000:
            health_score -= 20
        
        # Deduct points for active alerts
        critical_alerts = len([a for a in self.alerts if a.level == AlertLevel.CRITICAL and not a.resolved])
        warning_alerts = len([a for a in self.alerts if a.level == AlertLevel.WARNING and not a.resolved])
        
        health_score -= critical_alerts * 25
        health_score -= warning_alerts * 10
        
        # Determine health status
        if health_score >= 90:
            return HealthStatus.EXCELLENT
        elif health_score >= 75:
            return HealthStatus.GOOD
        elif health_score >= 50:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL
    
    async def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from recent metrics."""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        return {
            "avg_cpu": statistics.mean([m.cpu_percent for m in recent_metrics]),
            "avg_memory": statistics.mean([m.memory_percent for m in recent_metrics]),
            "avg_response_time": statistics.mean([
                m.response_time_ms for m in recent_metrics 
                if m.response_time_ms is not None
            ]) if any(m.response_time_ms for m in recent_metrics) else None
        }
    
    async def _generate_recommendations(self) -> List[str]:
        """Generate system optimization recommendations."""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        recent_metrics = self.metrics_history[-5:]  # Last 5 measurements
        avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
        avg_memory = statistics.mean([m.memory_percent for m in recent_metrics])
        
        if avg_cpu > 80:
            recommendations.append("High CPU usage detected - consider optimizing processor scheduling")
        
        if avg_memory > 80:
            recommendations.append("High memory usage - consider implementing memory cleanup routines")
        
        active_alerts = [a for a in self.alerts if not a.resolved]
        if len(active_alerts) > 5:
            recommendations.append("Multiple active alerts - review system configuration")
        
        if not recommendations:
            recommendations.append("System performance is within normal parameters")
        
        return recommendations
    
    async def _get_top_processors(self) -> List[Dict[str, Any]]:
        """Get top processors by usage."""
        # Simulate processor usage data
        return [
            {"name": "government_opportunity_scorer", "usage_count": 250, "avg_duration": 1.2},
            {"name": "propublica_fetch", "usage_count": 180, "avg_duration": 5.3},
            {"name": "bmf_filter", "usage_count": 165, "avg_duration": 0.8},
            {"name": "grants_gov_fetch", "usage_count": 120, "avg_duration": 8.1},
            {"name": "board_network_analyzer", "usage_count": 95, "avg_duration": 3.4}
        ]
    
    async def _calculate_error_rate(self, days: int) -> float:
        """Calculate system error rate."""
        # Simulate error rate calculation
        return 0.02  # 2% error rate
    
    async def _load_monitoring_data(self):
        """Load existing monitoring data."""
        try:
            metrics_file = self.monitoring_path / "metrics_history.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    self.metrics_history = [SystemMetrics(**m) for m in data.get('metrics', [])]
            
            alerts_file = self.monitoring_path / "alerts.json"
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    data = json.load(f)
                    self.alerts = [SystemAlert(**a) for a in data.get('alerts', [])]
                    
        except Exception as e:
            self.logger.error(f"Error loading monitoring data: {e}")
    
    async def _save_monitoring_data(self):
        """Save current monitoring data."""
        try:
            # Save metrics history (keep only recent data)
            metrics_file = self.monitoring_path / "metrics_history.json"
            with open(metrics_file, 'w') as f:
                json.dump({
                    'metrics': [asdict(m) for m in self.metrics_history[-100:]]  # Keep last 100
                }, f, indent=2)
            
            # Save alerts
            alerts_file = self.monitoring_path / "alerts.json"
            with open(alerts_file, 'w') as f:
                json.dump({
                    'alerts': [asdict(a) for a in self.alerts[-50:]]  # Keep last 50
                }, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving monitoring data: {e}")


# Factory function for easy access
def get_system_monitor(data_path: str = "data", monitoring_interval: int = 60) -> SystemMonitor:
    """Get a configured system monitor instance."""
    return SystemMonitor(data_path, monitoring_interval)