#!/usr/bin/env python3
"""
Monitoring and logging test for the web scraper
Tests metrics collection, logging, and health monitoring
"""

import asyncio
import json
import logging
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import structlog

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

class MetricsCollector:
    """Mock metrics collector for testing"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "response_times": [],
            "error_types": {},
            "proxy_usage": {},
            "method_usage": {},
            "status_codes": {}
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
        
        summary = {
            "total_requests": self.metrics["requests_total"],
            "successful_requests": self.metrics["requests_successful"],
            "failed_requests": self.metrics["requests_failed"],
            "success_rate": self.metrics["requests_successful"] / max(1, self.metrics["requests_total"]),
            "avg_response_time": sum(response_times) / max(1, len(response_times)),
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "status_codes": dict(self.metrics["status_codes"]),
            "method_usage": dict(self.metrics["method_usage"]),
            "proxy_usage": dict(self.metrics["proxy_usage"]),
            "error_types": dict(self.metrics["error_types"])
        }
        
        return summary

class LoggingTest:
    """Test logging functionality"""
    
    def __init__(self):
        self.logger = logger.bind(service="logging_test")
        self.log_entries = []
        self.metrics = MetricsCollector()
    
    async def test_structured_logging(self):
        """Test structured logging"""
        self.logger.info("Testing structured logging", test_type="structured_logging")
        
        # Test different log levels
        log_tests = [
            {"level": "debug", "message": "Debug message", "extra": {"debug_data": "test"}},
            {"level": "info", "message": "Info message", "extra": {"info_data": "test"}},
            {"level": "warning", "message": "Warning message", "extra": {"warning_data": "test"}},
            {"level": "error", "message": "Error message", "extra": {"error_data": "test"}},
        ]
        
        for log_test in log_tests:
            getattr(self.logger, log_test["level"])(
                log_test["message"],
                **log_test["extra"]
            )
            
            self.log_entries.append({
                "timestamp": datetime.now().isoformat(),
                "level": log_test["level"],
                "message": log_test["message"],
                "extra": log_test["extra"]
            })
        
        self.logger.info("Structured logging test completed", 
                        log_entries_created=len(self.log_entries))
    
    async def test_context_logging(self):
        """Test context-aware logging"""
        # Create context logger
        context_logger = self.logger.bind(
            request_id="req-123",
            user_id="user-456",
            session_id="sess-789"
        )
        
        context_logger.info("Processing request", action="start_processing")
        
        # Simulate processing steps
        processing_steps = [
            {"step": "validate_request", "duration": 0.1},
            {"step": "extract_data", "duration": 0.5},
            {"step": "process_data", "duration": 0.3},
            {"step": "save_results", "duration": 0.2}
        ]
        
        for step in processing_steps:
            await asyncio.sleep(0.1)  # Simulate processing time
            
            context_logger.info(
                "Processing step completed",
                step=step["step"],
                duration=step["duration"],
                status="success"
            )
            
            self.log_entries.append({
                "timestamp": datetime.now().isoformat(),
                "step": step["step"],
                "duration": step["duration"],
                "context": "request_processing"
            })
        
        context_logger.info("Request processing completed", 
                           total_steps=len(processing_steps),
                           status="success")
    
    async def test_error_logging(self):
        """Test error logging and stack traces"""
        error_logger = self.logger.bind(component="error_handler")
        
        # Test different error scenarios
        error_scenarios = [
            {"type": "validation_error", "message": "Invalid input data"},
            {"type": "network_error", "message": "Connection timeout"},
            {"type": "parsing_error", "message": "Failed to parse HTML"},
            {"type": "auth_error", "message": "Authentication failed"}
        ]
        
        for scenario in error_scenarios:
            try:
                # Simulate error condition
                if scenario["type"] == "validation_error":
                    raise ValueError(scenario["message"])
                elif scenario["type"] == "network_error":
                    raise ConnectionError(scenario["message"])
                elif scenario["type"] == "parsing_error":
                    raise RuntimeError(scenario["message"])
                elif scenario["type"] == "auth_error":
                    raise PermissionError(scenario["message"])
                    
            except Exception as e:
                error_logger.error(
                    "Error occurred during processing",
                    error_type=scenario["type"],
                    error_message=str(e),
                    exc_info=True
                )
                
                self.log_entries.append({
                    "timestamp": datetime.now().isoformat(),
                    "error_type": scenario["type"],
                    "error_message": str(e),
                    "handled": True
                })
    
    async def test_performance_logging(self):
        """Test performance monitoring and logging"""
        perf_logger = self.logger.bind(component="performance_monitor")
        
        # Simulate various request scenarios
        request_scenarios = [
            {"method": "scrapy", "url": "https://example.com", "expected_time": 0.5},
            {"method": "pydoll", "url": "https://api.example.com", "expected_time": 0.3},
            {"method": "playwright", "url": "https://spa.example.com", "expected_time": 2.0}
        ]
        
        for scenario in request_scenarios:
            start_time = time.time()
            
            # Simulate request processing
            await asyncio.sleep(scenario["expected_time"] * 0.1)  # Faster for testing
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Record metrics
            status_code = 200 if scenario["method"] != "playwright" else 201
            self.metrics.record_request(
                method=scenario["method"],
                status_code=status_code,
                response_time=duration,
                proxy_used=f"proxy-{scenario['method']}.example.com:8080"
            )
            
            perf_logger.info(
                "Request completed",
                method=scenario["method"],
                url=scenario["url"],
                response_time=duration,
                status_code=status_code,
                performance_ok=duration < 1.0
            )
    
    async def run_all_tests(self):
        """Run all logging tests"""
        self.logger.info("Starting logging and monitoring tests")
        
        test_methods = [
            self.test_structured_logging,
            self.test_context_logging,
            self.test_error_logging,
            self.test_performance_logging
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                self.logger.info(f"Test completed: {test_method.__name__}")
            except Exception as e:
                self.logger.error(f"Test failed: {test_method.__name__}", error=str(e))
        
        # Generate summary
        await self.generate_logging_summary()
    
    async def generate_logging_summary(self):
        """Generate logging test summary"""
        metrics_summary = self.metrics.get_summary()
        
        summary_logger = self.logger.bind(component="test_summary")
        
        summary_logger.info(
            "Logging test summary",
            total_log_entries=len(self.log_entries),
            metrics=metrics_summary,
            test_duration=time.time(),
            status="completed"
        )
        
        # Save detailed results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_log_entries": len(self.log_entries),
                "test_types": ["structured", "context", "error", "performance"],
                "status": "completed"
            },
            "metrics_summary": metrics_summary,
            "log_entries": self.log_entries
        }
        
        results_file = Path("logging_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Logging test results saved to: {results_file}")

class HealthMonitoringTest:
    """Test health monitoring functionality"""
    
    def __init__(self):
        self.logger = logger.bind(service="health_monitor")
        self.health_checks = {}
        self.alerts = []
    
    async def test_service_health_checks(self):
        """Test service health monitoring"""
        self.logger.info("Testing service health checks")
        
        services = [
            {"name": "extraction_service", "status": "healthy", "response_time": 0.05},
            {"name": "proxy_service", "status": "healthy", "response_time": 0.02},
            {"name": "storage_service", "status": "degraded", "response_time": 0.15},
            {"name": "vpn_service", "status": "healthy", "response_time": 0.03}
        ]
        
        for service in services:
            # Simulate health check
            await asyncio.sleep(0.1)
            
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "service": service["name"],
                "status": service["status"],
                "response_time": service["response_time"],
                "healthy": service["status"] == "healthy"
            }
            
            self.health_checks[service["name"]] = health_data
            
            if service["status"] != "healthy":
                self.alerts.append({
                    "timestamp": datetime.now().isoformat(),
                    "service": service["name"],
                    "alert_type": "service_degraded",
                    "message": f"Service {service['name']} is {service['status']}"
                })
            
            self.logger.info(
                "Health check completed",
                service=service["name"],
                status=service["status"],
                response_time=service["response_time"]
            )
    
    async def test_performance_monitoring(self):
        """Test performance monitoring"""
        self.logger.info("Testing performance monitoring")
        
        # Simulate performance metrics
        performance_data = {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 78.1,
            "network_io": 1024.5,
            "active_connections": 23,
            "queue_size": 12
        }
        
        # Check thresholds
        thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "active_connections": 100,
            "queue_size": 50
        }
        
        for metric, value in performance_data.items():
            threshold = thresholds.get(metric, 100.0)
            
            if value > threshold:
                self.alerts.append({
                    "timestamp": datetime.now().isoformat(),
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "alert_type": "threshold_exceeded"
                })
            
            self.logger.info(
                "Performance metric recorded",
                metric=metric,
                value=value,
                threshold=threshold,
                alert_triggered=value > threshold
            )
    
    async def test_circuit_breaker_monitoring(self):
        """Test circuit breaker monitoring"""
        self.logger.info("Testing circuit breaker monitoring")
        
        circuit_breakers = [
            {"name": "scrapy_service", "state": "closed", "failure_count": 0},
            {"name": "proxy_rotator", "state": "half_open", "failure_count": 3},
            {"name": "vpn_connector", "state": "open", "failure_count": 8}
        ]
        
        for cb in circuit_breakers:
            if cb["state"] == "open":
                self.alerts.append({
                    "timestamp": datetime.now().isoformat(),
                    "circuit_breaker": cb["name"],
                    "state": cb["state"],
                    "failure_count": cb["failure_count"],
                    "alert_type": "circuit_breaker_open"
                })
            
            self.logger.info(
                "Circuit breaker status",
                circuit_breaker=cb["name"],
                state=cb["state"],
                failure_count=cb["failure_count"],
                needs_attention=cb["state"] != "closed"
            )
    
    async def run_health_monitoring_tests(self):
        """Run all health monitoring tests"""
        self.logger.info("Starting health monitoring tests")
        
        test_methods = [
            self.test_service_health_checks,
            self.test_performance_monitoring,
            self.test_circuit_breaker_monitoring
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                self.logger.info(f"Health test completed: {test_method.__name__}")
            except Exception as e:
                self.logger.error(f"Health test failed: {test_method.__name__}", error=str(e))
        
        # Generate health summary
        await self.generate_health_summary()
    
    async def generate_health_summary(self):
        """Generate health monitoring summary"""
        healthy_services = len([s for s in self.health_checks.values() if s["healthy"]])
        total_services = len(self.health_checks)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy" if healthy_services == total_services else "degraded",
            "healthy_services": healthy_services,
            "total_services": total_services,
            "total_alerts": len(self.alerts),
            "health_checks": self.health_checks,
            "alerts": self.alerts
        }
        
        self.logger.info(
            "Health monitoring summary",
            overall_health=summary["overall_health"],
            healthy_services=healthy_services,
            total_services=total_services,
            total_alerts=len(self.alerts)
        )
        
        # Save health report
        health_file = Path("health_monitoring_results.json")
        with open(health_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"💾 Health monitoring results saved to: {health_file}")

async def main():
    """Main function to run all monitoring tests"""
    print("🔍 Starting Monitoring and Logging Tests")
    print("=" * 50)
    
    # Run logging tests
    logging_test = LoggingTest()
    await logging_test.run_all_tests()
    
    print("\n" + "=" * 50)
    
    # Run health monitoring tests
    health_test = HealthMonitoringTest()
    await health_test.run_health_monitoring_tests()
    
    print("\n🎉 All monitoring tests completed!")

if __name__ == "__main__":
    asyncio.run(main())