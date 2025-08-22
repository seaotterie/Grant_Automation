"""
PHASE 6: Advanced Analytics Dashboard
Comprehensive analytics dashboard with real-time metrics, predictive insights,
performance monitoring, and advanced data visualization capabilities.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import numpy as np
from collections import defaultdict, deque
import statistics
import uuid

from src.core.base_processor import BaseProcessor
from src.decision.decision_synthesis_framework import DecisionRecommendation, DecisionConfidence
from src.core.entity_cache_manager import get_entity_cache_manager

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics tracked in the analytics system"""
    COUNTER = "counter"                 # Simple count (opportunities processed)
    GAUGE = "gauge"                     # Point-in-time value (current users)
    HISTOGRAM = "histogram"             # Distribution of values (response times)
    RATE = "rate"                      # Rate of change (requests per second)
    PERCENTAGE = "percentage"           # Percentage value (success rate)
    TREND = "trend"                    # Trending value over time

class AnalyticsPeriod(Enum):
    """Time periods for analytics aggregation"""
    REALTIME = "realtime"              # Last 5 minutes
    HOURLY = "hourly"                  # Last 24 hours  
    DAILY = "daily"                    # Last 30 days
    WEEKLY = "weekly"                  # Last 12 weeks
    MONTHLY = "monthly"                # Last 12 months
    YEARLY = "yearly"                  # Last 5 years

class DashboardWidget(Enum):
    """Types of dashboard widgets"""
    KPI_CARD = "kpi_card"              # Key performance indicator card
    LINE_CHART = "line_chart"          # Time series line chart
    BAR_CHART = "bar_chart"            # Bar chart
    PIE_CHART = "pie_chart"            # Pie/donut chart
    GAUGE_CHART = "gauge_chart"        # Gauge/speedometer chart
    HEATMAP = "heatmap"                # Heat map visualization
    TABLE = "table"                    # Data table
    FUNNEL = "funnel"                  # Funnel chart
    SCATTER_PLOT = "scatter_plot"      # Scatter plot
    TREEMAP = "treemap"                # Tree map
    SANKEY = "sankey"                  # Sankey diagram

