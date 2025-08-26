// Catalynx Chart Utilities
// Chart.js integration and visualization utilities extracted from monolithic app.js

class CatalynxCharts {
    constructor() {
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        };
        
        this.colorPalette = [
            '#3B82F6', // blue-500
            '#10B981', // green-500
            '#F59E0B', // yellow-500
            '#EF4444', // red-500
            '#8B5CF6', // purple-500
            '#06B6D4', // cyan-500
            '#F97316', // orange-500
            '#84CC16', // lime-500
            '#EC4899', // pink-500
            '#6B7280'  // gray-500
        ];
    }
    
    createRevenueChart(canvas, data) {
        if (!window.Chart) {
            console.error('Chart.js not loaded');
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Revenue ($)',
                    data: data.values || [],
                    backgroundColor: this.colorPalette[0],
                    borderColor: this.colorPalette[0],
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    createStageDistributionChart(canvas, data) {
        if (!window.Chart) {
            console.error('Chart.js not loaded');
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: this.colorPalette.slice(0, data.labels?.length || 0),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createTimelineChart(canvas, data) {
        if (!window.Chart) {
            console.error('Chart.js not loaded');
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.label || 'Timeline',
                    data: data.values || [],
                    borderColor: this.colorPalette[0],
                    backgroundColor: this.colorPalette[0] + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            parser: 'YYYY-MM-DD',
                            tooltipFormat: 'MMM DD, YYYY',
                            displayFormats: {
                                day: 'MMM DD',
                                month: 'MMM YYYY'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    createScoreComparisonChart(canvas, data) {
        if (!window.Chart) {
            console.error('Chart.js not loaded');
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.dimensions || [],
                datasets: [{
                    label: 'Opportunity Score',
                    data: data.scores || [],
                    borderColor: this.colorPalette[0],
                    backgroundColor: this.colorPalette[0] + '40',
                    pointBackgroundColor: this.colorPalette[0],
                    pointBorderColor: '#ffffff',
                    pointHoverBackgroundColor: '#ffffff',
                    pointHoverBorderColor: this.colorPalette[0]
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });
    }
    
    createPerformanceMetricsChart(canvas, data) {
        if (!window.Chart) {
            console.error('Chart.js not loaded');
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.metrics || [],
                datasets: [{
                    label: 'Performance',
                    data: data.values || [],
                    backgroundColor: data.values?.map((value, index) => {
                        // Color coding based on performance thresholds
                        if (value >= 80) return this.colorPalette[1]; // Green for good
                        if (value >= 60) return this.colorPalette[2]; // Yellow for fair
                        return this.colorPalette[3]; // Red for poor
                    }) || this.colorPalette.slice(0, data.values?.length || 0)
                }]
            },
            options: {
                ...this.defaultOptions,
                indexAxis: 'y', // Horizontal bars
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.x + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createNetworkVisualization(canvas, data) {
        // For network visualization, we'd typically use a different library like D3.js
        // This is a simplified Chart.js scatter plot representation
        if (!window.Chart) {
            console.error('Chart.js not loaded');
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        return new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Network Nodes',
                    data: data.nodes || [],
                    backgroundColor: this.colorPalette[4],
                    borderColor: this.colorPalette[4],
                    pointRadius: data.nodes?.map(node => Math.max(5, node.size || 5)) || []
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        min: -10,
                        max: 10
                    },
                    y: {
                        min: -10,
                        max: 10
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                const point = context[0];
                                return data.nodes[point.dataIndex]?.name || 'Node';
                            },
                            label: function(context) {
                                const point = data.nodes[context.dataIndex];
                                return [
                                    `Connections: ${point.connections || 0}`,
                                    `Influence: ${point.influence || 0}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateChart(chart, newData) {
        if (!chart) return;
        
        // Update data
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }
        
        if (newData.datasets) {
            chart.data.datasets = newData.datasets;
        } else if (newData.values && chart.data.datasets[0]) {
            chart.data.datasets[0].data = newData.values;
        }
        
        // Re-render chart
        chart.update('active');
    }
    
    destroyChart(chart) {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    }
    
    resizeChart(chart) {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    }
    
    // Utility method to prepare data for charts
    prepareChartData(rawData, type) {
        switch (type) {
            case 'revenue':
                return {
                    labels: rawData.map(item => item.name || item.label),
                    values: rawData.map(item => item.revenue || item.value)
                };
            
            case 'stage':
                const stageCounts = {};
                rawData.forEach(item => {
                    const stage = item.stage || 'unknown';
                    stageCounts[stage] = (stageCounts[stage] || 0) + 1;
                });
                return {
                    labels: Object.keys(stageCounts),
                    values: Object.values(stageCounts)
                };
            
            case 'timeline':
                const sortedData = rawData.sort((a, b) => new Date(a.date) - new Date(b.date));
                return {
                    labels: sortedData.map(item => item.date),
                    values: sortedData.map(item => item.value),
                    label: 'Timeline Data'
                };
            
            default:
                return { labels: [], values: [] };
        }
    }
    
    // Export chart as image
    exportChart(chart, filename = 'chart.png') {
        if (!chart || !chart.canvas) return;
        
        const url = chart.canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = filename;
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Create global charts instance
const charts = new CatalynxCharts();
window.CatalynxCharts = charts;

export default charts;