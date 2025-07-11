import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import structlog
from common.models.scrape_request import ScrapeRequest, ScrapeMethod, Priority
from common.models.scrape_result import ScrapeResult, ScrapeStatus
from common.models.proxy_config import ProxyConfig
from .scrapy_service import ScrapyService
from .pydoll_service import PyDollService
from .playwright_service import PlaywrightService

logger = structlog.get_logger()


class ExtractionStrategy(str, Enum):
    """Extraction strategy for automatic method selection"""
    SPEED_FIRST = "speed_first"
    QUALITY_FIRST = "quality_first"
    COST_OPTIMIZED = "cost_optimized"
    RELIABILITY_FIRST = "reliability_first"


class ExtractionOrchestrator:
    """Orchestrates extraction across different services"""
    
    def __init__(self):
        self.logger = logger.bind(service="extraction_orchestrator")
        self.services = {
            ScrapeMethod.SCRAPY: ScrapyService(),
            ScrapeMethod.PYDOLL: PyDollService(),
            ScrapeMethod.PLAYWRIGHT: PlaywrightService()
        }
        self.proxy_config: Optional[ProxyConfig] = None
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize all services"""
        try:
            # Initialize PyDoll service
            await self.services[ScrapeMethod.PYDOLL].initialize()
            
            # Initialize Playwright service  
            await self.services[ScrapeMethod.PLAYWRIGHT].initialize()
            
            # Initialize circuit breakers
            for method in ScrapeMethod:
                self.circuit_breakers[method.value] = {
                    "state": "closed",  # closed, open, half_open
                    "failure_count": 0,
                    "last_failure_time": 0,
                    "failure_threshold": 5,
                    "recovery_timeout": 60,
                    "half_open_max_calls": 3
                }
            
            self.logger.info("Extraction orchestrator initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize extraction orchestrator", error=str(e))
            raise
    
    async def close(self):
        """Close all services"""
        try:
            await self.services[ScrapeMethod.PYDOLL].close()
            await self.services[ScrapeMethod.PLAYWRIGHT].close()
            self.logger.info("Extraction orchestrator closed")
            
        except Exception as e:
            self.logger.error("Failed to close extraction orchestrator", error=str(e))
    
    async def extract(self, scrape_request: ScrapeRequest) -> ScrapeResult:
        """Extract data using the specified or optimal method"""
        
        # Determine extraction method
        method = scrape_request.method
        if method == ScrapeMethod.SCRAPY and not self._is_method_available(method):
            # Fallback to alternative method
            method = self._get_fallback_method(scrape_request)
        
        # Check circuit breaker
        if not self._check_circuit_breaker(method):
            self.logger.warning("Circuit breaker open for method", method=method)
            # Try fallback method
            fallback_method = self._get_fallback_method(scrape_request)
            if fallback_method != method and self._check_circuit_breaker(fallback_method):
                method = fallback_method
            else:
                return ScrapeResult(
                    request_id=str(scrape_request.id) if scrape_request.id else "",
                    status=ScrapeStatus.FAILED,
                    error_message="All extraction methods unavailable",
                    error_type="CircuitBreakerError"
                )
        
        # Set proxy configuration
        if self.proxy_config:
            self.services[method].set_proxy_config(self.proxy_config)
        
        # Perform extraction
        start_time = time.time()
        
        try:
            # Update scrape request method
            scrape_request.method = method
            
            # Extract data
            result = await self.services[method].scrape(scrape_request)
            
            # Update performance metrics
            self._update_performance_metrics(
                method, 
                time.time() - start_time, 
                result.status == ScrapeStatus.SUCCESS
            )
            
            # Update circuit breaker
            self._update_circuit_breaker(method, result.status == ScrapeStatus.SUCCESS)
            
            return result
            
        except Exception as e:
            self.logger.error("Extraction failed", method=method, error=str(e))
            
            # Update circuit breaker
            self._update_circuit_breaker(method, False)
            
            return ScrapeResult(
                request_id=str(scrape_request.id) if scrape_request.id else "",
                status=ScrapeStatus.FAILED,
                error_message=str(e),
                error_type=type(e).__name__,
                response_time=time.time() - start_time
            )
    
    async def batch_extract(self, scrape_requests: List[ScrapeRequest]) -> List[ScrapeResult]:
        """Perform batch extraction with load balancing"""
        
        # Group requests by method
        method_groups = {}
        for request in scrape_requests:
            method = request.method
            if method not in method_groups:
                method_groups[method] = []
            method_groups[method].append(request)
        
        # Process each method group
        all_results = []
        
        for method, requests in method_groups.items():
            if not self._is_method_available(method) or not self._check_circuit_breaker(method):
                # Create error results for unavailable methods
                for request in requests:
                    error_result = ScrapeResult(
                        request_id=str(request.id) if request.id else "",
                        status=ScrapeStatus.FAILED,
                        error_message=f"Method {method} unavailable",
                        error_type="MethodUnavailableError"
                    )
                    all_results.append(error_result)
                continue
            
            # Set proxy configuration
            if self.proxy_config:
                self.services[method].set_proxy_config(self.proxy_config)
            
            # Process batch
            try:
                results = await self.services[method].batch_scrape(requests)
                all_results.extend(results)
                
                # Update metrics for batch
                for result in results:
                    self._update_circuit_breaker(method, result.status == ScrapeStatus.SUCCESS)
                    
            except Exception as e:
                self.logger.error("Batch extraction failed", method=method, error=str(e))
                
                # Create error results
                for request in requests:
                    error_result = ScrapeResult(
                        request_id=str(request.id) if request.id else "",
                        status=ScrapeStatus.FAILED,
                        error_message=str(e),
                        error_type=type(e).__name__
                    )
                    all_results.append(error_result)
                
                # Update circuit breaker
                self._update_circuit_breaker(method, False)
        
        return all_results
    
    def suggest_method(self, scrape_request: ScrapeRequest, strategy: ExtractionStrategy = ExtractionStrategy.SPEED_FIRST) -> ScrapeMethod:
        """Suggest optimal extraction method based on request characteristics"""
        
        # Analyze request characteristics
        has_javascript = any(condition for condition in scrape_request.wait_conditions if "networkidle" in condition or "javascript" in condition)
        needs_authentication = scrape_request.auth_type.value != "none"
        needs_complex_interaction = len(scrape_request.wait_conditions) > 2
        is_high_priority = scrape_request.priority in [Priority.HIGH, Priority.URGENT]
        
        # Decision logic based on strategy
        if strategy == ExtractionStrategy.SPEED_FIRST:
            if has_javascript or needs_authentication or needs_complex_interaction:
                return ScrapeMethod.PLAYWRIGHT
            elif is_high_priority:
                return ScrapeMethod.PYDOLL
            else:
                return ScrapeMethod.SCRAPY
        
        elif strategy == ExtractionStrategy.QUALITY_FIRST:
            if has_javascript or needs_authentication:
                return ScrapeMethod.PLAYWRIGHT
            elif scrape_request.selectors:
                return ScrapeMethod.PYDOLL
            else:
                return ScrapeMethod.SCRAPY
        
        elif strategy == ExtractionStrategy.COST_OPTIMIZED:
            if not has_javascript and not needs_authentication:
                return ScrapeMethod.SCRAPY
            elif not needs_complex_interaction:
                return ScrapeMethod.PYDOLL
            else:
                return ScrapeMethod.PLAYWRIGHT
        
        elif strategy == ExtractionStrategy.RELIABILITY_FIRST:
            # Check performance metrics
            best_method = self._get_best_performing_method()
            if best_method:
                return best_method
            
            # Fallback to safest option
            return ScrapeMethod.PLAYWRIGHT
        
        return ScrapeMethod.SCRAPY
    
    def _get_best_performing_method(self) -> Optional[ScrapeMethod]:
        """Get the best performing method based on metrics"""
        if not self.performance_metrics:
            return None
        
        best_method = None
        best_score = 0
        
        for method_name, metrics in self.performance_metrics.items():
            if metrics.get("requests", 0) < 10:  # Need sufficient data
                continue
            
            success_rate = metrics.get("success_rate", 0)
            avg_response_time = metrics.get("avg_response_time", float('inf'))
            
            # Calculate score (higher is better)
            score = success_rate * 0.7 + (1 / (avg_response_time + 1)) * 0.3
            
            if score > best_score:
                best_score = score
                best_method = ScrapeMethod(method_name)
        
        return best_method
    
    def _get_fallback_method(self, scrape_request: ScrapeRequest) -> ScrapeMethod:
        """Get fallback method based on request characteristics"""
        if scrape_request.method == ScrapeMethod.SCRAPY:
            return ScrapeMethod.PYDOLL
        elif scrape_request.method == ScrapeMethod.PYDOLL:
            return ScrapeMethod.PLAYWRIGHT
        else:
            return ScrapeMethod.SCRAPY
    
    def _is_method_available(self, method: ScrapeMethod) -> bool:
        """Check if extraction method is available"""
        return method in self.services
    
    def _check_circuit_breaker(self, method: ScrapeMethod) -> bool:
        """Check circuit breaker state"""
        breaker = self.circuit_breakers.get(method.value, {})
        state = breaker.get("state", "closed")
        
        if state == "closed":
            return True
        elif state == "open":
            # Check if recovery timeout has passed
            if time.time() - breaker.get("last_failure_time", 0) > breaker.get("recovery_timeout", 60):
                breaker["state"] = "half_open"
                breaker["half_open_calls"] = 0
                return True
            return False
        elif state == "half_open":
            # Allow limited calls in half-open state
            calls = breaker.get("half_open_calls", 0)
            if calls < breaker.get("half_open_max_calls", 3):
                breaker["half_open_calls"] = calls + 1
                return True
            return False
        
        return False
    
    def _update_circuit_breaker(self, method: ScrapeMethod, success: bool):
        """Update circuit breaker state"""
        breaker = self.circuit_breakers.get(method.value, {})
        
        if success:
            if breaker.get("state") == "half_open":
                # Reset circuit breaker
                breaker["state"] = "closed"
                breaker["failure_count"] = 0
            elif breaker.get("state") == "closed":
                # Reset failure count on success
                breaker["failure_count"] = 0
        else:
            # Increment failure count
            breaker["failure_count"] = breaker.get("failure_count", 0) + 1
            breaker["last_failure_time"] = time.time()
            
            # Open circuit breaker if threshold reached
            if breaker["failure_count"] >= breaker.get("failure_threshold", 5):
                breaker["state"] = "open"
    
    def _update_performance_metrics(self, method: ScrapeMethod, response_time: float, success: bool):
        """Update performance metrics"""
        method_name = method.value
        
        if method_name not in self.performance_metrics:
            self.performance_metrics[method_name] = {
                "requests": 0,
                "successful_requests": 0,
                "total_response_time": 0,
                "success_rate": 0,
                "avg_response_time": 0
            }
        
        metrics = self.performance_metrics[method_name]
        
        metrics["requests"] += 1
        metrics["total_response_time"] += response_time
        
        if success:
            metrics["successful_requests"] += 1
        
        # Calculate averages
        metrics["success_rate"] = metrics["successful_requests"] / metrics["requests"]
        metrics["avg_response_time"] = metrics["total_response_time"] / metrics["requests"]
    
    def set_proxy_config(self, proxy_config: ProxyConfig):
        """Set proxy configuration for all services"""
        self.proxy_config = proxy_config
        for service in self.services.values():
            service.set_proxy_config(proxy_config)
    
    def get_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get circuit breaker status"""
        return {
            method: {
                "state": breaker.get("state", "closed"),
                "failure_count": breaker.get("failure_count", 0),
                "last_failure_time": breaker.get("last_failure_time", 0)
            }
            for method, breaker in self.circuit_breakers.items()
        }
    
    def get_supported_features(self) -> Dict[str, Dict[str, bool]]:
        """Get supported features for all services"""
        return {
            method.value: service.get_supported_features()
            for method, service in self.services.items()
        }