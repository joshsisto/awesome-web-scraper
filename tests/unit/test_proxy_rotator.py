import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from services.proxy_management.proxy_rotator import ProxyRotator, ProxyPool, RotationStrategy
from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider, ProxyStatus


@pytest.fixture
def proxy_configs():
    """Fixture providing sample proxy configurations"""
    return [
        ProxyConfig(
            host="proxy1.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER,
            country="US",
            health_score=0.9,
            success_rate=0.95
        ),
        ProxyConfig(
            host="proxy2.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER,
            country="UK",
            health_score=0.8,
            success_rate=0.85
        ),
        ProxyConfig(
            host="proxy3.example.com",
            port=8080,
            proxy_type=ProxyType.SOCKS5,
            provider=ProxyProvider.RESIDENTIAL,
            country="US",
            health_score=0.7,
            success_rate=0.75
        )
    ]


@pytest.fixture
def proxy_pool(proxy_configs):
    """Fixture providing a sample proxy pool"""
    return ProxyPool(
        name="test_pool",
        proxies=proxy_configs,
        strategy=RotationStrategy.ROUND_ROBIN
    )


@pytest.fixture
async def proxy_rotator():
    """Fixture providing a proxy rotator instance"""
    rotator = ProxyRotator("redis://localhost:6379")
    
    # Mock Redis
    rotator.redis = AsyncMock()
    rotator.redis.ping = AsyncMock()
    rotator.redis.keys = AsyncMock(return_value=[])
    rotator.redis.get = AsyncMock(return_value=None)
    rotator.redis.set = AsyncMock()
    rotator.redis.delete = AsyncMock()
    rotator.redis.close = AsyncMock()
    
    # Mock VPN manager
    rotator.vpn_manager = AsyncMock()
    rotator.vpn_manager.initialize = AsyncMock()
    rotator.vpn_manager.disconnect = AsyncMock()
    
    await rotator.initialize()
    yield rotator
    await rotator.close()


