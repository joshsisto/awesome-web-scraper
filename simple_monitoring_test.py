#!/usr/bin/env python3
"""
Simple monitoring and logging test without external dependencies
"""

import asyncio
import json
import logging
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleMetricsCollector:
    """Simple metrics collector for testing"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "response_times": [],
            "error_types": {},
            "proxy_usage": {},
            "method_usage": {},
            "status_codes": {},
            "start_time": time.time()
        }
    
    def record_request(self, method: str, status_code: int, response_time: float, 
                      proxy_used: str = None, error_type: str = None):
        """Record request metrics"""
        self.metrics["requests_total"] += 1
        
        if 200 <= status_code < 300:
            self.metrics["requests_successful"] += 1
        else:
            self.metrics["requests_failed"] += 1
        
        self.metrics["response_times"].append(response_time)
        
        # Track status codes
        self.metrics["status_codes"][str(status_code)] = \
            self.metrics["status_codes"].get(str(status_code), 0) + 1
        
        # Track methods
        self.metrics["method_usage"][method] = \
            self.metrics["method_usage"].get(method, 0) + 1
        
        # Track proxy usage
        if proxy_used:
            self.metrics["proxy_usage"][proxy_used] = \
                self.metrics["proxy_usage"].get(proxy_used, 0) + 1
        
        # Track error types
        if error_type:
            self.metrics["error_types"][error_type] = \
                self.metrics["error_types"].get(error_type, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        response_times = self.metrics["response_times"]
        uptime = time.time() - self.metrics["start_time"]
        
        summary = {
            "uptime_seconds": uptime,
            "total_requests": self.metrics["requests_total"],
            "successful_requests": self.metrics["requests_successful"],
            "failed_requests": self.metrics["requests_failed"],
            "success_rate": self.metrics["requests_successful"] / max(1, self.metrics["requests_total"]),
            "requests_per_second": self.metrics["requests_total"] / max(1, uptime),
            "avg_response_time": sum(response_times) / max(1, len(response_times)),
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "status_codes": dict(self.metrics["status_codes"]),
            "method_usage": dict(self.metrics["method_usage"]),
            "proxy_usage": dict(self.metrics["proxy_usage"]),
            "error_types": dict(self.metrics["error_types"])
        }
        
        return summary

class SimpleLoggingTest:
    """Simple logging test"""
    
    def __init__(self):
        self.logger = logger
        self.log_entries = []
        self.metrics = SimpleMetricsCollector()
    
    async def test_basic_logging(self):
        """Test basic logging functionality"""
        logger.info("🔍 Testing basic logging functionality...")
        
        # Test different log levels
        log_tests = [
            {"level": "debug", "message": "Debug message for development"},
            {"level": "info", "message": "Information about scraping progress"},
            {"level": "warning", "message": "Warning about rate limiting"},
            {"level": "error", "message": "Error during data extraction"},
        ]
        
        for log_test in log_tests:
            if log_test["level"] == "debug":
                self.logger.debug(log_test["message"])
            elif log_test["level"] == "info":
                self.logger.info(log_test["message"])
            elif log_test["level"] == "warning":
                self.logger.warning(log_test["message"])
            elif log_test["level"] == "error":
                self.logger.error(log_test["message"])
            
            self.log_entries.append({
                "timestamp": datetime.now().isoformat(),
                "level": log_test["level"],
                "message": log_test["message"]
            })
        
        logger.info(f"   ✅ Basic logging: {len(self.log_entries)} entries created")
    
    async def test_request_logging(self):
        """Test request-specific logging"""
        logger.info("🔍 Testing request logging...")
        
        # Simulate various scraping requests
        requests = [
            {"method": "scrapy", "url": "https://example.com/products", "status": 200, "time": 0.5},
            {"method": "pydoll", "url": "https://api.example.com/data", "status": 200, "time": 0.3},
            {"method": "playwright", "url": "https://spa.example.com", "status": 200, "time": 2.1},
            {"method": "scrapy", "url": "https://example.com/timeout", "status": 408, "time": 5.0},
            {"method": "pydoll", "url": "https://api.example.com/notfound", "status": 404, "time": 0.2}
        ]
        
        for req in requests:
            # Log request start
            self.logger.info(f"Starting {req['method']} request to {req['url']}")
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            # Record metrics
            self.metrics.record_request(
                method=req["method"],
                status_code=req["status"],
                response_time=req["time"],
                proxy_used=f"proxy-{req['method']}.example.com:8080",
                error_type="timeout" if req["status"] == 408 else ("not_found" if req["status"] == 404 else None)
            )
            
            # Log request completion
            if req["status"] == 200:
                self.logger.info(f"✅ {req['method']} request completed: {req['status']} in {req['time']}s")
            else:
                self.logger.warning(f"⚠️  {req['method']} request failed: {req['status']} in {req['time']}s")
            
            self.log_entries.append({
                "timestamp": datetime.now().isoformat(),
                "request_method": req["method"],
                "url": req["url"],
                "status_code": req["status"],
                "response_time": req["time"]
            })
        
        logger.info(f"   ✅ Request logging: {len(requests)} requests processed")
    
    async def test_error_logging(self):
        """Test error logging"""
        logger.info("🔍 Testing error logging...")
        
        # Simulate various error scenarios
        error_scenarios = [
            {"type": "ConnectionError", "message": "Failed to connect to proxy server"},
            {"type": "TimeoutError", "message": "Request timed out after 30 seconds"},
            {"type": "ParseError", "message": "Failed to parse HTML content"},
            {"type": "ValidationError", "message": "Invalid data format received"}
        ]
        
        for scenario in error_scenarios:
            self.logger.error(f"Error occurred: {scenario['type']} - {scenario['message']}")
            
            self.log_entries.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": scenario["type"],
                "error_message": scenario["message"],
                "component": "error_handler"
            })
        
        logger.info(f"   ✅ Error logging: {len(error_scenarios)} errors logged")
    
    async def test_performance_logging(self):
        """Test performance monitoring"""
        logger.info("🔍 Testing performance monitoring...")
        
        # Get current metrics
        metrics = self.metrics.get_summary()
        
        # Log performance metrics
        self.logger.info(f"Performance Summary:")
        self.logger.info(f"  Total Requests: {metrics['total_requests']}")
        self.logger.info(f"  Success Rate: {metrics['success_rate']:.2%}")
        self.logger.info(f"  Avg Response Time: {metrics['avg_response_time']:.3f}s")
        self.logger.info(f"  Requests/Second: {metrics['requests_per_second']:.2f}")
        
        # Log method distribution
        if metrics['method_usage']:
            self.logger.info("Method Usage:")
            for method, count in metrics['method_usage'].items():
                percentage = (count / metrics['total_requests']) * 100
                self.logger.info(f"  {method}: {count} ({percentage:.1f}%)")
        
        # Log status code distribution
        if metrics['status_codes']:
            self.logger.info("Status Code Distribution:")
            for code, count in metrics['status_codes'].items():
                percentage = (count / metrics['total_requests']) * 100
                self.logger.info(f"  {code}: {count} ({percentage:.1f}%)")
        
        logger.info("   ✅ Performance monitoring: Metrics logged")
    
    async def run_all_tests(self):
        """Run all logging tests"""
        logger.info("🚀 Starting logging and monitoring tests")
        logger.info("=" * 50)
        
        test_methods = [
            self.test_basic_logging,
            self.test_request_logging,
            self.test_error_logging,
            self.test_performance_logging
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                logger.info("")  # Empty line for readability
            except Exception as e:
                logger.error(f"Test failed: {test_method.__name__} - {e}")
        
        # Generate summary
        await self.generate_summary()
    
    async def generate_summary(self):
        """Generate test summary"""
        metrics_summary = self.metrics.get_summary()
        
        logger.info("=" * 50)
        logger.info("📊 LOGGING & MONITORING TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Log Entries: {len(self.log_entries)}")
        logger.info(f"Test Duration: {metrics_summary['uptime_seconds']:.2f}s")
        logger.info(f"Simulated Requests: {metrics_summary['total_requests']}")
        logger.info(f"Success Rate: {metrics_summary['success_rate']:.2%}")
        
        # Feature validation
        features = {
            "Basic Logging": len(self.log_entries) > 0,
            "Request Tracking": metrics_summary['total_requests'] > 0,
            "Error Handling": len(metrics_summary['error_types']) > 0,
            "Performance Metrics": metrics_summary['avg_response_time'] > 0,
            "Method Distribution": len(metrics_summary['method_usage']) > 0,
            "Status Code Tracking": len(metrics_summary['status_codes']) > 0
        }
        
        logger.info("\n🔍 FEATURE VALIDATION:")
        for feature, status in features.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {feature}: {'PASS' if status else 'FAIL'}")
        
        # Save detailed results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_log_entries": len(self.log_entries),
                "test_duration": metrics_summary['uptime_seconds'],
                "features_tested": list(features.keys()),
                "features_passed": len([f for f in features.values() if f])
            },
            "metrics_summary": metrics_summary,
            "feature_validation": features,
            "log_entries": self.log_entries
        }
        
        results_file = Path("simple_monitoring_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n💾 Results saved to: {results_file}")
        logger.info("🎉 Logging and monitoring tests completed!")

async def main():
    """Main function"""
    test = SimpleLoggingTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())