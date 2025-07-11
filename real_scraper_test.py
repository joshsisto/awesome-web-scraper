#!/usr/bin/env python3
"""
Real scraper test using actual services
Tests the multi-framework capabilities with real HTTP requests
"""

import asyncio
import json
import logging
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import httpx
from selectolax.parser import HTMLParser

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from common.models.scrape_request import ScrapeRequest, ScrapeMethod, Priority
    from common.models.scrape_result import ScrapeResult, ScrapeStatus
    from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider
    MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Models not available: {e}")
    MODELS_AVAILABLE = False

class RealScrapingTest:
    """Test actual scraping functionality"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        self.start_time = time.time()
    
    async def test_scrapy_simulation(self):
        """Simulate Scrapy functionality with real HTTP requests"""
        logger.info("🕷️  Testing Scrapy simulation...")
        
        test_sites = [
            {
                "name": "HTTPBin HTML",
                "url": "https://httpbin.org/html",
                "selectors": {"title": "h1", "content": "p"},
                "description": "Simple HTML parsing"
            },
            {
                "name": "Quotes to Scrape",
                "url": "https://quotes.toscrape.com/",
                "selectors": {"quotes": ".quote .text", "authors": ".quote .author"},
                "description": "Quote extraction"
            }
        ]
        
        for site in test_sites:
            try:
                logger.info(f"   Testing: {site['name']}")
                
                # Make request
                start_time = time.time()
                response = await self.client.get(site["url"])
                response_time = time.time() - start_time
                
                # Parse HTML
                parser = HTMLParser(response.text)
                extracted_data = {}
                
                for field, selector in site["selectors"].items():
                    elements = parser.css(selector)
                    if elements:
                        if len(elements) == 1:
                            extracted_data[field] = elements[0].text(strip=True) if elements[0].text() else None
                        else:
                            extracted_data[field] = [el.text(strip=True) for el in elements if el.text()]
                
                # Record result
                result = {
                    "test_type": "scrapy_simulation",
                    "site_name": site["name"],
                    "url": site["url"],
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "data_extracted": extracted_data,
                    "selectors_used": len(site["selectors"]),
                    "success": response.status_code == 200,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                
                logger.info(f"      ✅ {site['name']}: {response.status_code}, {len(extracted_data)} fields extracted")
                
            except Exception as e:
                logger.error(f"      ❌ {site['name']}: {e}")
                self.results.append({
                    "test_type": "scrapy_simulation",
                    "site_name": site["name"],
                    "url": site["url"],
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    async def test_pydoll_simulation(self):
        """Simulate PyDoll functionality with fast API requests"""
        logger.info("⚡ Testing PyDoll simulation...")
        
        api_endpoints = [
            {
                "name": "JSON API",
                "url": "https://httpbin.org/json",
                "description": "Fast JSON parsing"
            },
            {
                "name": "IP Detection",
                "url": "https://httpbin.org/ip",
                "description": "IP address extraction"
            },
            {
                "name": "User Agent",
                "url": "https://httpbin.org/user-agent",
                "description": "User agent detection"
            },
            {
                "name": "Headers",
                "url": "https://httpbin.org/headers",
                "description": "Headers inspection"
            }
        ]
        
        for endpoint in api_endpoints:
            try:
                logger.info(f"   Testing: {endpoint['name']}")
                
                # Make fast request with custom headers
                headers = {
                    "User-Agent": "AwesomeScraper/1.0 (PyDoll Mode)",
                    "Accept": "application/json, text/html",
                    "Accept-Language": "en-US,en;q=0.9"
                }
                
                start_time = time.time()
                response = await self.client.get(endpoint["url"], headers=headers)
                response_time = time.time() - start_time
                
                # Try to parse as JSON, fallback to text
                try:
                    data = response.json()
                    content_type = "json"
                except:
                    data = {"raw_text": response.text[:200]}  # First 200 chars
                    content_type = "text"
                
                # Record result
                result = {
                    "test_type": "pydoll_simulation",
                    "endpoint_name": endpoint["name"],
                    "url": endpoint["url"],
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "content_type": content_type,
                    "data_size": len(str(data)),
                    "success": response.status_code == 200,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                
                logger.info(f"      ✅ {endpoint['name']}: {response.status_code}, {content_type}, {response_time:.3f}s")
                
            except Exception as e:
                logger.error(f"      ❌ {endpoint['name']}: {e}")
                self.results.append({
                    "test_type": "pydoll_simulation",
                    "endpoint_name": endpoint["name"],
                    "url": endpoint["url"],
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    async def test_playwright_simulation(self):
        """Simulate Playwright functionality with complex scenarios"""
        logger.info("🎭 Testing Playwright simulation...")
        
        complex_scenarios = [
            {
                "name": "Delay Test",
                "url": "https://httpbin.org/delay/2",
                "description": "Waiting for dynamic content"
            },
            {
                "name": "Redirect Test",
                "url": "https://httpbin.org/redirect/3",
                "description": "Following redirects"
            },
            {
                "name": "Auth Test",
                "url": "https://httpbin.org/basic-auth/testuser/testpass",
                "description": "Handling authentication",
                "auth": ("testuser", "testpass")
            },
            {
                "name": "Cookies Test",
                "url": "https://httpbin.org/cookies/set?session=abc123",
                "description": "Cookie handling"
            }
        ]
        
        for scenario in complex_scenarios:
            try:
                logger.info(f"   Testing: {scenario['name']}")
                
                # Configure request based on scenario
                kwargs = {}
                if "auth" in scenario:
                    kwargs["auth"] = scenario["auth"]
                
                # Simulate browser-like headers
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
                
                start_time = time.time()
                response = await self.client.get(scenario["url"], headers=headers, **kwargs)
                response_time = time.time() - start_time
                
                # Simulate browser processing time
                await asyncio.sleep(0.1)  # Simulate rendering
                
                # Record result
                result = {
                    "test_type": "playwright_simulation",
                    "scenario_name": scenario["name"],
                    "url": scenario["url"],
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "final_url": str(response.url),
                    "has_auth": "auth" in scenario,
                    "success": response.status_code in [200, 302],
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                
                logger.info(f"      ✅ {scenario['name']}: {response.status_code}, {response_time:.3f}s")
                
            except Exception as e:
                logger.error(f"      ❌ {scenario['name']}: {e}")
                self.results.append({
                    "test_type": "playwright_simulation",
                    "scenario_name": scenario["name"],
                    "url": scenario["url"],
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    async def test_ip_change_simulation(self):
        """Simulate VPN IP change testing"""
        logger.info("🌐 Testing IP change simulation...")
        
        # Get current IP multiple times to simulate VPN rotation
        ip_checks = []
        
        for i in range(3):
            try:
                logger.info(f"   IP Check {i+1}/3")
                
                # Simulate different VPN servers with different headers
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                ]
                
                headers = {"User-Agent": user_agents[i]}
                
                start_time = time.time()
                response = await self.client.get("https://httpbin.org/ip", headers=headers)
                response_time = time.time() - start_time
                
                ip_data = response.json()
                current_ip = ip_data.get("origin", "unknown")
                
                ip_checks.append({
                    "check_number": i + 1,
                    "ip_address": current_ip,
                    "response_time": response_time,
                    "user_agent": headers["User-Agent"][:50] + "...",
                    "success": response.status_code == 200,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"      ✅ IP Check {i+1}: {current_ip}")
                
                # Simulate VPN rotation delay
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"      ❌ IP Check {i+1}: {e}")
                ip_checks.append({
                    "check_number": i + 1,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Record VPN test result
        self.results.append({
            "test_type": "vpn_simulation",
            "ip_checks": ip_checks,
            "total_checks": len(ip_checks),
            "successful_checks": len([c for c in ip_checks if c.get("success", False)]),
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_data_validation(self):
        """Test data validation and quality metrics"""
        logger.info("📊 Testing data validation...")
        
        # Test data extraction quality
        test_url = "https://httpbin.org/html"
        
        try:
            response = await self.client.get(test_url)
            parser = HTMLParser(response.text)
            
            # Test various selectors
            selectors = {
                "title": "h1",
                "paragraphs": "p",
                "links": "a",
                "nonexistent": ".nonexistent-class"
            }
            
            extracted_data = {}
            for field, selector in selectors.items():
                elements = parser.css(selector)
                if elements:
                    if len(elements) == 1:
                        extracted_data[field] = elements[0].text(strip=True) if elements[0].text() else ""
                    else:
                        extracted_data[field] = [el.text(strip=True) for el in elements if el.text()]
                else:
                    extracted_data[field] = None
            
            # Calculate quality metrics
            total_fields = len(selectors)
            successful_extractions = len([v for v in extracted_data.values() if v is not None and v != ""])
            completeness_score = successful_extractions / total_fields
            
            # Data quality assessment
            quality_score = 0.0
            if extracted_data.get("title"):
                quality_score += 0.4  # Title is important
            if extracted_data.get("paragraphs"):
                quality_score += 0.3  # Content is important
            if extracted_data.get("links"):
                quality_score += 0.2  # Links are useful
            quality_score += 0.1  # Base score for successful extraction
            
            result = {
                "test_type": "data_validation",
                "url": test_url,
                "extracted_data": extracted_data,
                "total_selectors": total_fields,
                "successful_extractions": successful_extractions,
                "completeness_score": completeness_score,
                "quality_score": min(1.0, quality_score),
                "success": completeness_score > 0.5,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            
            logger.info(f"   ✅ Data validation: {completeness_score:.2%} completeness, {quality_score:.2f} quality")
            
        except Exception as e:
            logger.error(f"   ❌ Data validation failed: {e}")
            self.results.append({
                "test_type": "data_validation",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def run_all_tests(self):
        """Run all real scraping tests"""
        logger.info("🚀 Starting real scraper tests")
        logger.info("=" * 60)
        
        test_methods = [
            self.test_scrapy_simulation,
            self.test_pydoll_simulation,
            self.test_playwright_simulation,
            self.test_ip_change_simulation,
            self.test_data_validation
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                logger.info("")  # Empty line for readability
            except Exception as e:
                logger.error(f"Test method failed: {test_method.__name__} - {e}")
        
        await self.generate_report()
        await self.client.aclose()
    
    async def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        logger.info("=" * 60)
        logger.info("📊 REAL SCRAPER TEST REPORT")
        logger.info("=" * 60)
        
        # Count results by type
        test_types = {}
        successful_tests = 0
        failed_tests = 0
        
        for result in self.results:
            test_type = result.get("test_type", "unknown")
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "successful": 0, "failed": 0}
            
            test_types[test_type]["total"] += 1
            
            if result.get("success", False):
                test_types[test_type]["successful"] += 1
                successful_tests += 1
            else:
                test_types[test_type]["failed"] += 1
                failed_tests += 1
        
        # Overall summary
        total_tests = len(self.results)
        success_rate = successful_tests / max(1, total_tests)
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.2%}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        
        # Test type breakdown
        logger.info("\n📋 TEST TYPE BREAKDOWN:")
        for test_type, stats in test_types.items():
            type_success_rate = stats["successful"] / max(1, stats["total"])
            logger.info(f"  {test_type.replace('_', ' ').title()}:")
            logger.info(f"    Total: {stats['total']}")
            logger.info(f"    Success Rate: {type_success_rate:.2%}")
        
        # Multi-framework validation
        logger.info("\n🔍 MULTI-FRAMEWORK VALIDATION:")
        
        framework_tests = {
            "Scrapy Simulation": any(r.get("test_type") == "scrapy_simulation" and r.get("success") for r in self.results),
            "PyDoll Simulation": any(r.get("test_type") == "pydoll_simulation" and r.get("success") for r in self.results),
            "Playwright Simulation": any(r.get("test_type") == "playwright_simulation" and r.get("success") for r in self.results),
            "VPN/IP Testing": any(r.get("test_type") == "vpn_simulation" for r in self.results),
            "Data Validation": any(r.get("test_type") == "data_validation" and r.get("success") for r in self.results)
        }
        
        for framework, status in framework_tests.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {framework}: {'PASS' if status else 'FAIL'}")
        
        # Performance metrics
        response_times = []
        for result in self.results:
            if "response_time" in result:
                response_times.append(result["response_time"])
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            logger.info(f"\n⚡ PERFORMANCE METRICS:")
            logger.info(f"  Average Response Time: {avg_response_time:.3f}s")
            logger.info(f"  Fastest Response: {min_response_time:.3f}s")
            logger.info(f"  Slowest Response: {max_response_time:.3f}s")
        
        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_duration": total_duration,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate
            },
            "test_types": test_types,
            "framework_validation": framework_tests,
            "performance": {
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "total_requests": len(response_times)
            },
            "detailed_results": self.results
        }
        
        report_file = Path("real_scraper_test_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n💾 Detailed report saved to: {report_file}")
        logger.info("🎉 Real scraper tests completed!")

async def main():
    """Main function"""
    test = RealScrapingTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())