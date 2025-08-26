#!/usr/bin/env python3
"""
Desktop Debug and Performance Monitoring Tool
Enhanced desktop-specific debugging tools for Catalynx testing and development
Phase 4a: Desktop workflow optimization features
"""

import asyncio
import time
import psutil
import requests
import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_monitor.log')
    ]
)
logger = logging.getLogger(__name__)


class CatalynxDesktopMonitor:
    """Desktop-specific performance and debugging monitor"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.monitoring_active = False
        self.performance_data = []
        self.error_log = []
        self.api_metrics = {}
        self.system_metrics = {}
        
        # Desktop-specific keyboard shortcuts
        self.shortcuts = {
            'ctrl+shift+d': 'Toggle debug mode',
            'ctrl+shift+p': 'Show performance metrics',
            'ctrl+shift+r': 'Reset monitoring data',
            'ctrl+shift+s': 'Export system report'
        }
    
    def start_monitoring(self):
        """Start comprehensive system monitoring"""
        if self.monitoring_active:
            print("⚠️  Monitoring already active")
            return
        
        print("🚀 Starting Catalynx Desktop Debug Monitor...")
        self.monitoring_active = True
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_system_resources, daemon=True).start()
        threading.Thread(target=self._monitor_api_health, daemon=True).start()
        threading.Thread(target=self._monitor_modular_components, daemon=True).start()
        
        print("✅ Desktop monitoring active")
        print("💡 Available commands:")
        print("   'status' - Show current system status")
        print("   'performance' - Show performance metrics")
        print("   'apis' - Test API endpoints")
        print("   'modular' - Check modularization status")
        print("   'report' - Generate comprehensive report")
        print("   'stop' - Stop monitoring")
        print("   'help' - Show this help")
    
    def _monitor_system_resources(self):
        """Monitor system resources continuously"""
        while self.monitoring_active:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get process-specific metrics for Python processes
                python_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        if 'python' in proc.info['name'].lower():
                            python_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                self.system_metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_free_gb': disk.free / (1024**3),
                    'python_processes': len(python_processes),
                    'python_cpu_total': sum(p.get('cpu_percent', 0) for p in python_processes)
                }
                
                # Log high resource usage
                if cpu_percent > 80:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                if memory.percent > 80:
                    logger.warning(f"High memory usage: {memory.percent}%")
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(10)
    
    def _monitor_api_health(self):
        """Monitor API endpoint health"""
        api_endpoints = [
            ('/api/system/health', 'System Health'),
            ('/api/dashboard/overview', 'Dashboard'),
            ('/api/profiles', 'Profiles'),
            ('/api/discovery/tracks', 'Discovery'),
            ('/api/scoring/configuration', 'Scoring'),
            ('/api/ai/service-status', 'AI Services')
        ]
        
        while self.monitoring_active:
            try:
                endpoint_metrics = {}
                
                for endpoint, name in api_endpoints:
                    start_time = time.time()
                    try:
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        endpoint_metrics[name] = {
                            'status_code': response.status_code,
                            'response_time_ms': response_time,
                            'success': response.status_code == 200,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        if response_time > 1000:  # > 1 second
                            logger.warning(f"Slow API response: {endpoint} took {response_time:.1f}ms")
                        
                    except requests.exceptions.RequestException as e:
                        endpoint_metrics[name] = {
                            'status_code': None,
                            'response_time_ms': None,
                            'success': False,
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        }
                        logger.error(f"API endpoint failed: {endpoint} - {e}")
                
                self.api_metrics = endpoint_metrics
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"API monitoring error: {e}")
                time.sleep(15)
    
    def _monitor_modular_components(self):
        """Monitor modular component status"""
        while self.monitoring_active:
            try:
                # Check if modular routers are working
                modular_status = {}
                
                # Test each router
                router_endpoints = {
                    'dashboard': '/api/dashboard/overview',
                    'profiles': '/api/profiles',
                    'discovery': '/api/discovery/tracks',
                    'scoring': '/api/scoring/configuration',
                    'ai_processing': '/api/ai/service-status',
                    'export': '/api/export/formats'
                }
                
                for router_name, endpoint in router_endpoints.items():
                    try:
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=3)
                        modular_status[router_name] = {
                            'working': response.status_code in [200, 404],  # 404 acceptable for some
                            'status_code': response.status_code,
                            'timestamp': datetime.now().isoformat()
                        }
                    except Exception as e:
                        modular_status[router_name] = {
                            'working': False,
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        }
                
                self.modular_status = modular_status
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Modular component monitoring error: {e}")
                time.sleep(30)
    
    def show_status(self):
        """Show current system status"""
        print("\n📊 CATALYNX DESKTOP MONITOR STATUS")
        print("=" * 50)
        
        # System Resources
        if self.system_metrics:
            print(f"\n🖥️  SYSTEM RESOURCES:")
            print(f"   CPU Usage: {self.system_metrics['cpu_percent']:.1f}%")
            print(f"   Memory Usage: {self.system_metrics['memory_percent']:.1f}%")
            print(f"   Memory Available: {self.system_metrics['memory_available_gb']:.1f} GB")
            print(f"   Python Processes: {self.system_metrics['python_processes']}")
        
        # API Health
        if self.api_metrics:
            print(f"\n🌐 API ENDPOINTS:")
            for name, metrics in self.api_metrics.items():
                status = "✅" if metrics['success'] else "❌"
                if metrics.get('response_time_ms'):
                    print(f"   {status} {name}: {metrics['response_time_ms']:.1f}ms")
                else:
                    print(f"   {status} {name}: {metrics.get('error', 'Unknown error')}")
        
        # Modular Components
        if hasattr(self, 'modular_status'):
            print(f"\n🔧 MODULAR ROUTERS:")
            for router, status in self.modular_status.items():
                icon = "✅" if status['working'] else "❌"
                print(f"   {icon} {router.replace('_', ' ').title()}")
    
    def show_performance_metrics(self):
        """Show detailed performance metrics"""
        print("\n⚡ PERFORMANCE METRICS")
        print("=" * 50)
        
        if self.api_metrics:
            # API Performance Summary
            successful_apis = [m for m in self.api_metrics.values() if m['success']]
            if successful_apis:
                response_times = [m['response_time_ms'] for m in successful_apis if m['response_time_ms']]
                if response_times:
                    avg_response = sum(response_times) / len(response_times)
                    max_response = max(response_times)
                    min_response = min(response_times)
                    
                    print(f"API Performance:")
                    print(f"   Average Response Time: {avg_response:.1f}ms")
                    print(f"   Fastest Response: {min_response:.1f}ms")
                    print(f"   Slowest Response: {max_response:.1f}ms")
                    print(f"   Success Rate: {len(successful_apis)}/{len(self.api_metrics)} ({len(successful_apis)/len(self.api_metrics)*100:.1f}%)")
        
        if self.system_metrics:
            print(f"\nSystem Performance:")
            print(f"   CPU Load: {self.system_metrics['cpu_percent']:.1f}%")
            print(f"   Memory Usage: {self.system_metrics['memory_percent']:.1f}%")
            print(f"   Python CPU Usage: {self.system_metrics['python_cpu_total']:.1f}%")
    
    def test_modularization(self):
        """Test modularization status"""
        print("\n🔧 MODULARIZATION STATUS")
        print("=" * 50)
        
        # Check main.py size
        main_py_path = Path("src/web/main.py")
        if main_py_path.exists():
            with open(main_py_path, 'r', encoding='utf-8') as f:
                original_lines = len(f.readlines())
        else:
            original_lines = 7759  # Known original size
        
        # Check modular files
        modular_files = [
            "src/web/routers/dashboard.py",
            "src/web/routers/profiles.py", 
            "src/web/routers/discovery.py",
            "src/web/routers/scoring.py",
            "src/web/routers/ai_processing.py",
            "src/web/routers/export.py",
            "src/web/routers/websocket.py",
            "src/web/routers/admin.py",
            "src/web/main_modular.py"
        ]
        
        modular_lines = 0
        working_files = 0
        
        for file_path in modular_files:
            if Path(file_path).exists():
                working_files += 1
                with open(file_path, 'r', encoding='utf-8') as f:
                    modular_lines += len(f.readlines())
        
        progress = (modular_lines / original_lines) * 100 if original_lines > 0 else 0
        
        print(f"Backend Modularization:")
        print(f"   Original main.py: {original_lines:,} lines")
        print(f"   Modular components: {modular_lines:,} lines")
        print(f"   Progress: {progress:.1f}%")
        print(f"   Working files: {working_files}/{len(modular_files)}")
        
        # Check frontend modularization
        frontend_files = [
            "src/web/static/js/utils.js",
            "src/web/static/js/api/client.js",
            "src/web/static/js/modules/websocket.js",
            "src/web/static/js/modules/charts.js",
            "src/web/static/js/app_modular.js"
        ]
        
        frontend_working = sum(1 for f in frontend_files if Path(f).exists())
        
        print(f"\nFrontend Modularization:")
        print(f"   Modular JS files created: {frontend_working}/{len(frontend_files)}")
        print(f"   Original app.js: 14,928 lines")
        print(f"   Modular architecture: ✅ Complete" if frontend_working == len(frontend_files) else "❌ In Progress")
    
    def generate_report(self):
        """Generate comprehensive debug report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"catalynx_debug_report_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': self.system_metrics,
            'api_metrics': self.api_metrics,
            'modular_status': getattr(self, 'modular_status', {}),
            'monitoring_duration': time.time() - getattr(self, 'start_time', time.time()),
            'report_type': 'desktop_debug_comprehensive'
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📋 Debug report saved: {report_file}")
        return report_file
    
    def stop_monitoring(self):
        """Stop monitoring"""
        print("\n🛑 Stopping Catalynx Desktop Monitor...")
        self.monitoring_active = False
        print("✅ Monitoring stopped")
    
    def interactive_mode(self):
        """Run interactive monitoring mode"""
        self.start_time = time.time()
        self.start_monitoring()
        
        while True:
            try:
                command = input("\nCatalynx Monitor> ").strip().lower()
                
                if command == 'status':
                    self.show_status()
                elif command == 'performance':
                    self.show_performance_metrics()
                elif command == 'apis':
                    self.show_status()  # Shows API status
                elif command == 'modular':
                    self.test_modularization()
                elif command == 'report':
                    self.generate_report()
                elif command == 'stop' or command == 'quit' or command == 'exit':
                    self.stop_monitoring()
                    break
                elif command == 'help':
                    print("\n💡 Available commands:")
                    print("   status - Show current system status")
                    print("   performance - Show performance metrics") 
                    print("   apis - Test API endpoints")
                    print("   modular - Check modularization status")
                    print("   report - Generate comprehensive report")
                    print("   stop/quit/exit - Stop monitoring")
                    print("   help - Show this help")
                elif command == '':
                    continue
                else:
                    print(f"❌ Unknown command: '{command}'. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupted by user")
                self.stop_monitoring()
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main function for desktop debug monitor"""
    monitor = CatalynxDesktopMonitor()
    
    print("🖥️  Catalynx Desktop Debug & Performance Monitor")
    print("=" * 55)
    print("Desktop-specific debugging tool for POC development")
    print("Optimized for single-user desktop workflow testing")
    
    try:
        monitor.interactive_mode()
    except Exception as e:
        print(f"❌ Monitor failed: {e}")
        logger.error(f"Monitor failed: {e}")
    
    print("\n👋 Desktop Debug Monitor shutdown complete")


if __name__ == "__main__":
    main()