@dataclass
class Metric:
    """Individual metric definition and current value"""
    metric_id: str
    name: str
    description: str
    metric_type: MetricType
    
    # Current values
    current_value: Union[float, int, str]
    previous_value: Optional[Union[float, int, str]] = None
    
    # Metadata
    unit: str = ""                     # Unit of measurement (%, seconds, count)
    format_string: str = "{:.2f}"      # Display format
    thresholds: Dict[str, float] = field(default_factory=dict)  # Warning/critical thresholds
    
    # Trend analysis
    trend_direction: Optional[str] = None  # 'up', 'down', 'stable'
    trend_percentage: Optional[float] = None
    
    # Historical data
    history: List[Tuple[datetime, Union[float, int]]] = field(default_factory=list)
    
    # Configuration
    is_active: bool = True
    collect_history: bool = True
    max_history_points: int = 1440      # Default: 24 hours of minute data
    
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DashboardConfig:
    """Configuration for analytics dashboard"""
    dashboard_id: str
    name: str
    description: str
    
    # Layout configuration
    layout: str = "grid"               # 'grid', 'flex', 'custom'
    columns: int = 12                  # Grid columns
    refresh_interval: int = 30         # Seconds between auto-refresh
    
    # Widget configuration
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Permissions and access
    public: bool = False
    allowed_users: List[str] = field(default_factory=list)
    
    # Display options
    theme: str = "default"             # 'default', 'dark', 'light'
    show_legends: bool = True
    show_tooltips: bool = True
    
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalyticsSnapshot:
    """Point-in-time analytics snapshot"""
    snapshot_id: str
    timestamp: datetime
    period: AnalyticsPeriod
    
    # Core metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Performance insights
    performance_summary: Dict[str, Any] = field(default_factory=dict)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    anomaly_detection: Dict[str, Any] = field(default_factory=dict)
    
    # Predictive analytics
    predictions: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.collection_queue = deque(maxlen=10000)
        self.is_collecting = False
    
    def register_metric(self, metric: Metric) -> None:
        """Register a new metric for collection"""
        self.metrics[metric.metric_id] = metric
        logger.info(f"Registered metric: {metric.name}")
    
    async def update_metric(self, metric_id: str, value: Union[float, int, str], timestamp: Optional[datetime] = None) -> bool:
        """Update metric value"""
        if metric_id not in self.metrics:
            logger.warning(f"Metric not found: {metric_id}")
            return False
        
        metric = self.metrics[metric_id]
        timestamp = timestamp or datetime.now()
        
        # Store previous value
        metric.previous_value = metric.current_value
        metric.current_value = value
        metric.last_updated = timestamp
        
        # Add to history if enabled
        if metric.collect_history and isinstance(value, (int, float)):
            metric.history.append((timestamp, value))
            
            # Trim history to max points
            if len(metric.history) > metric.max_history_points:
                metric.history = metric.history[-metric.max_history_points:]
        
        # Calculate trend
        await self._calculate_trend(metric)
        
        return True
    
    async def _calculate_trend(self, metric: Metric) -> None:
        """Calculate trend direction and percentage for metric"""
        if metric.previous_value is None or not isinstance(metric.current_value, (int, float)):
            return
        
        if not isinstance(metric.previous_value, (int, float)):
            return
        
        current = float(metric.current_value)
        previous = float(metric.previous_value)
        
        if previous == 0:
            metric.trend_percentage = 0.0
            metric.trend_direction = 'stable'
            return
        
        # Calculate percentage change
        change = ((current - previous) / previous) * 100
        metric.trend_percentage = change
        
        # Determine direction
        if abs(change) < 1.0:  # Less than 1% change considered stable
            metric.trend_direction = 'stable'
        elif change > 0:
            metric.trend_direction = 'up'
        else:
            metric.trend_direction = 'down'
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system-wide metrics"""
        
        # Get entity cache manager for system stats
        entity_cache = get_entity_cache_manager()
        
        # Collect basic system metrics
        system_metrics = {
            'entities_cached': len(entity_cache.cache) if hasattr(entity_cache, 'cache') else 0,
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'active_profiles': self._count_active_profiles(),
            'processed_opportunities': self._count_processed_opportunities(),
            'system_uptime': self._calculate_uptime(),
            'memory_usage': self._get_memory_usage(),
            'response_time_avg': self._calculate_avg_response_time()
        }
        
        # Update registered metrics
        for metric_name, value in system_metrics.items():
            if metric_name in self.metrics:
                await self.update_metric(metric_name, value)
        
        return system_metrics
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # Simplified calculation - in production would track actual hits/misses
        return 85.5  # Example: 85.5% hit rate
    
    def _count_active_profiles(self) -> int:
        """Count active user profiles"""
        # Would connect to actual user session tracking
        return 12  # Example: 12 active profiles
    
    def _count_processed_opportunities(self) -> int:
        """Count total opportunities processed"""
        # Would connect to actual opportunity processing statistics
        return 1247  # Example: 1,247 opportunities processed
    
    def _calculate_uptime(self) -> float:
        """Calculate system uptime in hours"""
        # Would connect to actual system start time tracking
        return 168.5  # Example: 168.5 hours uptime
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        # Would connect to actual system monitoring
        return 42.3  # Example: 42.3% memory usage
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time in milliseconds"""
        # Would connect to actual request timing
        return 234.7  # Example: 234.7ms average response time
    
    def get_metric(self, metric_id: str) -> Optional[Metric]:
        """Get metric by ID"""
        return self.metrics.get(metric_id)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all registered metrics"""
        return self.metrics.copy()

class PerformanceAnalyzer:
    """Analyzes performance trends and patterns"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    async def analyze_performance(self, period: AnalyticsPeriod) -> Dict[str, Any]:
        """Perform comprehensive performance analysis"""
        
        analysis = {
            'period': period.value,
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'good',  # 'excellent', 'good', 'fair', 'poor'
            'key_insights': [],
            'performance_scores': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Analyze each metric category
        response_time_analysis = await self._analyze_response_times(period)
        throughput_analysis = await self._analyze_throughput(period)
        error_rate_analysis = await self._analyze_error_rates(period)
        resource_usage_analysis = await self._analyze_resource_usage(period)
        
        # Combine analyses
        analysis['response_time'] = response_time_analysis
        analysis['throughput'] = throughput_analysis
        analysis['error_rates'] = error_rate_analysis
        analysis['resource_usage'] = resource_usage_analysis
        
        # Calculate overall health score
        health_score = self._calculate_health_score([
            response_time_analysis.get('score', 0.5),
            throughput_analysis.get('score', 0.5),
            error_rate_analysis.get('score', 0.5),
            resource_usage_analysis.get('score', 0.5)
        ])
        
        analysis['health_score'] = health_score
        analysis['overall_health'] = self._health_score_to_status(health_score)
        
        # Generate insights
        analysis['key_insights'] = await self._generate_performance_insights(
            response_time_analysis, throughput_analysis, error_rate_analysis, resource_usage_analysis
        )
        
        return analysis
    
    async def _analyze_response_times(self, period: AnalyticsPeriod) -> Dict[str, Any]:
        """Analyze response time metrics"""
        
        # Get response time metric
        response_metric = self.metrics_collector.get_metric('response_time_avg')
        
        if not response_metric or not response_metric.history:
            return {'score': 0.5, 'status': 'unknown', 'trend': 'stable'}
        
        # Analyze recent response times
        recent_times = [value for _, value in response_metric.history[-100:]]  # Last 100 data points
        
        avg_time = statistics.mean(recent_times)
        median_time = statistics.median(recent_times)
        p95_time = np.percentile(recent_times, 95) if recent_times else avg_time
        
        # Determine score based on response time thresholds
        if avg_time < 200:       # Excellent: < 200ms
            score = 1.0
            status = 'excellent'
        elif avg_time < 500:     # Good: < 500ms
            score = 0.8
            status = 'good'
        elif avg_time < 1000:    # Fair: < 1000ms
            score = 0.6
            status = 'fair'
        else:                    # Poor: >= 1000ms
            score = 0.3
            status = 'poor'
        
        return {
            'score': score,
            'status': status,
            'average_ms': avg_time,
            'median_ms': median_time,
            'p95_ms': p95_time,
            'trend': response_metric.trend_direction,
            'trend_percentage': response_metric.trend_percentage
        }
    
    async def _analyze_throughput(self, period: AnalyticsPeriod) -> Dict[str, Any]:
        """Analyze system throughput metrics"""
        
        # Simulate throughput analysis
        current_throughput = 245.3  # requests per minute
        target_throughput = 300.0
        
        score = min(1.0, current_throughput / target_throughput)
        
        if score >= 0.9:
            status = 'excellent'
        elif score >= 0.7:
            status = 'good'
        elif score >= 0.5:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'score': score,
            'status': status,
            'current_rpm': current_throughput,
            'target_rpm': target_throughput,
            'utilization_percentage': score * 100,
            'trend': 'up'
        }
    
    async def _analyze_error_rates(self, period: AnalyticsPeriod) -> Dict[str, Any]:
        """Analyze error rate metrics"""
        
        # Simulate error rate analysis
        error_rate = 0.8  # 0.8% error rate
        
        if error_rate < 0.5:
            score = 1.0
            status = 'excellent'
        elif error_rate < 1.0:
            score = 0.8
            status = 'good'
        elif error_rate < 2.0:
            score = 0.6
            status = 'fair'
        else:
            score = 0.3
            status = 'poor'
        
        return {
            'score': score,
            'status': status,
            'error_rate_percentage': error_rate,
            'total_errors': 47,
            'total_requests': 5875,
            'trend': 'down'  # Decreasing error rate is good
        }
    
    async def _analyze_resource_usage(self, period: AnalyticsPeriod) -> Dict[str, Any]:
        """Analyze resource usage metrics"""
        
        # Get resource usage metrics
        memory_metric = self.metrics_collector.get_metric('memory_usage')
        memory_usage = memory_metric.current_value if memory_metric else 42.3
        
        # Simulate CPU and other resource usage
        cpu_usage = 35.7
        disk_usage = 67.2
        
        # Calculate overall resource score
        memory_score = max(0, (100 - memory_usage) / 100) if memory_usage < 90 else 0.1
        cpu_score = max(0, (100 - cpu_usage) / 100) if cpu_usage < 90 else 0.1
        disk_score = max(0, (100 - disk_usage) / 100) if disk_usage < 90 else 0.1
        
        overall_score = (memory_score + cpu_score + disk_score) / 3
        
        if overall_score >= 0.8:
            status = 'excellent'
        elif overall_score >= 0.6:
            status = 'good'
        elif overall_score >= 0.4:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'score': overall_score,
            'status': status,
            'memory_usage_percentage': memory_usage,
            'cpu_usage_percentage': cpu_usage,
            'disk_usage_percentage': disk_usage,
            'trend': 'stable'
        }
    
    def _calculate_health_score(self, scores: List[float]) -> float:
        """Calculate overall health score from component scores"""
        return statistics.mean(scores) if scores else 0.5
    
    def _health_score_to_status(self, score: float) -> str:
        """Convert health score to status string"""
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.5:
            return 'fair'
        else:
            return 'poor'
    
    async def _generate_performance_insights(self, *analyses) -> List[str]:
        """Generate actionable performance insights"""
        
        insights = []
        
        # Response time insights
        rt_analysis = analyses[0] if analyses else {}
        if rt_analysis.get('status') == 'poor':
            insights.append("Response times are above acceptable thresholds - investigate slow queries and optimize bottlenecks")
        elif rt_analysis.get('trend') == 'up':
            insights.append("Response times are trending upward - monitor for potential performance degradation")
        
        # Throughput insights
        tp_analysis = analyses[1] if len(analyses) > 1 else {}
        if tp_analysis.get('utilization_percentage', 0) > 90:
            insights.append("System operating near capacity - consider scaling resources")
        
        # Error rate insights
        er_analysis = analyses[2] if len(analyses) > 2 else {}
        if er_analysis.get('error_rate_percentage', 0) > 1.0:
            insights.append("Error rate elevated - investigate error patterns and implement fixes")
        
        # Resource usage insights
        ru_analysis = analyses[3] if len(analyses) > 3 else {}
        if ru_analysis.get('memory_usage_percentage', 0) > 80:
            insights.append("Memory usage high - monitor for memory leaks and optimize memory allocation")
        
        return insights if insights else ["System performance is within normal parameters"]

