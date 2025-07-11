import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.extraction.pydoll_service import PyDollService
from services.extraction.playwright_service import PlaywrightService
from services.extraction.extraction_orchestrator import ExtractionOrchestrator, ExtractionStrategy
from common.models.scrape_request import ScrapeRequest, ScrapeMethod, AuthType
from common.models.scrape_result import ScrapeResult, ScrapeStatus
from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider


@pytest.fixture
def sample_scrape_request():
    """Fixture providing a sample scrape request"""
    return ScrapeRequest(
        url="https://example.com",
        method=ScrapeMethod.PYDOLL,
        selectors={"title": "h1", "content": ".content"},
        extract_links=True,
        extract_images=True
    )


@pytest.fixture
def sample_proxy_config():
    """Fixture providing a sample proxy configuration"""
    return ProxyConfig(
        host="proxy.example.com",
        port=8080,
        proxy_type=ProxyType.HTTP,
        provider=ProxyProvider.DATACENTER
    )


class TestPyDollService:
    """Test cases for PyDollService"""
    
    @pytest.fixture
    async def pydoll_service(self):
        """Fixture providing a PyDoll service instance"""
        service = PyDollService()
        await service.initialize()
        yield service
        await service.close()
    
    @pytest.mark.asyncio
    async def test_initialization(self, pydoll_service):
        """Test PyDoll service initialization"""
        assert pydoll_service.session is not None
        assert pydoll_service.ua is not None
        assert pydoll_service.proxy_config is None
    
    @pytest.mark.asyncio
    async def test_set_proxy_config(self, pydoll_service, sample_proxy_config):
        """Test setting proxy configuration"""
        pydoll_service.set_proxy_config(sample_proxy_config)
        
        assert pydoll_service.proxy_config == sample_proxy_config
    
    @pytest.mark.asyncio
    async def test_scrape_success(self, pydoll_service, sample_scrape_request):
        """Test successful scraping"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Title</h1>
                <div class="content">Test Content</div>
                <a href="/page1">Link 1</a>
                <a href="/page2">Link 2</a>
                <img src="/image1.jpg" alt="Image 1">
                <img src="/image2.jpg" alt="Image 2">
            </body>
        </html>
        """
        mock_response.url = "https://example.com"
        mock_response.content = mock_response.text.encode()
        
        # Mock session.get
        pydoll_service.session.get = AsyncMock(return_value=mock_response)
        
        result = await pydoll_service.scrape(sample_scrape_request)
        
        assert result.status == ScrapeStatus.SUCCESS
        assert result.status_code == 200
        assert result.data["title"] == "Test Title"
        assert result.data["content"] == "Test Content"
        assert len(result.links) == 2
        assert len(result.images) == 2
        assert result.success_score > 0.5
    
    @pytest.mark.asyncio
    async def test_scrape_timeout(self, pydoll_service, sample_scrape_request):
        """Test scraping with timeout"""
        import httpx
        
        # Mock timeout exception
        pydoll_service.session.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        
        result = await pydoll_service.scrape(sample_scrape_request)
        
        assert result.status == ScrapeStatus.TIMEOUT
        assert result.error_type == "TimeoutError"
        assert result.error_message == "Request timeout"
    
    @pytest.mark.asyncio
    async def test_scrape_rate_limited(self, pydoll_service, sample_scrape_request):
        """Test scraping with rate limiting"""
        # Mock rate limited response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"content-type": "text/html"}
        
        pydoll_service.session.get = AsyncMock(return_value=mock_response)
        
        result = await pydoll_service.scrape(sample_scrape_request)
        
        assert result.status == ScrapeStatus.RATE_LIMITED
        assert result.error_type == "RateLimitError"
        assert result.status_code == 429
    
    @pytest.mark.asyncio
    async def test_scrape_invalid_method(self, pydoll_service):
        """Test scraping with invalid method"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.SCRAPY  # Wrong method
        )
        
        with pytest.raises(ValueError, match="Invalid method for PyDollService"):
            await pydoll_service.scrape(request)
    
    @pytest.mark.asyncio
    async def test_batch_scrape(self, pydoll_service):
        """Test batch scraping"""
        requests = [
            ScrapeRequest(url="https://example.com/1", method=ScrapeMethod.PYDOLL),
            ScrapeRequest(url="https://example.com/2", method=ScrapeMethod.PYDOLL),
            ScrapeRequest(url="https://example.com/3", method=ScrapeMethod.PYDOLL)
        ]
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.url = "https://example.com"
        mock_response.content = mock_response.text.encode()
        
        pydoll_service.session.get = AsyncMock(return_value=mock_response)
        
        results = await pydoll_service.batch_scrape(requests)
        
        assert len(results) == 3
        assert all(result.status == ScrapeStatus.SUCCESS for result in results)
    
    def test_get_supported_features(self, pydoll_service):
        """Test getting supported features"""
        features = pydoll_service.get_supported_features()
        
        assert features["javascript"] is False
        assert features["cookies"] is True
        assert features["concurrent_requests"] is True
        assert features["proxy_support"] is True
        assert features["fast_parsing"] is True
        assert features["memory_efficient"] is True


class TestPlaywrightService:
    """Test cases for PlaywrightService"""
    
    @pytest.fixture
    async def playwright_service(self):
        """Fixture providing a Playwright service instance"""
        service = PlaywrightService()
        # Mock playwright initialization
        service.playwright = Mock()
        service.browser = Mock()
        yield service
        await service.close()
    
    @pytest.mark.asyncio
    async def test_initialization(self, playwright_service):
        """Test Playwright service initialization"""
        assert playwright_service.playwright is not None
        assert playwright_service.browser is not None
        assert playwright_service.proxy_config is None
    
    @pytest.mark.asyncio
    async def test_set_proxy_config(self, playwright_service, sample_proxy_config):
        """Test setting proxy configuration"""
        playwright_service.set_proxy_config(sample_proxy_config)
        
        assert playwright_service.proxy_config == sample_proxy_config
    
    @pytest.mark.asyncio
    async def test_scrape_playwright_method_required(self, playwright_service):
        """Test that Playwright method is required"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.SCRAPY  # Wrong method
        )
        
        with pytest.raises(ValueError, match="Invalid method for PlaywrightService"):
            await playwright_service.scrape(request)
    
    @pytest.mark.asyncio
    async def test_scrape_success_mock(self, playwright_service):
        """Test successful scraping with mocked browser"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.PLAYWRIGHT,
            selectors={"title": "h1"},
            extract_links=True
        )
        
        # Mock browser context and page
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        
        # Mock browser methods
        playwright_service.browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_cookies = AsyncMock()
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.query_selector_all = AsyncMock(return_value=[])
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_page.text_content = AsyncMock(return_value="Test content")
        mock_page.url = "https://example.com"
        mock_page.close = AsyncMock()
        mock_context.close = AsyncMock()
        
        result = await playwright_service.scrape(request)
        
        assert result.status == ScrapeStatus.SUCCESS
        assert result.status_code == 200
        mock_page.goto.assert_called_once()
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
    
    def test_get_supported_features(self, playwright_service):
        """Test getting supported features"""
        features = playwright_service.get_supported_features()
        
        assert features["javascript"] is True
        assert features["cookies"] is True
        assert features["browser_automation"] is True
        assert features["screenshot_capture"] is True
        assert features["proxy_support"] is True
        assert features["stealth_mode"] is True


class TestExtractionOrchestrator:
    """Test cases for ExtractionOrchestrator"""
    
    @pytest.fixture
    async def orchestrator(self):
        """Fixture providing an extraction orchestrator"""
        orchestrator = ExtractionOrchestrator()
        
        # Mock services
        orchestrator.services[ScrapeMethod.PYDOLL] = AsyncMock()
        orchestrator.services[ScrapeMethod.PLAYWRIGHT] = AsyncMock()
        orchestrator.services[ScrapeMethod.SCRAPY] = AsyncMock()
        
        # Mock service initialization
        orchestrator.services[ScrapeMethod.PYDOLL].initialize = AsyncMock()
        orchestrator.services[ScrapeMethod.PLAYWRIGHT].initialize = AsyncMock()
        orchestrator.services[ScrapeMethod.PYDOLL].close = AsyncMock()
        orchestrator.services[ScrapeMethod.PLAYWRIGHT].close = AsyncMock()
        
        await orchestrator.initialize()
        yield orchestrator
        await orchestrator.close()
    
    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert len(orchestrator.services) == 3
        assert all(method in orchestrator.services for method in ScrapeMethod)
        assert len(orchestrator.circuit_breakers) == 3
        
        # Check that services were initialized
        orchestrator.services[ScrapeMethod.PYDOLL].initialize.assert_called_once()
        orchestrator.services[ScrapeMethod.PLAYWRIGHT].initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_success(self, orchestrator):
        """Test successful extraction"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.PYDOLL
        )
        
        expected_result = ScrapeResult(
            request_id="test123",
            status=ScrapeStatus.SUCCESS,
            status_code=200,
            data={"title": "Test"}
        )
        
        # Mock service response
        orchestrator.services[ScrapeMethod.PYDOLL].scrape = AsyncMock(return_value=expected_result)
        
        result = await orchestrator.extract(request)
        
        assert result.status == ScrapeStatus.SUCCESS
        assert result.data == {"title": "Test"}
        orchestrator.services[ScrapeMethod.PYDOLL].scrape.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_with_fallback(self, orchestrator):
        """Test extraction with fallback method"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.SCRAPY
        )
        
        # Mock circuit breaker to be open for scrapy
        orchestrator.circuit_breakers[ScrapeMethod.SCRAPY.value]["state"] = "open"
        
        expected_result = ScrapeResult(
            request_id="test123",
            status=ScrapeStatus.SUCCESS,
            status_code=200,
            data={"title": "Test"}
        )
        
        # Mock fallback service response
        orchestrator.services[ScrapeMethod.PYDOLL].scrape = AsyncMock(return_value=expected_result)
        
        result = await orchestrator.extract(request)
        
        assert result.status == ScrapeStatus.SUCCESS
        assert request.method == ScrapeMethod.PYDOLL  # Should be updated to fallback
        orchestrator.services[ScrapeMethod.PYDOLL].scrape.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_all_methods_unavailable(self, orchestrator):
        """Test extraction when all methods are unavailable"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.SCRAPY
        )
        
        # Mock all circuit breakers to be open
        for method in ScrapeMethod:
            orchestrator.circuit_breakers[method.value]["state"] = "open"
        
        result = await orchestrator.extract(request)
        
        assert result.status == ScrapeStatus.FAILED
        assert result.error_type == "CircuitBreakerError"
    
    @pytest.mark.asyncio
    async def test_batch_extract(self, orchestrator):
        """Test batch extraction"""
        requests = [
            ScrapeRequest(url="https://example.com/1", method=ScrapeMethod.PYDOLL),
            ScrapeRequest(url="https://example.com/2", method=ScrapeMethod.PLAYWRIGHT),
            ScrapeRequest(url="https://example.com/3", method=ScrapeMethod.PYDOLL)
        ]
        
        # Mock service responses
        pydoll_results = [
            ScrapeResult(request_id="1", status=ScrapeStatus.SUCCESS, data={"title": "Test 1"}),
            ScrapeResult(request_id="3", status=ScrapeStatus.SUCCESS, data={"title": "Test 3"})
        ]
        playwright_results = [
            ScrapeResult(request_id="2", status=ScrapeStatus.SUCCESS, data={"title": "Test 2"})
        ]
        
        orchestrator.services[ScrapeMethod.PYDOLL].batch_scrape = AsyncMock(return_value=pydoll_results)
        orchestrator.services[ScrapeMethod.PLAYWRIGHT].batch_scrape = AsyncMock(return_value=playwright_results)
        
        results = await orchestrator.batch_extract(requests)
        
        assert len(results) == 3
        assert all(result.status == ScrapeStatus.SUCCESS for result in results)
    
    def test_suggest_method_speed_first(self, orchestrator):
        """Test method suggestion with speed-first strategy"""
        # Simple request
        request = ScrapeRequest(url="https://example.com", method=ScrapeMethod.SCRAPY)
        
        suggested = orchestrator.suggest_method(request, ExtractionStrategy.SPEED_FIRST)
        assert suggested == ScrapeMethod.SCRAPY
        
        # Request with JavaScript
        request.wait_conditions = ["networkidle"]
        suggested = orchestrator.suggest_method(request, ExtractionStrategy.SPEED_FIRST)
        assert suggested == ScrapeMethod.PLAYWRIGHT
    
    def test_suggest_method_quality_first(self, orchestrator):
        """Test method suggestion with quality-first strategy"""
        # Request with authentication
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.SCRAPY,
            auth_type=AuthType.FORM
        )
        
        suggested = orchestrator.suggest_method(request, ExtractionStrategy.QUALITY_FIRST)
        assert suggested == ScrapeMethod.PLAYWRIGHT
    
    def test_suggest_method_cost_optimized(self, orchestrator):
        """Test method suggestion with cost-optimized strategy"""
        # Simple request
        request = ScrapeRequest(url="https://example.com", method=ScrapeMethod.SCRAPY)
        
        suggested = orchestrator.suggest_method(request, ExtractionStrategy.COST_OPTIMIZED)
        assert suggested == ScrapeMethod.SCRAPY
        
        # Request with complex interaction
        request.wait_conditions = ["selector:.complex", "delay:5", "networkidle"]
        suggested = orchestrator.suggest_method(request, ExtractionStrategy.COST_OPTIMIZED)
        assert suggested == ScrapeMethod.PLAYWRIGHT
    
    def test_circuit_breaker_logic(self, orchestrator):
        """Test circuit breaker logic"""
        method = ScrapeMethod.PYDOLL
        
        # Test closed state
        assert orchestrator._check_circuit_breaker(method) is True
        
        # Test failure updates
        for _ in range(5):
            orchestrator._update_circuit_breaker(method, False)
        
        # Should be open now
        assert orchestrator._check_circuit_breaker(method) is False
        
        # Test recovery
        orchestrator.circuit_breakers[method.value]["last_failure_time"] = 0  # Force timeout
        assert orchestrator._check_circuit_breaker(method) is True  # Should be half-open
    
    def test_performance_metrics_tracking(self, orchestrator):
        """Test performance metrics tracking"""
        method = ScrapeMethod.PYDOLL
        
        # Track some metrics
        orchestrator._update_performance_metrics(method, 1.5, True)
        orchestrator._update_performance_metrics(method, 2.0, True)
        orchestrator._update_performance_metrics(method, 3.0, False)
        
        metrics = orchestrator.get_performance_metrics()
        
        assert method.value in metrics
        assert metrics[method.value]["requests"] == 3
        assert metrics[method.value]["successful_requests"] == 2
        assert metrics[method.value]["success_rate"] == 2/3
        assert metrics[method.value]["avg_response_time"] == (1.5 + 2.0 + 3.0) / 3
    
    def test_get_supported_features(self, orchestrator):
        """Test getting supported features"""
        # Mock service features
        orchestrator.services[ScrapeMethod.PYDOLL].get_supported_features = Mock(
            return_value={"javascript": False, "cookies": True}
        )
        orchestrator.services[ScrapeMethod.PLAYWRIGHT].get_supported_features = Mock(
            return_value={"javascript": True, "cookies": True}
        )
        orchestrator.services[ScrapeMethod.SCRAPY].get_supported_features = Mock(
            return_value={"javascript": False, "cookies": True}
        )
        
        features = orchestrator.get_supported_features()
        
        assert len(features) == 3
        assert features["pydoll"]["javascript"] is False
        assert features["playwright"]["javascript"] is True
        assert features["scrapy"]["javascript"] is False


if __name__ == "__main__":
    pytest.main([__file__])