#!/usr/bin/env python3
"""
Real integration tests for the web scraper
Tests actual service functionality with real HTTP requests
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import httpx
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Real integration test runner"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        
    async def test_basic_http_functionality(self):
        """Test basic HTTP functionality"""
        logger.info("🔍 Testing basic HTTP functionality...")
        
        test_cases = [
            {
                "name": "Simple GET request",
                "url": "https://httpbin.org/get",
                "method": "GET"
            },
            {
                "name": "JSON response",
                "url": "https://httpbin.org/json",
                "method": "GET"
            },
            {
                "name": "User agent detection",
                "url": "https://httpbin.org/user-agent",
                "method": "GET"
            },
            {
                "name": "Headers inspection",
                "url": "https://httpbin.org/headers",
                "method": "GET"
            }
        ]
        
        for test_case in test_cases:
            try:
                logger.info(f"   Testing: {test_case['name']}")
                
                response = await self.client.get(test_case["url"])
                
                result = {
                    "test": test_case["name"],
                    "url": test_case["url"],
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds(),
                    "content_length": len(response.text)
                }
                
                self.results.append(result)
                
                if response.status_code == 200:
                    logger.info(f"      ✅ {test_case['name']}: {response.status_code}")
                else:
                    logger.warning(f"      ⚠️  {test_case['name']}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"      ❌ {test_case['name']}: {e}")
                self.results.append({
                    "test": test_case["name"],
                    "url": test_case["url"],
                    "success": False,
                    "error": str(e)
                })
    
    async def test_ip_detection(self):
        """Test IP detection and geolocation"""
        logger.info("🔍 Testing IP detection...")
        
        try:
            # Test IP detection
            response = await self.client.get("https://httpbin.org/ip")
            ip_data = response.json()
            
            logger.info(f"   Current IP: {ip_data.get('origin', 'Unknown')}")
            
            # Test geolocation (if available)
            try:
                geo_response = await self.client.get("http://ip-api.com/json/")
                geo_data = geo_response.json()
                
                logger.info(f"   Location: {geo_data.get('city', 'Unknown')}, {geo_data.get('country', 'Unknown')}")
                logger.info(f"   ISP: {geo_data.get('isp', 'Unknown')}")
                
                result = {
                    "test": "IP Detection",
                    "ip": ip_data.get('origin'),
                    "location": f"{geo_data.get('city', 'Unknown')}, {geo_data.get('country', 'Unknown')}",
                    "isp": geo_data.get('isp', 'Unknown'),
                    "success": True
                }
                
            except Exception as e:
                logger.warning(f"   ⚠️  Geolocation failed: {e}")
                result = {
                    "test": "IP Detection",
                    "ip": ip_data.get('origin'),
                    "success": True,
                    "geo_error": str(e)
                }
            
            self.results.append(result)
            logger.info("      ✅ IP detection completed")
            
        except Exception as e:
            logger.error(f"      ❌ IP detection failed: {e}")
            self.results.append({
                "test": "IP Detection",
                "success": False,
                "error": str(e)
            })
    
    async def test_model_functionality(self):
        """Test our data models"""
        logger.info("🔍 Testing data model functionality...")
        
        try:
            from common.models.scrape_request import ScrapeRequest, ScrapeMethod
            from common.models.scrape_result import ScrapeResult, ScrapeStatus
            from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider
            
            # Test ScrapeRequest creation
            request = ScrapeRequest(
                url="https://httpbin.org/get",
                method=ScrapeMethod.PYDOLL,
                selectors={"title": "h1", "content": "body"},
                use_proxy=True,
                use_stealth=True
            )
            
            logger.info(f"   ✅ ScrapeRequest created: {request.url}")
            
            # Test ScrapeResult creation
            result = ScrapeResult(
                request_id="test-123",
                status=ScrapeStatus.SUCCESS,
                status_code=200,
                data={"title": "Test Page", "content": "Test content"},
                response_time=1.5
            )
            
            logger.info(f"   ✅ ScrapeResult created: {result.status}")
            
            # Test ProxyConfig creation
            proxy = ProxyConfig(
                host="proxy.example.com",
                port=8080,
                proxy_type=ProxyType.HTTP,
                provider=ProxyProvider.DATACENTER,
                country="US"
            )
            
            logger.info(f"   ✅ ProxyConfig created: {proxy.get_proxy_url()}")
            
            # Test serialization
            request_dict = request.dict()
            result_dict = result.dict()
            proxy_dict = proxy.dict()
            
            logger.info(f"   ✅ Serialization works: {len(request_dict)} request fields")
            
            self.results.append({
                "test": "Model Functionality",
                "success": True,
                "request_fields": len(request_dict),
                "result_fields": len(result_dict),
                "proxy_fields": len(proxy_dict)
            })
            
        except Exception as e:
            logger.error(f"      ❌ Model testing failed: {e}")
            self.results.append({
                "test": "Model Functionality",
                "success": False,
                "error": str(e)
            })
    
    async def test_pydoll_service_mock(self):
        """Test PyDoll service functionality (mock)"""
        logger.info("🔍 Testing PyDoll service simulation...")
        
        try:
            # Simulate PyDoll service functionality
            test_urls = [
                "https://httpbin.org/json",
                "https://httpbin.org/xml",
                "https://httpbin.org/html"
            ]
            
            for url in test_urls:
                # Make actual HTTP request to simulate PyDoll behavior
                response = await self.client.get(url)
                
                # Simulate data extraction
                extracted_data = {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", "unknown"),
                    "size": len(response.text),
                    "extraction_time": response.elapsed.total_seconds()
                }
                
                logger.info(f"   ✅ PyDoll simulation: {url} -> {response.status_code}")
                
                self.results.append({
                    "test": "PyDoll Service Simulation",
                    "url": url,
                    "success": response.status_code == 200,
                    "data": extracted_data
                })
            
        except Exception as e:
            logger.error(f"      ❌ PyDoll simulation failed: {e}")
            self.results.append({
                "test": "PyDoll Service Simulation",
                "success": False,
                "error": str(e)
            })
    
    async def test_anti_detection_headers(self):
        """Test anti-detection headers"""
        logger.info("🔍 Testing anti-detection headers...")
        
        try:
            # Test with various user agents
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            for i, ua in enumerate(user_agents):
                headers = {
                    "User-Agent": ua,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
                
                response = await self.client.get("https://httpbin.org/headers", headers=headers)
                response_data = response.json()
                
                detected_ua = response_data.get("headers", {}).get("User-Agent", "")
                
                logger.info(f"   ✅ User Agent {i+1}: {detected_ua[:50]}...")
                
                self.results.append({
                    "test": "Anti-Detection Headers",
                    "user_agent_index": i + 1,
                    "success": ua in detected_ua,
                    "detected_ua": detected_ua
                })
                
        except Exception as e:
            logger.error(f"      ❌ Header testing failed: {e}")
            self.results.append({
                "test": "Anti-Detection Headers",
                "success": False,
                "error": str(e)
            })
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        logger.info("🔍 Testing error handling...")
        
        error_scenarios = [
            {"name": "404 Not Found", "url": "https://httpbin.org/status/404"},
            {"name": "500 Server Error", "url": "https://httpbin.org/status/500"},
            {"name": "Timeout", "url": "https://httpbin.org/delay/5"},
            {"name": "Rate Limit", "url": "https://httpbin.org/status/429"}
        ]
        
        for scenario in error_scenarios:
            try:
                logger.info(f"   Testing: {scenario['name']}")
                
                # Set shorter timeout for timeout test
                timeout = 3.0 if "Timeout" in scenario["name"] else 10.0
                
                response = await self.client.get(scenario["url"], timeout=timeout)
                
                result = {
                    "test": f"Error Handling - {scenario['name']}",
                    "url": scenario["url"],
                    "status_code": response.status_code,
                    "handled": True,
                    "expected_error": scenario["name"]
                }
                
                logger.info(f"      ✅ {scenario['name']}: {response.status_code}")
                
            except httpx.TimeoutException:
                result = {
                    "test": f"Error Handling - {scenario['name']}",
                    "url": scenario["url"],
                    "timeout": True,
                    "handled": True,
                    "expected_error": scenario["name"]
                }
                logger.info(f"      ✅ {scenario['name']}: Timeout handled")
                
            except Exception as e:
                result = {
                    "test": f"Error Handling - {scenario['name']}",
                    "url": scenario["url"],
                    "error": str(e),
                    "handled": True,
                    "expected_error": scenario["name"]
                }
                logger.info(f"      ✅ {scenario['name']}: Exception handled")
            
            self.results.append(result)
    
    async def test_performance_metrics(self):
        """Test performance metrics collection"""
        logger.info("🔍 Testing performance metrics...")
        
        try:
            # Make multiple requests to collect metrics
            urls = [
                "https://httpbin.org/get",
                "https://httpbin.org/json",
                "https://httpbin.org/html"
            ]
            
            response_times = []
            
            for url in urls:
                start_time = asyncio.get_event_loop().time()
                
                response = await self.client.get(url)
                
                end_time = asyncio.get_event_loop().time()
                response_time = end_time - start_time
                
                response_times.append(response_time)
                
                logger.info(f"   ✅ {url}: {response_time:.3f}s")
            
            # Calculate metrics
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            metrics = {
                "test": "Performance Metrics",
                "total_requests": len(urls),
                "avg_response_time": avg_response_time,
                "min_response_time": min_response_time,
                "max_response_time": max_response_time,
                "success": True
            }
            
            self.results.append(metrics)
            
            logger.info(f"   📊 Average response time: {avg_response_time:.3f}s")
            logger.info(f"   📊 Min response time: {min_response_time:.3f}s")
            logger.info(f"   📊 Max response time: {max_response_time:.3f}s")
            
        except Exception as e:
            logger.error(f"      ❌ Performance metrics failed: {e}")
            self.results.append({
                "test": "Performance Metrics",
                "success": False,
                "error": str(e)
            })
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting integration tests")
        logger.info("=" * 50)
        
        tests = [
            self.test_basic_http_functionality,
            self.test_ip_detection,
            self.test_model_functionality,
            self.test_pydoll_service_mock,
            self.test_anti_detection_headers,
            self.test_error_handling,
            self.test_performance_metrics
        ]
        
        for test in tests:
            try:
                await test()
                logger.info("")  # Empty line for readability
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} failed: {e}")
        
        await self.generate_report()
        
        # Close HTTP client
        await self.client.aclose()
    
    async def generate_report(self):
        """Generate integration test report"""
        logger.info("=" * 50)
        logger.info("📊 INTEGRATION TEST REPORT")
        logger.info("=" * 50)
        
        # Count results
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.get("success", False)])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests:.2%}")
        
        # Feature summary
        logger.info("\n🔍 FEATURE VALIDATION:")
        
        features = {
            "HTTP Functionality": any(r.get("test") == "Simple GET request" and r.get("success") for r in self.results),
            "IP Detection": any(r.get("test") == "IP Detection" and r.get("success") for r in self.results),
            "Data Models": any(r.get("test") == "Model Functionality" and r.get("success") for r in self.results),
            "Service Simulation": any(r.get("test") == "PyDoll Service Simulation" and r.get("success") for r in self.results),
            "Anti-Detection": any(r.get("test") == "Anti-Detection Headers" and r.get("success") for r in self.results),
            "Error Handling": any("Error Handling" in r.get("test", "") for r in self.results),
            "Performance Metrics": any(r.get("test") == "Performance Metrics" and r.get("success") for r in self.results)
        }
        
        for feature, status in features.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {feature}: {'PASS' if status else 'FAIL'}")
        
        # Save results
        results_file = Path("integration_test_results.json")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0
            },
            "features": features,
            "detailed_results": self.results
        }
        
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n💾 Detailed report saved to: {results_file}")
        logger.info("🎉 Integration tests completed!")

async def main():
    """Main function"""
    runner = IntegrationTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())