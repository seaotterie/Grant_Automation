#!/usr/bin/env python3
"""
Comprehensive Security Testing Framework for Catalynx
DevOps security best practices implementation covering:
- API Security Testing
- Input Validation & Injection Prevention
- Authentication & Authorization
- Data Privacy & Protection
- Rate Limiting & DOS Prevention
- Secure Configuration Validation
"""

import requests
import json
import time
import sys
import secrets
import string
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
import base64

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

class SecurityTestSuite:
    """Comprehensive security testing framework"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        self.test_profile_id = None
        
    def log_result(self, test_name, status, severity="INFO", details="", recommendation=""):
        """Log security test result"""
        result = {
            "test_name": test_name,
            "status": status,  # SECURE, VULNERABLE, WARNING, ERROR
            "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW, INFO
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "recommendation": recommendation
        }
        self.results.append(result)
        
        if status == "SECURE":
            status_symbol = "[SECURE]"
        elif status == "VULNERABLE":
            status_symbol = "[VULN]"
        elif status == "WARNING":
            status_symbol = "[WARN]"
        else:
            status_symbol = "[ERROR]"
        
        print(f"{status_symbol} {test_name} ({severity})")
        if details:
            print(f"   Details: {details}")
        if recommendation:
            print(f"   Recommendation: {recommendation}")
        print()
    
    def test_api_security_headers(self):
        """Test 1: API Security Headers"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            headers = response.headers
            
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=",
                "Content-Security-Policy": "default-src"
            }
            
            missing_headers = []
            present_headers = []
            
            for header, expected in security_headers.items():
                if header in headers:
                    if isinstance(expected, list):
                        if any(exp in headers[header] for exp in expected):
                            present_headers.append(header)
                        else:
                            missing_headers.append(f"{header} (invalid value)")
                    else:
                        if expected in headers[header]:
                            present_headers.append(header)
                        else:
                            missing_headers.append(f"{header} (invalid value)")
                else:
                    missing_headers.append(header)
            
            if not missing_headers:
                self.log_result(
                    "Security Headers",
                    "SECURE",
                    "LOW",
                    f"All security headers present: {present_headers}"
                )
            elif len(missing_headers) <= 2:
                self.log_result(
                    "Security Headers",
                    "WARNING",
                    "MEDIUM",
                    f"Missing headers: {missing_headers}",
                    "Implement missing security headers in web server configuration"
                )
            else:
                self.log_result(
                    "Security Headers",
                    "VULNERABLE",
                    "HIGH",
                    f"Multiple missing headers: {missing_headers}",
                    "CRITICAL: Implement comprehensive security headers"
                )
                
        except Exception as e:
            self.log_result(
                "Security Headers",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def test_sql_injection_prevention(self):
        """Test 2: SQL Injection Prevention"""
        try:
            # Test common SQL injection payloads
            sql_payloads = [
                "'; DROP TABLE profiles; --",
                "' OR '1'='1",
                "' UNION SELECT * FROM users --",
                "'; INSERT INTO profiles VALUES (1,2,3); --",
                "admin'--",
                "admin' /*",
                "' OR 1=1--"
            ]
            
            vulnerable_endpoints = []
            protected_endpoints = []
            
            # Test profile search (if available)
            for payload in sql_payloads:
                try:
                    # Test search parameter
                    response = self.session.get(f"{self.base_url}/api/profiles?search={quote_plus(payload)}")
                    
                    # Check if payload is reflected or causes SQL errors
                    if (response.status_code == 500 and 
                        any(error in response.text.lower() for error in ['sql', 'syntax', 'mysql', 'postgres', 'sqlite'])):
                        vulnerable_endpoints.append(f"profile search: {payload}")
                    else:
                        protected_endpoints.append("profile search")
                        break
                except:
                    pass
            
            # Test profile creation with SQL injection
            for payload in sql_payloads[:3]:  # Test subset for profile creation
                try:
                    malicious_profile = {
                        "name": payload,
                        "organization_type": "nonprofit",
                        "focus_areas": ["test"]
                    }
                    response = self.session.post(f"{self.base_url}/api/profiles", json=malicious_profile)
                    
                    if response.status_code == 500 and 'sql' in response.text.lower():
                        vulnerable_endpoints.append(f"profile creation: {payload}")
                        break
                except:
                    pass
            
            if vulnerable_endpoints:
                self.log_result(
                    "SQL Injection Prevention",
                    "VULNERABLE",
                    "CRITICAL",
                    f"SQL injection possible on: {vulnerable_endpoints}",
                    "URGENT: Implement parameterized queries and input validation"
                )
            else:
                self.log_result(
                    "SQL Injection Prevention",
                    "SECURE",
                    "LOW",
                    "No SQL injection vulnerabilities detected in tested endpoints"
                )
                
        except Exception as e:
            self.log_result(
                "SQL Injection Prevention",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def test_xss_prevention(self):
        """Test 3: Cross-Site Scripting (XSS) Prevention"""
        try:
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "';alert(String.fromCharCode(88,83,83))//'"
            ]
            
            vulnerable_endpoints = []
            
            # Test profile creation for XSS
            for payload in xss_payloads:
                try:
                    xss_profile = {
                        "name": payload,
                        "organization_type": "nonprofit",
                        "mission_statement": payload,
                        "focus_areas": [payload]
                    }
                    response = self.session.post(f"{self.base_url}/api/profiles", json=xss_profile)
                    
                    if response.status_code in [200, 201]:
                        profile_data = response.json()
                        profile_id = profile_data.get("profile", {}).get("profile_id")
                        
                        if profile_id:
                            # Retrieve profile and check if script is reflected
                            get_response = self.session.get(f"{self.base_url}/api/profiles/{profile_id}")
                            if get_response.status_code == 200 and payload in get_response.text:
                                vulnerable_endpoints.append(f"profile fields: {payload}")
                            
                            # Cleanup
                            try:
                                self.session.delete(f"{self.base_url}/api/profiles/{profile_id}")
                            except:
                                pass
                            break
                except:
                    pass
            
            # Test dashboard for reflected XSS
            try:
                response = self.session.get(f"{self.base_url}/?search=<script>alert('XSS')</script>")
                if response.status_code == 200 and "<script>" in response.text:
                    vulnerable_endpoints.append("dashboard search parameter")
            except:
                pass
            
            if vulnerable_endpoints:
                self.log_result(
                    "XSS Prevention",
                    "VULNERABLE",
                    "HIGH",
                    f"XSS vulnerabilities found in: {vulnerable_endpoints}",
                    "Implement proper output encoding and Content Security Policy"
                )
            else:
                self.log_result(
                    "XSS Prevention",
                    "SECURE",
                    "LOW",
                    "No XSS vulnerabilities detected in tested endpoints"
                )
                
        except Exception as e:
            self.log_result(
                "XSS Prevention",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def test_input_validation(self):
        """Test 4: Input Validation & Sanitization"""
        try:
            validation_issues = []
            
            # Test extremely long inputs
            long_string = "A" * 10000
            try:
                long_profile = {
                    "name": long_string,
                    "organization_type": "nonprofit",
                    "mission_statement": long_string,
                    "focus_areas": ["test"]
                }
                response = self.session.post(f"{self.base_url}/api/profiles", json=long_profile)
                
                if response.status_code in [200, 201]:
                    validation_issues.append("Accepts extremely long input strings")
                    # Cleanup
                    try:
                        profile_data = response.json().get("profile", {})
                        if profile_data.get("profile_id"):
                            self.session.delete(f"{self.base_url}/api/profiles/{profile_data['profile_id']}")
                    except:
                        pass
            except:
                pass
            
            # Test special characters and encoding
            special_chars = ["../../../etc/passwd", "\x00\x01\x02", "../../windows/system32"]
            for chars in special_chars:
                try:
                    special_profile = {
                        "name": chars,
                        "organization_type": "nonprofit",
                        "focus_areas": ["test"]
                    }
                    response = self.session.post(f"{self.base_url}/api/profiles", json=special_profile)
                    
                    if response.status_code in [200, 201] and chars in response.text:
                        validation_issues.append(f"Accepts dangerous special characters: {chars[:20]}")
                        # Cleanup
                        try:
                            profile_data = response.json().get("profile", {})
                            if profile_data.get("profile_id"):
                                self.session.delete(f"{self.base_url}/api/profiles/{profile_data['profile_id']}")
                        except:
                            pass
                        break
                except:
                    pass
            
            # Test invalid data types
            try:
                invalid_profile = {
                    "name": 12345,  # Should be string
                    "organization_type": ["invalid"],  # Should be string
                    "annual_revenue": "not_a_number",  # Should be integer
                    "focus_areas": "not_an_array"  # Should be array
                }
                response = self.session.post(f"{self.base_url}/api/profiles", json=invalid_profile)
                
                if response.status_code in [200, 201]:
                    validation_issues.append("Accepts invalid data types")
            except:
                pass
            
            if validation_issues:
                severity = "HIGH" if len(validation_issues) > 2 else "MEDIUM"
                self.log_result(
                    "Input Validation",
                    "VULNERABLE",
                    severity,
                    f"Validation issues: {validation_issues}",
                    "Implement strict input validation and type checking"
                )
            else:
                self.log_result(
                    "Input Validation",
                    "SECURE",
                    "LOW",
                    "Input validation appears to be working correctly"
                )
                
        except Exception as e:
            self.log_result(
                "Input Validation",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def test_rate_limiting(self):
        """Test 5: Rate Limiting & DOS Prevention"""
        try:
            # Test rapid requests to health endpoint
            start_time = time.time()
            request_count = 0
            blocked_requests = 0
            
            for i in range(50):  # Send 50 rapid requests
                try:
                    response = self.session.get(f"{self.base_url}/api/health")
                    request_count += 1
                    
                    if response.status_code == 429:  # Too Many Requests
                        blocked_requests += 1
                    elif response.status_code != 200:
                        break
                    
                    time.sleep(0.01)  # Brief pause
                except:
                    break
            
            duration = time.time() - start_time
            requests_per_second = request_count / duration
            
            if blocked_requests > 0:
                self.log_result(
                    "Rate Limiting",
                    "SECURE",
                    "LOW",
                    f"Rate limiting active: {blocked_requests}/{request_count} requests blocked"
                )
            elif requests_per_second > 100:  # Very high rate allowed
                self.log_result(
                    "Rate Limiting",
                    "VULNERABLE",
                    "MEDIUM",
                    f"No rate limiting detected: {requests_per_second:.1f} req/sec allowed",
                    "Implement rate limiting to prevent DOS attacks"
                )
            else:
                self.log_result(
                    "Rate Limiting",
                    "WARNING",
                    "LOW",
                    f"Rate limiting unclear: {requests_per_second:.1f} req/sec, {blocked_requests} blocked"
                )
                
        except Exception as e:
            self.log_result(
                "Rate Limiting",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def test_authentication_security(self):
        """Test 6: Authentication & Authorization"""
        try:
            auth_issues = []
            
            # Test for authentication requirements
            sensitive_endpoints = [
                "/api/profiles",
                "/api/admin",
                "/api/config",
                "/api/users"
            ]
            
            for endpoint in sensitive_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        auth_issues.append(f"{endpoint} accessible without authentication")
                    elif response.status_code == 401:
                        # Good - requires authentication
                        pass
                except:
                    pass
            
            # Test session security
            if 'session' in str(self.session.cookies):
                session_cookies = [cookie for cookie in self.session.cookies if 'session' in cookie.name.lower()]
                for cookie in session_cookies:
                    if not cookie.secure:
                        auth_issues.append("Session cookie not marked secure")
                    if not hasattr(cookie, 'httponly') or not cookie.httponly:
                        auth_issues.append("Session cookie not marked HttpOnly")
            
            # Test for default credentials (if login exists)
            default_creds = [
                ("admin", "admin"),
                ("admin", "password"),
                ("admin", "123456"),
                ("user", "user")
            ]
            
            for username, password in default_creds:
                try:
                    login_data = {"username": username, "password": password}
                    response = self.session.post(f"{self.base_url}/api/login", json=login_data)
                    if response.status_code == 200:
                        auth_issues.append(f"Default credentials work: {username}:{password}")
                        break
                except:
                    pass
            
            if auth_issues:
                severity = "CRITICAL" if any("accessible without" in issue for issue in auth_issues) else "MEDIUM"
                self.log_result(
                    "Authentication Security",
                    "VULNERABLE",
                    severity,
                    f"Authentication issues: {auth_issues}",
                    "Implement proper authentication and authorization"
                )
            else:
                self.log_result(
                    "Authentication Security",
                    "SECURE",
                    "LOW",
                    "Authentication appears to be properly configured"
                )
                
        except Exception as e:
            self.log_result(
                "Authentication Security",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def test_data_privacy_protection(self):
        """Test 7: Data Privacy & Protection"""
        try:
            privacy_issues = []
            
            # Create test profile with sensitive data
            test_profile = {
                "name": "Privacy Test Org",
                "organization_type": "nonprofit",
                "ein": "12-3456789",  # Sensitive data
                "mission_statement": "Testing data privacy controls",
                "focus_areas": ["privacy"],
                "annual_revenue": 1000000,
                "notes": "Confidential internal notes"
            }
            
            response = self.session.post(f"{self.base_url}/api/profiles", json=test_profile)
            
            if response.status_code in [200, 201]:
                profile_data = response.json().get("profile", {})
                profile_id = profile_data.get("profile_id")
                
                # Test data exposure in responses
                response_text = json.dumps(response.json())
                
                # Check for potentially sensitive data in logs or errors
                sensitive_patterns = ["password", "secret", "key", "token", "confidential"]
                exposed_data = [pattern for pattern in sensitive_patterns if pattern in response_text.lower()]
                
                if exposed_data:
                    privacy_issues.append(f"Potentially sensitive data exposed: {exposed_data}")
                
                # Test data retention - can we retrieve after "deletion"?
                if profile_id:
                    delete_response = self.session.delete(f"{self.base_url}/api/profiles/{profile_id}")
                    if delete_response.status_code in [200, 204]:
                        # Try to access deleted profile
                        get_response = self.session.get(f"{self.base_url}/api/profiles/{profile_id}")
                        if get_response.status_code == 200:
                            privacy_issues.append("Deleted profile data still accessible")
                
                # Test for PII in logs
                try:
                    logs_response = self.session.get(f"{self.base_url}/api/logs")
                    if logs_response.status_code == 200 and "12-3456789" in logs_response.text:
                        privacy_issues.append("PII (EIN) appears in logs")
                except:
                    pass
            
            if privacy_issues:
                self.log_result(
                    "Data Privacy Protection",
                    "VULNERABLE",
                    "HIGH",
                    f"Privacy issues: {privacy_issues}",
                    "Implement data privacy controls and PII protection"
                )
            else:
                self.log_result(
                    "Data Privacy Protection",
                    "SECURE",
                    "LOW",
                    "Data privacy appears to be properly protected"
                )
                
        except Exception as e:
            self.log_result(
                "Data Privacy Protection",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def test_secure_configuration(self):
        """Test 8: Secure Configuration"""
        try:
            config_issues = []
            
            # Test for information disclosure
            info_endpoints = [
                "/api/version",
                "/api/info",
                "/api/config",
                "/api/debug",
                "/.env",
                "/config.json",
                "/api/docs",  # OpenAPI docs might reveal too much
                "/docs"
            ]
            
            for endpoint in info_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        content = response.text.lower()
                        # Check for sensitive information
                        if any(keyword in content for keyword in ['password', 'secret', 'key', 'token', 'database']):
                            config_issues.append(f"{endpoint} exposes sensitive configuration")
                        elif endpoint in ["/api/docs", "/docs"]:
                            # API docs are OK but note them
                            pass
                        else:
                            config_issues.append(f"{endpoint} accessible (information disclosure)")
                except:
                    pass
            
            # Test error handling
            try:
                response = self.session.get(f"{self.base_url}/api/nonexistent/endpoint/12345")
                if response.status_code == 500:
                    error_content = response.text.lower()
                    if any(keyword in error_content for keyword in ['traceback', 'file path', 'line number']):
                        config_issues.append("Detailed error messages expose system information")
            except:
                pass
            
            # Test HTTP methods
            try:
                # Test if dangerous methods are allowed
                response = self.session.request('TRACE', f"{self.base_url}/api/health")
                if response.status_code not in [405, 501]:
                    config_issues.append("TRACE method enabled (potential security risk)")
            except:
                pass
            
            if config_issues:
                severity = "HIGH" if any("sensitive" in issue for issue in config_issues) else "MEDIUM"
                self.log_result(
                    "Secure Configuration",
                    "VULNERABLE",
                    severity,
                    f"Configuration issues: {config_issues}",
                    "Review and secure server configuration"
                )
            else:
                self.log_result(
                    "Secure Configuration",
                    "SECURE",
                    "LOW",
                    "Server configuration appears secure"
                )
                
        except Exception as e:
            self.log_result(
                "Secure Configuration",
                "ERROR",
                "INFO",
                f"Exception: {str(e)}"
            )
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        total_tests = len(self.results)
        secure_tests = len([r for r in self.results if r["status"] == "SECURE"])
        vulnerable_tests = len([r for r in self.results if r["status"] == "VULNERABLE"])
        warning_tests = len([r for r in self.results if r["status"] == "WARNING"])
        error_tests = len([r for r in self.results if r["status"] == "ERROR"])
        
        # Calculate risk levels
        critical_issues = len([r for r in self.results if r["severity"] == "CRITICAL"])
        high_issues = len([r for r in self.results if r["severity"] == "HIGH"])
        medium_issues = len([r for r in self.results if r["severity"] == "MEDIUM"])
        
        print("\n" + "="*80)
        print("SECURITY TESTING REPORT")
        print("="*80)
        print(f"Security Tests Executed: {total_tests}")
        print(f"Secure: {secure_tests} [SECURE]")
        print(f"Vulnerable: {vulnerable_tests} [VULN]")
        print(f"Warnings: {warning_tests} [WARN]")
        print(f"Errors: {error_tests} [ERROR]")
        print()
        print("RISK ASSESSMENT:")
        print(f"Critical Issues: {critical_issues}")
        print(f"High Risk Issues: {high_issues}")
        print(f"Medium Risk Issues: {medium_issues}")
        
        # Calculate security score
        if total_tests > 0:
            security_score = ((secure_tests + (warning_tests * 0.5)) / total_tests) * 100
            print(f"Security Score: {security_score:.1f}%")
        
        print("="*80)
        
        print("\nDETAILED SECURITY FINDINGS:")
        for result in self.results:
            status_symbol = "[SECURE]" if result["status"] == "SECURE" else \
                           "[VULN]" if result["status"] == "VULNERABLE" else \
                           "[WARN]" if result["status"] == "WARNING" else "[ERROR]"
            print(f"{status_symbol} {result['test_name']} ({result['severity']})")
            if result["details"]:
                print(f"   Finding: {result['details']}")
            if result["recommendation"]:
                print(f"   Action: {result['recommendation']}")
            print()
        
        # Save detailed report
        report_data = {
            "security_scan": "Catalynx Security Testing",
            "execution_time": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "secure": secure_tests,
                "vulnerable": vulnerable_tests,
                "warnings": warning_tests,
                "errors": error_tests,
                "security_score": security_score if total_tests > 0 else 0
            },
            "risk_assessment": {
                "critical_issues": critical_issues,
                "high_risk_issues": high_issues,
                "medium_risk_issues": medium_issues
            },
            "detailed_findings": self.results
        }
        
        report_file = Path(__file__).parent / f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"Detailed security report saved: {report_file}")
        
        # Determine overall security status
        if critical_issues > 0:
            print("\n[CRITICAL] IMMEDIATE SECURITY ACTION REQUIRED")
            print("   Critical vulnerabilities found - address immediately")
            return False
        elif high_issues > 2:
            print("\n[HIGH RISK] SECURITY IMPROVEMENTS NEEDED")
            print("   Multiple high-risk issues - prioritize remediation")
            return False
        elif vulnerable_tests == 0:
            print("\n[SECURE] GOOD SECURITY POSTURE")
            print("   No major vulnerabilities detected")
            return True
        else:
            print("\n[MODERATE] SECURITY REVIEW RECOMMENDED")
            print("   Some vulnerabilities found - review and address")
            return True
    
    def run_security_tests(self):
        """Execute all security tests"""
        print("Starting Comprehensive Security Testing...")
        print("Testing OWASP Top 10 and DevOps Security Best Practices")
        print("="*80)
        
        # Execute all security tests
        self.test_api_security_headers()
        self.test_sql_injection_prevention()
        self.test_xss_prevention()
        self.test_input_validation()
        self.test_rate_limiting()
        self.test_authentication_security()
        self.test_data_privacy_protection()
        self.test_secure_configuration()
        
        # Generate comprehensive report
        return self.generate_security_report()

def main():
    """Main execution function"""
    security_tester = SecurityTestSuite()
    
    try:
        success = security_tester.run_security_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSecurity testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nSecurity testing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()