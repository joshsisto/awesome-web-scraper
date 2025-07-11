import pytest
from datetime import datetime
from common.models.scrape_request import ScrapeRequest, ScrapeMethod, AuthType, Priority
from common.models.scrape_result import ScrapeResult, ScrapeStatus
from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider, ProxyStatus


class TestScrapeRequest:
    """Test cases for ScrapeRequest model"""
    
    def test_scrape_request_creation(self):
        """Test creating a basic scrape request"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.SCRAPY,
            selectors={"title": "h1"}
        )
        
        assert request.url == "https://example.com"
        assert request.method == ScrapeMethod.SCRAPY
        assert request.selectors == {"title": "h1"}
        assert request.priority == Priority.NORMAL
        assert request.auth_type == AuthType.NONE
        assert request.use_proxy is True
        assert request.use_stealth is True
        assert request.timeout == 30
        assert request.max_retries == 3
    
    def test_scrape_request_with_auth(self):
        """Test scrape request with authentication"""
        request = ScrapeRequest(
            url="https://example.com/login",
            method=ScrapeMethod.PLAYWRIGHT,
            auth_type=AuthType.FORM,
            auth_credentials={
                "username": "testuser",
                "password": "testpass"
            }
        )
        
        assert request.auth_type == AuthType.FORM
        assert request.auth_credentials["username"] == "testuser"
        assert request.auth_credentials["password"] == "testpass"
    
    def test_scrape_request_validation(self):
        """Test scrape request validation"""
        with pytest.raises(ValueError):
            ScrapeRequest(url="invalid-url")
    
    def test_scrape_request_serialization(self):
        """Test scrape request serialization"""
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.PYDOLL,
            selectors={"title": "h1", "links": "a"}
        )
        
        data = request.dict()
        assert data["url"] == "https://example.com"
        assert data["method"] == "pydoll"
        assert "created_at" in data
        assert "updated_at" in data


class TestScrapeResult:
    """Test cases for ScrapeResult model"""
    
    def test_scrape_result_creation(self):
        """Test creating a basic scrape result"""
        result = ScrapeResult(
            request_id="test123",
            status=ScrapeStatus.SUCCESS,
            status_code=200,
            data={"title": "Test Page"}
        )
        
        assert result.request_id == "test123"
        assert result.status == ScrapeStatus.SUCCESS
        assert result.status_code == 200
        assert result.data == {"title": "Test Page"}
        assert result.retry_count == 0
    
    def test_scrape_result_with_error(self):
        """Test scrape result with error"""
        result = ScrapeResult(
            request_id="test123",
            status=ScrapeStatus.FAILED,
            error_message="Connection timeout",
            error_type="TimeoutError"
        )
        
        assert result.status == ScrapeStatus.FAILED
        assert result.error_message == "Connection timeout"
        assert result.error_type == "TimeoutError"
    
    def test_scrape_result_serialization(self):
        """Test scrape result serialization"""
        result = ScrapeResult(
            request_id="test123",
            status=ScrapeStatus.SUCCESS,
            status_code=200,
            data={"title": "Test Page"},
            links=["https://example.com/page1", "https://example.com/page2"]
        )
        
        data = result.dict()
        assert data["request_id"] == "test123"
        assert data["status"] == "success"
        assert data["status_code"] == 200
        assert len(data["links"]) == 2


class TestProxyConfig:
    """Test cases for ProxyConfig model"""
    
    def test_proxy_config_creation(self):
        """Test creating a basic proxy config"""
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER
        )
        
        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080
        assert proxy.proxy_type == ProxyType.HTTP
        assert proxy.provider == ProxyProvider.DATACENTER
        assert proxy.status == ProxyStatus.ACTIVE
        assert proxy.health_score == 1.0
        assert proxy.success_rate == 1.0
    
    def test_proxy_config_with_auth(self):
        """Test proxy config with authentication"""
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.SOCKS5,
            provider=ProxyProvider.PRIVATE_INTERNET_ACCESS,
            username="user",
            password="pass"
        )
        
        assert proxy.username == "user"
        assert proxy.password == "pass"
    
    def test_proxy_config_validation(self):
        """Test proxy config validation"""
        with pytest.raises(ValueError):
            ProxyConfig(
                host="proxy.example.com",
                port=70000,  # Invalid port
                proxy_type=ProxyType.HTTP,
                provider=ProxyProvider.DATACENTER
            )
        
        with pytest.raises(ValueError):
            ProxyConfig(
                host="proxy.example.com",
                port=8080,
                proxy_type=ProxyType.HTTP,
                provider=ProxyProvider.DATACENTER,
                health_score=1.5  # Invalid score
            )
    
    def test_proxy_url_generation(self):
        """Test proxy URL generation"""
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER
        )
        
        assert proxy.get_proxy_url() == "http://proxy.example.com:8080"
        
        proxy.username = "user"
        proxy.password = "pass"
        
        assert proxy.get_proxy_url() == "http://user:pass@proxy.example.com:8080"
    
    def test_health_score_update(self):
        """Test health score update"""
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER
        )
        
        initial_score = proxy.health_score
        
        # Successful request
        proxy.update_health_score(True)
        assert proxy.health_score >= initial_score
        assert proxy.success_rate == 1.0
        assert proxy.total_requests == 1
        assert proxy.failed_requests == 0
        
        # Failed request
        proxy.update_health_score(False)
        assert proxy.health_score < initial_score
        assert proxy.success_rate == 0.5
        assert proxy.total_requests == 2
        assert proxy.failed_requests == 1
    
    def test_proxy_config_serialization(self):
        """Test proxy config serialization"""
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.SOCKS5,
            provider=ProxyProvider.PRIVATE_INTERNET_ACCESS,
            country="US",
            region="California",
            city="Los Angeles"
        )
        
        data = proxy.dict()
        assert data["host"] == "proxy.example.com"
        assert data["port"] == 8080
        assert data["proxy_type"] == "socks5"
        assert data["provider"] == "pia"
        assert data["country"] == "US"
        assert data["region"] == "California"
        assert data["city"] == "Los Angeles"


if __name__ == "__main__":
    pytest.main([__file__])