class TestProxyRotator:
    """Test cases for ProxyRotator"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, proxy_rotator):
        """Test proxy rotator initialization"""
        assert proxy_rotator.redis is not None
        assert proxy_rotator.vpn_manager is not None
        assert proxy_rotator.health_check_task is not None
        assert len(proxy_rotator.pools) == 0
    
    @pytest.mark.asyncio
    async def test_add_proxy_pool(self, proxy_rotator, proxy_pool):
        """Test adding a proxy pool"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        assert "test_pool" in proxy_rotator.pools
        assert proxy_rotator.pools["test_pool"] == proxy_pool
        proxy_rotator.redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_proxy_pool(self, proxy_rotator, proxy_pool):
        """Test removing a proxy pool"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        await proxy_rotator.remove_proxy_pool("test_pool")
        
        assert "test_pool" not in proxy_rotator.pools
        proxy_rotator.redis.delete.assert_called_with("proxy_pool:test_pool")
    
    @pytest.mark.asyncio
    async def test_get_proxy_round_robin(self, proxy_rotator, proxy_pool):
        """Test getting proxy with round-robin strategy"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        # Mock proxy stats
        proxy_rotator._get_proxy_stats = AsyncMock(return_value={"total_requests": 0})
        
        proxy = await proxy_rotator.get_proxy("test_pool")
        
        assert proxy is not None
        assert proxy in proxy_pool.proxies
        assert proxy.status == ProxyStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_get_proxy_with_country_filter(self, proxy_rotator, proxy_pool):
        """Test getting proxy with country filter"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        # Mock proxy stats
        proxy_rotator._get_proxy_stats = AsyncMock(return_value={"total_requests": 0})
        
        proxy = await proxy_rotator.get_proxy("test_pool", country="UK")
        
        assert proxy is not None
        assert proxy.country == "UK"
    
    @pytest.mark.asyncio
    async def test_get_proxy_sticky_session(self, proxy_rotator, proxy_pool):
        """Test getting proxy with sticky session"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        # Mock proxy stats
        proxy_rotator._get_proxy_stats = AsyncMock(return_value={"total_requests": 0})
        
        # First request creates session
        proxy1 = await proxy_rotator.get_proxy("test_pool", session_id="session123")
        
        # Second request should return same proxy
        proxy2 = await proxy_rotator.get_proxy("test_pool", session_id="session123")
        
        assert proxy1 is not None
        assert proxy2 is not None
        assert proxy1.host == proxy2.host
        assert proxy1.port == proxy2.port
    
    @pytest.mark.asyncio
    async def test_get_proxy_no_available_proxies(self, proxy_rotator):
        """Test getting proxy when no proxies are available"""
        # Create pool with blocked proxies
        blocked_proxies = [
            ProxyConfig(
                host="blocked.example.com",
                port=8080,
                proxy_type=ProxyType.HTTP,
                provider=ProxyProvider.DATACENTER,
                status=ProxyStatus.BLOCKED
            )
        ]
        
        pool = ProxyPool(
            name="blocked_pool",
            proxies=blocked_proxies,
            strategy=RotationStrategy.ROUND_ROBIN
        )
        
        await proxy_rotator.add_proxy_pool(pool)
        
        proxy = await proxy_rotator.get_proxy("blocked_pool")
        
        assert proxy is None
    
    @pytest.mark.asyncio
    async def test_proxy_selection_strategies(self, proxy_rotator, proxy_configs):
        """Test different proxy selection strategies"""
        # Test health-based strategy
        health_pool = ProxyPool(
            name="health_pool",
            proxies=proxy_configs,
            strategy=RotationStrategy.HEALTH_BASED
        )
        
        await proxy_rotator.add_proxy_pool(health_pool)
        
        proxy = await proxy_rotator._select_proxy(proxy_configs, RotationStrategy.HEALTH_BASED)
        
        # Should select proxy with highest health score
        assert proxy.health_score == 0.9
        assert proxy.host == "proxy1.example.com"
        
        # Test random strategy
        random_proxy = await proxy_rotator._select_proxy(proxy_configs, RotationStrategy.RANDOM)
        assert random_proxy in proxy_configs
        
        # Test geographic strategy
        geo_proxy = await proxy_rotator._select_proxy(proxy_configs, RotationStrategy.GEOGRAPHIC)
        assert geo_proxy in proxy_configs
    
    @pytest.mark.asyncio
    async def test_release_proxy(self, proxy_rotator, proxy_pool):
        """Test releasing a proxy"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        proxy = proxy_pool.proxies[0]
        
        # Mock update stats
        proxy_rotator._update_proxy_stats = AsyncMock()
        
        await proxy_rotator.release_proxy(proxy, session_id="session123")
        
        # Check that stats were updated
        proxy_rotator._update_proxy_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_report_proxy_result_success(self, proxy_rotator, proxy_pool):
        """Test reporting successful proxy result"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        proxy = proxy_pool.proxies[0]
        initial_health = proxy.health_score
        
        # Mock methods
        proxy_rotator._update_proxy_stats = AsyncMock()
        proxy_rotator._save_proxy_config = AsyncMock()
        
        await proxy_rotator.report_proxy_result(proxy, True, 1.5)
        
        # Check that health score improved
        assert proxy.health_score >= initial_health
        assert proxy.status == ProxyStatus.ACTIVE
        
        # Check that stats were updated
        proxy_rotator._update_proxy_stats.assert_called_once()
        proxy_rotator._save_proxy_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_report_proxy_result_failure(self, proxy_rotator, proxy_pool):
        """Test reporting failed proxy result"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        proxy = proxy_pool.proxies[0]
        initial_health = proxy.health_score
        
        # Mock methods
        proxy_rotator._update_proxy_stats = AsyncMock()
        proxy_rotator._save_proxy_config = AsyncMock()
        
        # Report multiple failures to trigger status change
        for _ in range(10):
            await proxy_rotator.report_proxy_result(proxy, False, None)
        
        # Check that health score decreased
        assert proxy.health_score < initial_health
        
        # Check that proxy was blocked due to low health
        assert proxy.status in [ProxyStatus.BLOCKED, ProxyStatus.RATE_LIMITED]
    
    @pytest.mark.asyncio
    async def test_rotate_vpn_if_needed(self, proxy_rotator):
        """Test VPN rotation when needed"""
        # Mock VPN manager
        proxy_rotator.vpn_manager.rotate_server = AsyncMock(return_value=True)
        proxy_rotator.vpn_manager.get_proxy_config = AsyncMock(return_value=None)
        
        # Mock high failure rate
        proxy_rotator.proxy_stats = {
            "proxy1": {"recent_failures": 2},
            "proxy2": {"recent_failures": 2}
        }
        
        result = await proxy_rotator.rotate_vpn_if_needed(failure_threshold=3)
        
        assert result is True
        proxy_rotator.vpn_manager.rotate_server.assert_called_once()
        
        # Check that failure counts were reset
        for stats in proxy_rotator.proxy_stats.values():
            assert stats["recent_failures"] == 0
    
    @pytest.mark.asyncio
    async def test_get_pool_status(self, proxy_rotator, proxy_pool):
        """Test getting pool status"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        status = proxy_rotator.get_pool_status("test_pool")
        
        assert status["name"] == "test_pool"
        assert status["strategy"] == "round_robin"
        assert status["total_proxies"] == 3
        assert status["active_proxies"] == 3
        assert status["blocked_proxies"] == 0
        assert status["failed_proxies"] == 0
    
    @pytest.mark.asyncio
    async def test_get_pool_status_not_found(self, proxy_rotator):
        """Test getting status for non-existent pool"""
        status = proxy_rotator.get_pool_status("nonexistent")
        
        assert "error" in status
        assert status["error"] == "Pool not found"
    
    @pytest.mark.asyncio
    async def test_get_all_pools_status(self, proxy_rotator, proxy_pool):
        """Test getting status of all pools"""
        await proxy_rotator.add_proxy_pool(proxy_pool)
        
        # Add another pool
        pool2 = ProxyPool(
            name="pool2",
            proxies=[proxy_pool.proxies[0]],
            strategy=RotationStrategy.RANDOM
        )
        await proxy_rotator.add_proxy_pool(pool2)
        
        all_status = proxy_rotator.get_all_pools_status()
        
        assert len(all_status) == 2
        assert "test_pool" in all_status
        assert "pool2" in all_status
        assert all_status["test_pool"]["total_proxies"] == 3
        assert all_status["pool2"]["total_proxies"] == 1


if __name__ == "__main__":
    pytest.main([__file__])