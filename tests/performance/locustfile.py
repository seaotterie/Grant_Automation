# Locust Performance Testing for Catalynx Platform
# Load testing configuration for realistic user scenarios

from locust import HttpUser, task, between, events
import json
import random
import time
from datetime import datetime, timedelta

class CatalynxUser(HttpUser):
    """Standard user performing typical grant research activities"""
    
    wait_time = between(2, 8)  # 2-8 seconds between requests
    weight = 3  # Most common user type
    
    def on_start(self):
        """Initialize user session"""
        self.profile_id = None
        self.created_profiles = []
        self.discovered_opportunities = []
        
        # Create a test profile for this user session
        self.create_test_profile()
    
    def create_test_profile(self):
        """Create a test profile for this user"""
        profile_data = {
            "organization_name": f"Load Test Organization {random.randint(1000, 9999)}",
            "mission_statement": "Supporting community initiatives through innovative programs",
            "ntee_codes": random.choice([["B25"], ["P20"], ["T30"], ["B25", "B28"]]),
            "revenue": random.randint(500000, 10000000),
            "staff_count": random.randint(10, 100),
            "years_active": random.randint(5, 30),
            "state": random.choice(["VA", "MD", "NC", "DC", "NY", "CA"]),
            "focus_areas": random.choice([
                ["education", "literacy"],
                ["health", "community"],
                ["environment", "conservation"],
                ["arts", "culture"]
            ])
        }
        
        with self.client.post("/api/profiles", 
                             json=profile_data, 
                             catch_response=True) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                self.profile_id = data.get("profile_id")
                self.created_profiles.append(self.profile_id)
                response.success()
            else:
                response.failure(f"Failed to create profile: {response.status_code}")
    
    @task(5)
    def view_dashboard(self):
        """Most common action - view main dashboard"""
        self.client.get("/", name="dashboard")
    
    @task(4)
    def check_system_health(self):
        """Check system health - frequent monitoring"""
        self.client.get("/api/health", name="health_check")
    
    @task(3)
    def view_profile_analytics(self):
        """View profile analytics"""
        if self.profile_id:
            with self.client.get(f"/api/profiles/{self.profile_id}/analytics", 
                                catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Profile not found is acceptable
                else:
                    response.failure(f"Analytics failed: {response.status_code}")
    
    @task(2)
    def run_entity_discovery(self):
        """Run entity-based discovery"""
        if self.profile_id:
            discovery_params = {
                "max_results": random.randint(5, 20),
                "ntee_filter": random.choice([["B25"], ["P20"], None]),
                "revenue_range": {
                    "min": random.randint(10000, 100000),
                    "max": random.randint(1000000, 5000000)
                }
            }
            
            with self.client.post(f"/api/profiles/{self.profile_id}/discover/entity-analytics",
                                 json=discovery_params,
                                 catch_response=True) as response:
                if response.status_code in [200, 202]:
                    if response.status_code == 200:
                        data = response.json()
                        opportunities = data.get("opportunities", [])
                        self.discovered_opportunities.extend(opportunities[:5])  # Keep first 5
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Profile not found is acceptable
                else:
                    response.failure(f"Discovery failed: {response.status_code}")
    
    @task(2)
    def view_cache_stats(self):
        """Check entity cache statistics"""
        with self.client.get("/api/discovery/entity-cache-stats", 
                           catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Cache stats failed: {response.status_code}")
    
    @task(1)
    def run_ai_lite_analysis(self):
        """Run AI-Lite analysis on discovered opportunities"""
        if self.profile_id and self.discovered_opportunities:
            opportunity = random.choice(self.discovered_opportunities)
            
            analysis_data = {
                "profile_id": self.profile_id,
                "opportunity_id": opportunity.get("opportunity_id", "test_opp"),
                "analysis_type": "strategic_fit"
            }
            
            with self.client.post("/api/ai/lite-analysis",
                                 json=analysis_data,
                                 catch_response=True) as response:
                if response.status_code in [200, 202, 404, 501]:
                    response.success()
                else:
                    response.failure(f"AI analysis failed: {response.status_code}")
    
    @task(1)
    def export_opportunities(self):
        """Export opportunities data"""
        if self.profile_id:
            export_data = {
                "profile_id": self.profile_id,
                "format": random.choice(["json", "csv", "pdf"]),
                "template": "standard"
            }
            
            with self.client.post("/api/export/opportunities",
                                 json=export_data,
                                 catch_response=True) as response:
                if response.status_code in [200, 202, 404, 501]:
                    response.success()
                else:
                    response.failure(f"Export failed: {response.status_code}")
    
    def on_stop(self):
        """Cleanup when user session ends"""
        # Clean up created profiles
        for profile_id in self.created_profiles:
            try:
                self.client.delete(f"/api/profiles/{profile_id}")
            except:
                pass  # Ignore cleanup errors


class PowerUser(HttpUser):
    """Power user performing intensive research activities"""
    
    wait_time = between(1, 3)  # Faster interactions
    weight = 1  # Less common but more intensive
    
    def on_start(self):
        """Initialize power user session"""
        self.profiles = []
        self.create_multiple_profiles()
    
    def create_multiple_profiles(self):
        """Create multiple profiles for comparison analysis"""
        for i in range(3):  # Create 3 profiles
            profile_data = {
                "organization_name": f"Power User Org {i+1}-{random.randint(100, 999)}",
                "revenue": random.randint(1000000, 50000000),
                "ntee_codes": [random.choice(["B25", "P20", "T30"])],
                "state": random.choice(["VA", "NY", "CA"])
            }
            
            response = self.client.post("/api/profiles", json=profile_data)
            if response.status_code in [200, 201]:
                data = response.json()
                self.profiles.append(data.get("profile_id"))
    
    @task(3)
    def intensive_discovery(self):
        """Run intensive discovery across multiple profiles"""
        if self.profiles:
            profile_id = random.choice(self.profiles)
            
            # Large discovery request
            discovery_params = {
                "max_results": 50,  # Maximum results
                "include_analysis": True,
                "detailed_matching": True
            }
            
            self.client.post(f"/api/profiles/{profile_id}/discover/entity-analytics",
                           json=discovery_params,
                           name="intensive_discovery")
    
    @task(2)
    def batch_analysis(self):
        """Perform batch analysis operations"""
        if self.profiles:
            # Simulate batch scoring
            opportunities = [
                {"opportunity_id": f"batch_opp_{i}", "name": f"Batch Opp {i}"}
                for i in range(10)
            ]
            
            batch_data = {
                "opportunities": opportunities,
                "analysis_type": "comprehensive"
            }
            
            profile_id = random.choice(self.profiles)
            self.client.post(f"/api/profiles/{profile_id}/opportunity-scores",
                           json=batch_data,
                           name="batch_analysis")
    
    @task(1)
    def generate_comprehensive_report(self):
        """Generate comprehensive reports"""
        if self.profiles:
            profile_id = random.choice(self.profiles)
            
            report_data = {
                "profile_id": profile_id,
                "format": "pdf",
                "template": "comprehensive",
                "include_charts": True,
                "include_analysis": True
            }
            
            self.client.post("/api/export/comprehensive-report",
                           json=report_data,
                           name="comprehensive_report")
    
    def on_stop(self):
        """Cleanup power user data"""
        for profile_id in self.profiles:
            try:
                self.client.delete(f"/api/profiles/{profile_id}")
            except:
                pass


class AdminUser(HttpUser):
    """Administrator performing system monitoring and maintenance"""
    
    wait_time = between(10, 30)  # Less frequent but important operations
    weight = 1  # Rare but critical
    
    @task(3)
    def monitor_system_status(self):
        """Monitor overall system health"""
        self.client.get("/api/system/status", name="system_status")
    
    @task(2)
    def check_performance_metrics(self):
        """Check system performance metrics"""
        self.client.get("/api/metrics", name="performance_metrics")
    
    @task(2)
    def monitor_cache_performance(self):
        """Monitor cache performance"""
        self.client.get("/api/discovery/entity-cache-stats", name="cache_monitoring")
    
    @task(1)
    def system_analytics_overview(self):
        """Get system-wide analytics"""
        self.client.get("/api/analytics/overview", name="system_analytics")


# Event handlers for custom metrics
@events.request.add_listener
def request_handler(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Custom request handler for detailed metrics"""
    if exception:
        print(f"Request failed: {name} - {exception}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment"""
    print("Starting Catalynx load test...")
    print(f"Target host: {environment.host}")

@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """Cleanup after test completion"""
    print("\nCatalynx load test completed.")
    
    # Print summary statistics
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")


# Custom test scenarios for specific features
class DiscoveryStressTest(HttpUser):
    """Stress test focused on discovery operations"""
    
    wait_time = between(0.5, 2)  # Aggressive timing
    
    def on_start(self):
        """Setup for discovery stress test"""
        self.profile_id = "discovery_stress_profile"
        
        # Create dedicated profile
        profile_data = {
            "organization_name": "Discovery Stress Test Org",
            "revenue": 5000000,
            "ntee_codes": ["B25"],
            "state": "VA"
        }
        
        response = self.client.post("/api/profiles", json=profile_data)
        if response.status_code in [200, 201]:
            data = response.json()
            self.profile_id = data.get("profile_id", self.profile_id)
    
    @task
    def rapid_discovery_requests(self):
        """Rapid fire discovery requests"""
        discovery_params = {
            "max_results": random.randint(1, 10),
            "quick_mode": True
        }
        
        self.client.post(f"/api/profiles/{self.profile_id}/discover/entity-analytics",
                        json=discovery_params,
                        name="rapid_discovery")


class CachePerformanceTest(HttpUser):
    """Test focused on cache performance"""
    
    wait_time = between(0.1, 0.5)  # Very rapid requests
    
    @task(5)
    def cache_hit_requests(self):
        """Generate requests likely to hit cache"""
        # Request same entities repeatedly to test cache hits
        entity_ids = ["popular_entity_1", "popular_entity_2", "popular_entity_3"]
        entity_id = random.choice(entity_ids)
        
        self.client.get(f"/api/entities/{entity_id}/data", name="cache_hit_test")
    
    @task(1)
    def cache_miss_requests(self):
        """Generate requests likely to miss cache"""
        # Request unique entities to test cache misses
        entity_id = f"unique_entity_{random.randint(10000, 99999)}"
        
        self.client.get(f"/api/entities/{entity_id}/data", name="cache_miss_test")


# Performance test configuration
class WebsiteTestUser(HttpUser):
    """Simulated website user for realistic load patterns"""
    
    # Realistic user behavior timing
    wait_time = between(3, 15)
    
    @task(10)
    def browse_homepage(self):
        """Browse main page - most common action"""
        self.client.get("/")
    
    @task(5)
    def view_static_content(self):
        """View static content like documentation"""
        static_paths = ["/static/style.css", "/static/app.js"]
        path = random.choice(static_paths)
        self.client.get(path, name="static_content")
    
    @task(2)
    def search_functionality(self):
        """Use search features"""
        search_terms = ["education", "health", "environment", "community"]
        term = random.choice(search_terms)
        
        self.client.get(f"/api/search?q={term}", name="search")
    
    @task(1)
    def help_documentation(self):
        """Access help and documentation"""
        self.client.get("/api/help", name="help_docs")