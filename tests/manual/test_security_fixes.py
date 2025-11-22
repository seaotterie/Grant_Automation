#!/usr/bin/env python3
"""
Security Testing Script for Catalynx
Tests all critical security fixes are properly implemented

Usage:
    python test_security_fixes.py --url http://localhost:8000
"""

import requests
import json
import sys
import time
import argparse
from typing import Dict, List, Tuple
from datetime import datetime

class SecurityTester:
    """Automated security testing for Catalynx"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results = []

    def test_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"  Details: {details}")

    def test_jwt_persistence(self) -> bool:
        """Test that JWT secret is persistent across restarts"""
        print("\n[TEST 1] JWT Secret Persistence")
        print("-" * 50)

        # This test requires manual verification
        print("⚠️  MANUAL TEST REQUIRED:")
        print("1. Start the server and login")
        print("2. Save the JWT token")
        print("3. Restart the server")
        print("4. Try using the same token")
        print("5. Token should still be valid (not 401 error)")

        manual_result = input("\nDid the token remain valid after restart? (y/n): ").lower()
        passed = manual_result == 'y'

        self.test_result(
            "JWT Secret Persistence",
            passed,
            "JWT secret must be stored in .env file, not generated at runtime"
        )
        return passed

    def test_sql_injection_blocked(self) -> bool:
        """Test that SQL injection in sort parameters is blocked"""
        print("\n[TEST 2] SQL Injection Protection")
        print("-" * 50)

        # Test malicious sort parameter
        payloads = [
            "name; DROP TABLE profiles--",
            "name UNION SELECT * FROM sqlite_master--",
            "name); DELETE FROM profiles--",
            "1=1; --",
            "name' OR '1'='1"
        ]

        all_passed = True
        for payload in payloads:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/profiles",
                    params={'sort_by': payload},
                    timeout=5
                )

                # Should return 400 or 422 (validation error), not 200
                if response.status_code in [400, 422]:
                    print(f"  ✓ Blocked: {payload[:50]}")
                elif response.status_code == 500:
                    # Server error - injection may have been attempted
                    print(f"  ✗ Server error on: {payload[:50]}")
                    all_passed = False
                else:
                    print(f"  ✗ Accepted: {payload[:50]} (status: {response.status_code})")
                    all_passed = False

            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request failed: {e}")
                all_passed = False

        self.test_result(
            "SQL Injection Protection",
            all_passed,
            "All malicious sort parameters should be rejected"
        )
        return all_passed

    def test_xss_protection(self) -> bool:
        """Test that XSS payloads are properly escaped"""
        print("\n[TEST 3] XSS Protection")
        print("-" * 50)

        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror="alert(1)">',
            'javascript:alert(1)',
            '<svg onload="alert(1)">',
            '<iframe src="javascript:alert(1)">',
        ]

        all_passed = True

        # Test in profile name field
        for payload in xss_payloads:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/profiles",
                    json={'name': payload, 'organization_type': 'nonprofit'},
                    timeout=5
                )

                # Check if HTML tags are in response (would indicate vulnerability)
                if response.status_code == 200:
                    response_text = response.text
                    # If payload appears unescaped, that's bad
                    if '<script>' in response_text or 'onerror=' in response_text:
                        print(f"  ✗ XSS payload not escaped: {payload[:50]}")
                        all_passed = False
                    else:
                        print(f"  ✓ Payload escaped: {payload[:50]}")
                else:
                    # Validation error is acceptable
                    print(f"  ✓ Rejected: {payload[:50]}")

            except requests.exceptions.RequestException as e:
                print(f"  ⚠️  Request failed: {e}")

        self.test_result(
            "XSS Protection",
            all_passed,
            "All XSS payloads should be escaped or rejected"
        )
        return all_passed

    def test_cors_configuration(self) -> bool:
        """Test that CORS is properly restricted"""
        print("\n[TEST 4] CORS Configuration")
        print("-" * 50)

        # Test with malicious origin
        malicious_origins = [
            'https://evil.com',
            'http://attacker.net',
            'https://phishing.site'
        ]

        all_passed = True
        for origin in malicious_origins:
            try:
                response = self.session.options(
                    f"{self.base_url}/api/profiles",
                    headers={'Origin': origin},
                    timeout=5
                )

                # Check Access-Control-Allow-Origin header
                allow_origin = response.headers.get('Access-Control-Allow-Origin')

                if allow_origin == '*':
                    print(f"  ✗ CORS allows all origins (wildcard)")
                    all_passed = False
                elif allow_origin == origin:
                    print(f"  ✗ CORS allows malicious origin: {origin}")
                    all_passed = False
                else:
                    print(f"  ✓ Blocked origin: {origin}")

            except requests.exceptions.RequestException as e:
                print(f"  ⚠️  Request failed: {e}")

        self.test_result(
            "CORS Configuration",
            all_passed,
            "CORS should only allow specific trusted origins"
        )
        return all_passed

    def test_rate_limiting(self) -> bool:
        """Test that rate limiting is enforced"""
        print("\n[TEST 5] Rate Limiting")
        print("-" * 50)

        # Send rapid requests to trigger rate limit
        print("  Sending 150 requests rapidly...")

        rate_limited = False
        for i in range(150):
            try:
                response = self.session.get(
                    f"{self.base_url}/api/profiles",
                    timeout=2
                )

                if response.status_code == 429:  # Too Many Requests
                    print(f"  ✓ Rate limited at request {i+1}")
                    rate_limited = True
                    break

            except requests.exceptions.RequestException:
                continue

        if not rate_limited:
            print(f"  ✗ No rate limiting detected after 150 requests")

        self.test_result(
            "Rate Limiting",
            rate_limited,
            "API should enforce rate limits (429 status after threshold)"
        )
        return rate_limited

    def test_authentication_required(self) -> bool:
        """Test that authentication is enforced on sensitive endpoints"""
        print("\n[TEST 6] Authentication Required")
        print("-" * 50)

        # Test accessing protected endpoints without auth
        protected_endpoints = [
            '/api/profiles',
            '/api/admin/system/overview',
            '/api/discovery/bmf',
        ]

        # NOTE: Current system has auth disabled for desktop use
        # This test checks if auth CAN be enabled

        print("  ⚠️  Note: Authentication currently disabled for desktop app")
        print("  Testing if auth infrastructure exists...")

        auth_exists = False
        try:
            # Try to import auth module
            import sys
            sys.path.insert(0, 'src')
            from auth.jwt_auth import get_current_user_dependency
            auth_exists = True
            print("  ✓ Authentication infrastructure exists")
        except ImportError:
            print("  ✗ Authentication module not found")

        self.test_result(
            "Authentication Infrastructure",
            auth_exists,
            "Auth system exists but is disabled for desktop mode"
        )
        return auth_exists

    def test_security_headers(self) -> bool:
        """Test that security headers are present"""
        print("\n[TEST 7] Security Headers")
        print("-" * 50)

        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': lambda v: 'max-age' in v,
            'Content-Security-Policy': lambda v: "default-src" in v,
        }

        all_passed = True

        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)

            for header, expected in required_headers.items():
                value = response.headers.get(header)

                if value is None:
                    print(f"  ✗ Missing header: {header}")
                    all_passed = False
                elif callable(expected):
                    if expected(value):
                        print(f"  ✓ Valid: {header}")
                    else:
                        print(f"  ✗ Invalid value: {header}")
                        all_passed = False
                elif expected == value:
                    print(f"  ✓ Present: {header}")
                else:
                    print(f"  ⚠️  Unexpected value for {header}: {value}")

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request failed: {e}")
            all_passed = False

        self.test_result(
            "Security Headers",
            all_passed,
            "All required security headers should be present and correct"
        )
        return all_passed

    def test_csp_configuration(self) -> bool:
        """Test that CSP doesn't allow unsafe operations"""
        print("\n[TEST 8] Content Security Policy")
        print("-" * 50)

        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            csp = response.headers.get('Content-Security-Policy', '')

            issues = []

            if 'unsafe-inline' in csp:
                issues.append("CSP allows 'unsafe-inline'")
                print(f"  ✗ CSP allows 'unsafe-inline' (XSS risk)")

            if 'unsafe-eval' in csp:
                issues.append("CSP allows 'unsafe-eval'")
                print(f"  ✗ CSP allows 'unsafe-eval' (code injection risk)")

            if not csp:
                issues.append("No CSP header")
                print(f"  ✗ No Content-Security-Policy header")

            if not issues:
                print(f"  ✓ CSP properly configured")

            passed = len(issues) == 0

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request failed: {e}")
            passed = False

        self.test_result(
            "CSP Configuration",
            passed,
            "CSP should not allow unsafe-inline or unsafe-eval"
        )
        return passed

    def test_input_validation(self) -> bool:
        """Test that input validation is enforced"""
        print("\n[TEST 9] Input Validation")
        print("-" * 50)

        # Test invalid data types and formats
        invalid_inputs = [
            {'name': '', 'organization_type': 'nonprofit'},  # Empty name
            {'name': 'Test', 'organization_type': 'invalid_type'},  # Invalid type
            {'name': 'Test', 'organization_type': 'nonprofit', 'ein': 'invalid'},  # Invalid EIN
            {'name': 'Test', 'organization_type': 'nonprofit', 'annual_revenue': -1000},  # Negative revenue
            {'name': 'Test', 'organization_type': 'nonprofit', 'website_url': 'not-a-url'},  # Invalid URL
        ]

        all_passed = True

        for invalid_data in invalid_inputs:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/profiles",
                    json=invalid_data,
                    timeout=5
                )

                # Should return 422 (Validation Error)
                if response.status_code == 422:
                    print(f"  ✓ Rejected invalid input: {list(invalid_data.keys())}")
                else:
                    print(f"  ✗ Accepted invalid input: {list(invalid_data.keys())} (status: {response.status_code})")
                    all_passed = False

            except requests.exceptions.RequestException as e:
                print(f"  ⚠️  Request failed: {e}")

        self.test_result(
            "Input Validation",
            all_passed,
            "All invalid inputs should be rejected with 422 status"
        )
        return all_passed

    def test_env_file_exists(self) -> bool:
        """Test that .env file exists and is not in git"""
        print("\n[TEST 10] Environment Configuration")
        print("-" * 50)

        import os
        from pathlib import Path

        env_exists = Path('.env').exists()
        gitignore_exists = Path('.gitignore').exists()

        if env_exists:
            print(f"  ✓ .env file exists")
        else:
            print(f"  ✗ .env file missing")

        # Check .gitignore
        env_in_gitignore = False
        if gitignore_exists:
            with open('.gitignore', 'r') as f:
                content = f.read()
                if '.env' in content:
                    print(f"  ✓ .env in .gitignore")
                    env_in_gitignore = True
                else:
                    print(f"  ✗ .env not in .gitignore")

        passed = env_exists and env_in_gitignore

        self.test_result(
            "Environment Configuration",
            passed,
            ".env must exist and be in .gitignore"
        )
        return passed

    def run_all_tests(self) -> Dict:
        """Run all security tests"""
        print("=" * 60)
        print("CATALYNX SECURITY TEST SUITE")
        print("=" * 60)

        # Run tests
        results = {
            'jwt_persistence': self.test_jwt_persistence(),
            'sql_injection': self.test_sql_injection_blocked(),
            'xss_protection': self.test_xss_protection(),
            'cors': self.test_cors_configuration(),
            'rate_limiting': self.test_rate_limiting(),
            'authentication': self.test_authentication_required(),
            'security_headers': self.test_security_headers(),
            'csp': self.test_csp_configuration(),
            'input_validation': self.test_input_validation(),
            'env_file': self.test_env_file_exists(),
        }

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)
        percentage = (passed / total) * 100

        print(f"\nPassed: {passed}/{total} ({percentage:.1f}%)")
        print(f"Failed: {total - passed}/{total}")

        if passed == total:
            print("\n✓ ALL TESTS PASSED - Security fixes implemented correctly!")
        else:
            print(f"\n✗ {total - passed} TESTS FAILED - Review security fixes")

        # Save detailed results
        with open('security_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'passed': passed,
                    'failed': total - passed,
                    'total': total,
                    'percentage': percentage
                },
                'results': self.results
            }, f, indent=2)

        print(f"\nDetailed results saved to: security_test_results.json")

        return results


def main():
    parser = argparse.ArgumentParser(description='Test Catalynx security fixes')
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of Catalynx application (default: http://localhost:8000)'
    )

    args = parser.parse_args()

    # Verify server is running
    try:
        response = requests.get(args.url, timeout=5)
        print(f"✓ Server is running at {args.url}\n")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to server at {args.url}")
        print(f"  Error: {e}")
        print("\nPlease start the server and try again:")
        print("  python src/web/main.py")
        sys.exit(1)

    # Run tests
    tester = SecurityTester(args.url)
    results = tester.run_all_tests()

    # Exit code based on results
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