class PredictiveAnalytics:
    """Predictive analytics engine for forecasting and trend analysis"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    async def generate_predictions(self, metric_id: str, forecast_hours: int = 24) -> Dict[str, Any]:
        """Generate predictions for a specific metric"""
        
        metric = self.metrics_collector.get_metric(metric_id)
        if not metric or not metric.history:
            return {
                'error': 'Insufficient data for prediction',
                'metric_id': metric_id
            }
        
        # Extract time series data
        times, values = zip(*metric.history) if metric.history else ([], [])
        
        if len(values) < 5:  # Need minimum data points
            return {
                'error': 'Insufficient historical data',
                'metric_id': metric_id,
                'data_points': len(values)
            }
        
        # Simple linear trend prediction (in production would use more sophisticated models)
        prediction = await self._linear_trend_forecast(values, forecast_hours)
        
        # Confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(values, prediction)
        
        # Anomaly detection
        anomalies = await self._detect_anomalies(values)
        
        return {
            'metric_id': metric_id,
            'metric_name': metric.name,
            'forecast_hours': forecast_hours,
            'current_value': metric.current_value,
            'predicted_values': prediction,
            'confidence_intervals': confidence_intervals,
            'trend_analysis': {
                'direction': metric.trend_direction,
                'strength': abs(metric.trend_percentage or 0),
                'consistency': self._calculate_trend_consistency(values)
            },
            'anomalies': anomalies,
            'prediction_accuracy': self._estimate_prediction_accuracy(values),
            'generated_at': datetime.now().isoformat()
        }
    
    async def _linear_trend_forecast(self, values: List[float], forecast_points: int) -> List[float]:
        """Generate linear trend forecast"""
        
        if len(values) < 2:
            return [values[0]] * forecast_points if values else [0] * forecast_points
        
        # Calculate linear trend
        x = list(range(len(values)))
        y = list(values)
        
        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x2 - sum_x ** 2 == 0:  # Avoid division by zero
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        intercept = (sum_y - slope * sum_x) / n
        
        # Generate predictions
        last_x = len(values) - 1
        predictions = []
        for i in range(forecast_points):
            future_x = last_x + i + 1
            predicted_y = slope * future_x + intercept
            predictions.append(max(0, predicted_y))  # Ensure non-negative predictions
        
        return predictions
    
    def _calculate_confidence_intervals(self, historical_values: List[float], predictions: List[float]) -> Dict[str, List[float]]:
        """Calculate confidence intervals for predictions"""
        
        if not historical_values:
            return {'upper': predictions, 'lower': predictions}
        
        # Calculate standard deviation of historical values
        std_dev = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
        
        # Simple confidence intervals (±2 standard deviations for ~95% confidence)
        upper_bounds = [pred + 2 * std_dev for pred in predictions]
        lower_bounds = [max(0, pred - 2 * std_dev) for pred in predictions]
        
        return {
            'upper': upper_bounds,
            'lower': lower_bounds
        }
    
    async def _detect_anomalies(self, values: List[float]) -> List[Dict[str, Any]]:
        """Detect anomalies in historical data"""
        
        if len(values) < 10:  # Need sufficient data for anomaly detection
            return []
        
        # Calculate mean and standard deviation
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        # Detect anomalies (values beyond 2 standard deviations)
        anomalies = []
        threshold = 2 * std_dev
        
        for i, value in enumerate(values):
            if abs(value - mean) > threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'deviation': abs(value - mean),
                    'type': 'high' if value > mean else 'low'
                })
        
        return anomalies
    
    def _calculate_trend_consistency(self, values: List[float]) -> float:
        """Calculate how consistent the trend is (0-1 scale)"""
        
        if len(values) < 3:
            return 0.5
        
        # Calculate direction changes
        direction_changes = 0
        for i in range(1, len(values) - 1):
            prev_direction = 1 if values[i] > values[i-1] else -1
            curr_direction = 1 if values[i+1] > values[i] else -1
            if prev_direction != curr_direction:
                direction_changes += 1
        
        # Consistency score (fewer direction changes = more consistent)
        max_possible_changes = len(values) - 2
        if max_possible_changes == 0:
            return 1.0
        
        consistency = 1.0 - (direction_changes / max_possible_changes)
        return consistency
    
    def _estimate_prediction_accuracy(self, values: List[float]) -> float:
        """Estimate prediction accuracy based on historical trend consistency"""
        
        consistency = self._calculate_trend_consistency(values)
        variance = statistics.variance(values) if len(values) > 1 else 0
        
        # Higher consistency and lower variance = higher accuracy
        accuracy = consistency * 0.6 + (1.0 / (1.0 + variance / 1000)) * 0.4
        return min(1.0, accuracy)

class DashboardEngine:
    """Engine for generating and managing analytics dashboards"""
    
    def __init__(self, metrics_collector: MetricsCollector, performance_analyzer: PerformanceAnalyzer):
        self.metrics_collector = metrics_collector
        self.performance_analyzer = performance_analyzer
        self.dashboards = {}
    
    def create_dashboard(self, config: DashboardConfig) -> str:
        """Create a new analytics dashboard"""
        self.dashboards[config.dashboard_id] = config
        logger.info(f"Created dashboard: {config.name}")
        return config.dashboard_id
    
    async def generate_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Generate data for dashboard rendering"""
        
        if dashboard_id not in self.dashboards:
            return {'error': f'Dashboard not found: {dashboard_id}'}
        
        config = self.dashboards[dashboard_id]
        
        # Generate data for each widget
        widget_data = {}
        for widget_config in config.widgets:
            widget_id = widget_config.get('id', str(uuid.uuid4()))
            widget_data[widget_id] = await self._generate_widget_data(widget_config)
        
        # Get overall performance summary
        performance_summary = await self.performance_analyzer.analyze_performance(AnalyticsPeriod.REALTIME)
        
        return {
            'dashboard_id': dashboard_id,
            'name': config.name,
            'description': config.description,
            'layout': config.layout,
            'refresh_interval': config.refresh_interval,
            'widgets': widget_data,
            'performance_summary': performance_summary,
            'generated_at': datetime.now().isoformat(),
            'metadata': config.metadata
        }
    
    async def _generate_widget_data(self, widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for a specific widget"""
        
        widget_type = widget_config.get('type', 'kpi_card')
        metric_id = widget_config.get('metric_id')
        
        if widget_type == 'kpi_card':
            return await self._generate_kpi_card_data(widget_config, metric_id)
        elif widget_type == 'line_chart':
            return await self._generate_line_chart_data(widget_config, metric_id)
        elif widget_type == 'bar_chart':
            return await self._generate_bar_chart_data(widget_config, metric_id)
        elif widget_type == 'pie_chart':
            return await self._generate_pie_chart_data(widget_config, metric_id)
        elif widget_type == 'gauge_chart':
            return await self._generate_gauge_chart_data(widget_config, metric_id)
        else:
            return {'error': f'Unsupported widget type: {widget_type}'}
    
    async def _generate_kpi_card_data(self, config: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
        """Generate KPI card widget data"""
        
        metric = self.metrics_collector.get_metric(metric_id) if metric_id else None
        
        if not metric:
            return {
                'type': 'kpi_card',
                'error': f'Metric not found: {metric_id}'
            }
        
        return {
            'type': 'kpi_card',
            'title': config.get('title', metric.name),
            'value': metric.current_value,
            'formatted_value': metric.format_string.format(metric.current_value) if isinstance(metric.current_value, (int, float)) else str(metric.current_value),
            'unit': metric.unit,
            'trend': {
                'direction': metric.trend_direction,
                'percentage': metric.trend_percentage,
                'color': self._get_trend_color(metric.trend_direction)
            },
            'status': self._get_metric_status(metric),
            'description': config.get('description', metric.description)
        }
    
    async def _generate_line_chart_data(self, config: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
        """Generate line chart widget data"""
        
        metric = self.metrics_collector.get_metric(metric_id) if metric_id else None
        
        if not metric or not metric.history:
            return {
                'type': 'line_chart',
                'error': 'No historical data available'
            }
        
        # Prepare time series data
        times, values = zip(*metric.history[-100:])  # Last 100 points
        
        return {
            'type': 'line_chart',
            'title': config.get('title', f'{metric.name} Trend'),
            'data': {
                'labels': [t.strftime('%H:%M') for t in times],
                'datasets': [{
                    'label': metric.name,
                    'data': list(values),
                    'borderColor': config.get('color', '#007bff'),
                    'tension': 0.1
                }]
            },
            'options': {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': metric.unit
                        }
                    }
                }
            }
        }
    
    async def _generate_bar_chart_data(self, config: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
        """Generate bar chart widget data"""
        
        # For demonstration, create sample category data
        categories = ['High Priority', 'Medium Priority', 'Low Priority', 'Monitor Only']
        values = [23, 45, 12, 8]  # Sample distribution
        
        return {
            'type': 'bar_chart',
            'title': config.get('title', 'Recommendation Distribution'),
            'data': {
                'labels': categories,
                'datasets': [{
                    'label': 'Count',
                    'data': values,
                    'backgroundColor': [
                        '#28a745',  # Green for high priority
                        '#ffc107',  # Yellow for medium priority
                        '#fd7e14',  # Orange for low priority
                        '#6c757d'   # Gray for monitor only
                    ]
                }]
            },
            'options': {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        }
    
    async def _generate_pie_chart_data(self, config: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
        """Generate pie chart widget data"""
        
        # Sample data for confidence distribution
        labels = ['Very High', 'High', 'Medium', 'Low', 'Very Low']
        values = [15, 35, 30, 15, 5]
        
        return {
            'type': 'pie_chart',
            'title': config.get('title', 'Confidence Distribution'),
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': values,
                    'backgroundColor': [
                        '#28a745',
                        '#20c997',
                        '#ffc107',
                        '#fd7e14',
                        '#dc3545'
                    ]
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {
                        'position': 'bottom'
                    }
                }
            }
        }
    
    async def _generate_gauge_chart_data(self, config: Dict[str, Any], metric_id: str) -> Dict[str, Any]:
        """Generate gauge chart widget data"""
        
        metric = self.metrics_collector.get_metric(metric_id) if metric_id else None
        
        if not metric:
            current_value = 75  # Default value
            max_value = 100
        else:
            current_value = float(metric.current_value) if isinstance(metric.current_value, (int, float)) else 0
            max_value = config.get('max_value', 100)
        
        return {
            'type': 'gauge_chart',
            'title': config.get('title', 'System Health'),
            'data': {
                'value': current_value,
                'max': max_value,
                'color': self._get_gauge_color(current_value, max_value)
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'tooltip': {
                        'enabled': False
                    }
                }
            }
        }
    
    def _get_trend_color(self, trend_direction: Optional[str]) -> str:
        """Get color for trend indicator"""
        if trend_direction == 'up':
            return '#28a745'  # Green
        elif trend_direction == 'down':
            return '#dc3545'  # Red
        else:
            return '#6c757d'  # Gray
    
    def _get_metric_status(self, metric: Metric) -> str:
        """Get status for metric based on thresholds"""
        if not metric.thresholds or not isinstance(metric.current_value, (int, float)):
            return 'normal'
        
        value = float(metric.current_value)
        
        if 'critical' in metric.thresholds and value >= metric.thresholds['critical']:
            return 'critical'
        elif 'warning' in metric.thresholds and value >= metric.thresholds['warning']:
            return 'warning'
        else:
            return 'normal'
    
    def _get_gauge_color(self, value: float, max_value: float) -> str:
        """Get color for gauge chart based on value"""
        percentage = (value / max_value) * 100
        
        if percentage >= 80:
            return '#28a745'  # Green
        elif percentage >= 60:
            return '#ffc107'  # Yellow
        elif percentage >= 40:
            return '#fd7e14'  # Orange
        else:
            return '#dc3545'  # Red
    
    def get_dashboard_config(self, dashboard_id: str) -> Optional[DashboardConfig]:
        """Get dashboard configuration"""
        return self.dashboards.get(dashboard_id)
    
    def list_dashboards(self) -> List[Dict[str, Any]]:
        """List all available dashboards"""
        return [
            {
                'id': dashboard_id,
                'name': config.name,
                'description': config.description,
                'created_at': config.created_at.isoformat(),
                'last_modified': config.last_modified.isoformat()
            }
            for dashboard_id, config in self.dashboards.items()
        ]

class AdvancedAnalyticsDashboard(BaseProcessor):
    """Main advanced analytics dashboard system"""
    
    def __init__(self):
        super().__init__()
        self.metrics_collector = MetricsCollector()
        self.performance_analyzer = PerformanceAnalyzer(self.metrics_collector)
        self.predictive_analytics = PredictiveAnalytics(self.metrics_collector)
        self.dashboard_engine = DashboardEngine(self.metrics_collector, self.performance_analyzer)
        
        # Initialize default metrics and dashboards
        asyncio.create_task(self._initialize_default_setup())
    
    async def _initialize_default_setup(self):
        """Initialize default metrics and dashboards"""
        
        # Register core system metrics
        await self._register_core_metrics()
        
        # Create default dashboard
        await self._create_default_dashboard()
        
        logger.info("Advanced analytics dashboard initialized")
    
    async def _register_core_metrics(self):
        """Register core system metrics"""
        
        core_metrics = [
            Metric(
                metric_id='response_time_avg',
                name='Average Response Time',
                description='Average API response time in milliseconds',
                metric_type=MetricType.GAUGE,
                current_value=234.7,
                unit='ms',
                format_string='{:.1f}',
                thresholds={'warning': 500, 'critical': 1000}
            ),
            Metric(
                metric_id='throughput_rpm',
                name='Throughput (RPM)',
                description='Requests processed per minute',
                metric_type=MetricType.RATE,
                current_value=245.3,
                unit='rpm',
                format_string='{:.1f}'
            ),
            Metric(
                metric_id='error_rate',
                name='Error Rate',
                description='Percentage of failed requests',
                metric_type=MetricType.PERCENTAGE,
                current_value=0.8,
                unit='%',
                format_string='{:.1f}',
                thresholds={'warning': 1.0, 'critical': 2.0}
            ),
            Metric(
                metric_id='memory_usage',
                name='Memory Usage',
                description='System memory usage percentage',
                metric_type=MetricType.GAUGE,
                current_value=42.3,
                unit='%',
                format_string='{:.1f}',
                thresholds={'warning': 70, 'critical': 85}
            ),
            Metric(
                metric_id='cache_hit_rate',
                name='Cache Hit Rate',
                description='Percentage of requests served from cache',
                metric_type=MetricType.PERCENTAGE,
                current_value=85.5,
                unit='%',
                format_string='{:.1f}'
            ),
            Metric(
                metric_id='active_profiles',
                name='Active Profiles',
                description='Number of currently active user profiles',
                metric_type=MetricType.GAUGE,
                current_value=12,
                unit='count',
                format_string='{:.0f}'
            ),
            Metric(
                metric_id='processed_opportunities',
                name='Processed Opportunities',
                description='Total opportunities processed by the system',
                metric_type=MetricType.COUNTER,
                current_value=1247,
                unit='count',
                format_string='{:,.0f}'
            )
        ]
        
        for metric in core_metrics:
            self.metrics_collector.register_metric(metric)
    
    async def _create_default_dashboard(self):
        """Create default analytics dashboard"""
        
        default_config = DashboardConfig(
            dashboard_id='main_dashboard',
            name='Main Analytics Dashboard',
            description='Primary system analytics and performance monitoring',
            layout='grid',
            columns=12,
            refresh_interval=30,
            widgets=[
                {
                    'id': 'response_time_kpi',
                    'type': 'kpi_card',
                    'metric_id': 'response_time_avg',
                    'title': 'Response Time',
                    'grid_position': {'row': 1, 'col': 1, 'width': 3, 'height': 2}
                },
                {
                    'id': 'throughput_kpi',
                    'type': 'kpi_card',
                    'metric_id': 'throughput_rpm',
                    'title': 'Throughput',
                    'grid_position': {'row': 1, 'col': 4, 'width': 3, 'height': 2}
                },
                {
                    'id': 'error_rate_kpi',
                    'type': 'kpi_card',
                    'metric_id': 'error_rate',
                    'title': 'Error Rate',
                    'grid_position': {'row': 1, 'col': 7, 'width': 3, 'height': 2}
                },
                {
                    'id': 'memory_gauge',
                    'type': 'gauge_chart',
                    'metric_id': 'memory_usage',
                    'title': 'Memory Usage',
                    'grid_position': {'row': 1, 'col': 10, 'width': 3, 'height': 2}
                },
                {
                    'id': 'response_time_trend',
                    'type': 'line_chart',
                    'metric_id': 'response_time_avg',
                    'title': 'Response Time Trend',
                    'grid_position': {'row': 3, 'col': 1, 'width': 6, 'height': 3}
                },
                {
                    'id': 'recommendation_distribution',
                    'type': 'bar_chart',
                    'title': 'Recommendation Distribution',
                    'grid_position': {'row': 3, 'col': 7, 'width': 6, 'height': 3}
                }
            ]
        )
        
        self.dashboard_engine.create_dashboard(default_config)
    
    async def process(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Main processing method for analytics dashboard"""
        try:
            logger.info(f"Processing analytics request for profile {profile_id}")
            
            operation = kwargs.get('operation', 'get_dashboard')
            
            if operation == 'get_dashboard':
                result = await self._get_dashboard_data(profile_id, **kwargs)
            elif operation == 'update_metric':
                result = await self._update_metric(profile_id, **kwargs)
            elif operation == 'get_performance_analysis':
                result = await self._get_performance_analysis(profile_id, **kwargs)
            elif operation == 'get_predictions':
                result = await self._get_predictions(profile_id, **kwargs)
            elif operation == 'create_dashboard':
                result = await self._create_custom_dashboard(profile_id, **kwargs)
            else:
                result = await self._get_analytics_overview(profile_id, **kwargs)
            
            return {
                'profile_id': profile_id,
                'operation': operation,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in advanced analytics dashboard: {e}")
            return {
                'profile_id': profile_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_dashboard_data(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Get dashboard data for rendering"""
        
        dashboard_id = kwargs.get('dashboard_id', 'main_dashboard')
        
        # Collect latest metrics
        await self.metrics_collector.collect_system_metrics()
        
        # Generate dashboard data
        dashboard_data = await self.dashboard_engine.generate_dashboard_data(dashboard_id)
        
        return {
            'dashboard_data': dashboard_data,
            'available_dashboards': self.dashboard_engine.list_dashboards()
        }
    
    async def _update_metric(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Update a specific metric value"""
        
        metric_id = kwargs.get('metric_id')
        value = kwargs.get('value')
        
        if not metric_id or value is None:
            return {'error': 'Missing metric_id or value'}
        
        success = await self.metrics_collector.update_metric(metric_id, value)
        
        return {
            'metric_updated': success,
            'metric_id': metric_id,
            'new_value': value
        }
    
    async def _get_performance_analysis(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Get comprehensive performance analysis"""
        
        period = kwargs.get('period', 'realtime')
        try:
            period_enum = AnalyticsPeriod(period)
        except ValueError:
            period_enum = AnalyticsPeriod.REALTIME
        
        analysis = await self.performance_analyzer.analyze_performance(period_enum)
        
        return {
            'performance_analysis': analysis
        }
    
    async def _get_predictions(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Get predictive analytics"""
        
        metric_id = kwargs.get('metric_id', 'response_time_avg')
        forecast_hours = kwargs.get('forecast_hours', 24)
        
        predictions = await self.predictive_analytics.generate_predictions(metric_id, forecast_hours)
        
        return {
            'predictions': predictions
        }
    
    async def _create_custom_dashboard(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Create a custom dashboard"""
        
        dashboard_config = kwargs.get('dashboard_config', {})
        
        config = DashboardConfig(
            dashboard_id=dashboard_config.get('id', str(uuid.uuid4())),
            name=dashboard_config.get('name', 'Custom Dashboard'),
            description=dashboard_config.get('description', 'User-created custom dashboard'),
            widgets=dashboard_config.get('widgets', [])
        )
        
        dashboard_id = self.dashboard_engine.create_dashboard(config)
        
        return {
            'dashboard_created': True,
            'dashboard_id': dashboard_id,
            'config': self._serialize_dashboard_config(config)
        }
    
    async def _get_analytics_overview(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Get comprehensive analytics overview"""
        
        # Collect latest metrics
        system_metrics = await self.metrics_collector.collect_system_metrics()
        
        # Get performance analysis
        performance = await self.performance_analyzer.analyze_performance(AnalyticsPeriod.REALTIME)
        
        # Get sample predictions
        predictions = await self.predictive_analytics.generate_predictions('response_time_avg', 6)
        
        # Get dashboard list
        dashboards = self.dashboard_engine.list_dashboards()
        
        return {
            'system_metrics': system_metrics,
            'performance_analysis': performance,
            'sample_predictions': predictions,
            'available_dashboards': dashboards,
            'metrics_count': len(self.metrics_collector.get_all_metrics()),
            'system_health': performance.get('overall_health', 'unknown')
        }
    
    def _serialize_dashboard_config(self, config: DashboardConfig) -> Dict[str, Any]:
        """Serialize dashboard configuration for JSON output"""
        return {
            'dashboard_id': config.dashboard_id,
            'name': config.name,
            'description': config.description,
            'layout': config.layout,
            'columns': config.columns,
            'refresh_interval': config.refresh_interval,
            'widgets_count': len(config.widgets),
            'theme': config.theme,
            'created_at': config.created_at.isoformat(),
            'last_modified': config.last_modified.isoformat()
        }

# Export main components
__all__ = [
    'AdvancedAnalyticsDashboard',
    'Metric',
    'DashboardConfig',
    'AnalyticsSnapshot',
    'MetricType',
    'AnalyticsPeriod',
    'DashboardWidget'
]