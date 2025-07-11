import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from services.proxy_management.vpn_manager import VPNManager, VPNProvider
from services.proxy_management.pia_integration import PIAIntegration, PIAServer
from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider, ProxyStatus


class TestVPNManager:
    """Test cases for VPNManager"""
    
    @pytest.fixture
    async def vpn_manager(self):
        """Fixture providing a VPN manager instance"""
        manager = VPNManager(VPNProvider.PIA)
        
        # Mock PIA integration
        mock_pia = AsyncMock(spec=PIAIntegration)
        mock_pia.initialize = AsyncMock()
        mock_pia.check_pia_status = AsyncMock(return_value="Connected")
        mock_pia.connect_to_server = AsyncMock(return_value=True)
        mock_pia.disconnect = AsyncMock(return_value=True)
        mock_pia.rotate_server = AsyncMock(return_value=True)
        mock_pia.get_proxy_config = AsyncMock(return_value=ProxyConfig(
            host="pia.example.com",
            port=1080,
            proxy_type=ProxyType.SOCKS5,
            provider=ProxyProvider.PRIVATE_INTERNET_ACCESS
        ))
        mock_pia.get_connection_info = AsyncMock(return_value={
            "status": "Connected",
            "current_server": {
                "name": "us-east",
                "country": "US",
                "city": "New York"
            }
        })
        mock_pia.get_optimal_server = AsyncMock(return_value=PIAServer(
            name="us-east",
            host="us-east.pia.com",
            port=1080,
            country="US",
            region="East Coast",
            city="New York",
            load=0.3,
            latency=50.0
        ))
        mock_pia.servers = {
            "us-east": PIAServer("us-east", "us-east.pia.com", 1080, "US", "East Coast", "New York", 0.3, 50.0),
            "us-west": PIAServer("us-west", "us-west.pia.com", 1080, "US", "West Coast", "Los Angeles", 0.4, 80.0),
            "uk-london": PIAServer("uk-london", "uk-london.pia.com", 1080, "UK", "England", "London", 0.2, 40.0)
        }
        
        manager.integrations[VPNProvider.PIA] = mock_pia
        manager.current_integration = mock_pia
        
        yield manager
    
    @pytest.mark.asyncio
    async def test_initialization(self, vpn_manager):
        """Test VPN manager initialization"""
        await vpn_manager.initialize()
        
        assert vpn_manager.provider == VPNProvider.PIA
        assert vpn_manager.current_integration is not None
        vpn_manager.current_integration.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_unsupported_provider(self):
        """Test initialization with unsupported provider"""
        manager = VPNManager(VPNProvider.NORDVPN)
        
        with pytest.raises(NotImplementedError):
            await manager.initialize()
    
    @pytest.mark.asyncio
    async def test_connect_specific_server(self, vpn_manager):
        """Test connecting to a specific server"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.connect(server_name="us-east")
        
        assert result is True
        vpn_manager.current_integration.connect_to_server.assert_called_once_with("us-east")
    
    @pytest.mark.asyncio
    async def test_connect_by_country(self, vpn_manager):
        """Test connecting by country"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.connect(country="US")
        
        assert result is True
        vpn_manager.current_integration.get_optimal_server.assert_called_once_with("US")
        vpn_manager.current_integration.connect_to_server.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_optimal_server(self, vpn_manager):
        """Test connecting to optimal server"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.connect()
        
        assert result is True
        vpn_manager.current_integration.get_optimal_server.assert_called_once_with()
        vpn_manager.current_integration.connect_to_server.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_no_integration(self):
        """Test connecting without integration"""
        manager = VPNManager(VPNProvider.PIA)
        
        result = await manager.connect()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_connect_no_servers_available(self, vpn_manager):
        """Test connecting when no servers are available"""
        await vpn_manager.initialize()
        
        # Mock no servers available
        vpn_manager.current_integration.get_optimal_server.return_value = None
        
        result = await vpn_manager.connect(country="XX")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self, vpn_manager):
        """Test disconnecting"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.disconnect()
        
        assert result is True
        vpn_manager.current_integration.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_no_integration(self):
        """Test disconnecting without integration"""
        manager = VPNManager(VPNProvider.PIA)
        
        result = await manager.disconnect()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_rotate_server(self, vpn_manager):
        """Test rotating server"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.rotate_server(country="US")
        
        assert result is True
        vpn_manager.current_integration.rotate_server.assert_called_once_with("US")
    
    @pytest.mark.asyncio
    async def test_rotate_server_no_integration(self):
        """Test rotating server without integration"""
        manager = VPNManager(VPNProvider.PIA)
        
        result = await manager.rotate_server()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_status(self, vpn_manager):
        """Test getting VPN status"""
        await vpn_manager.initialize()
        
        status = await vpn_manager.get_status()
        
        assert status == "Connected"
        vpn_manager.current_integration.check_pia_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_status_no_integration(self):
        """Test getting status without integration"""
        manager = VPNManager(VPNProvider.PIA)
        
        status = await manager.get_status()
        
        assert status == "no_integration"
    
    @pytest.mark.asyncio
    async def test_get_proxy_config(self, vpn_manager):
        """Test getting proxy configuration"""
        await vpn_manager.initialize()
        
        config = vpn_manager.get_proxy_config()
        
        assert config is not None
        assert config.host == "pia.example.com"
        assert config.port == 1080
        assert config.proxy_type == ProxyType.SOCKS5
        assert config.provider == ProxyProvider.PRIVATE_INTERNET_ACCESS
    
    @pytest.mark.asyncio
    async def test_get_proxy_config_no_integration(self):
        """Test getting proxy config without integration"""
        manager = VPNManager(VPNProvider.PIA)
        
        config = manager.get_proxy_config()
        
        assert config is None
    
    @pytest.mark.asyncio
    async def test_get_connection_info(self, vpn_manager):
        """Test getting connection info"""
        await vpn_manager.initialize()
        
        info = await vpn_manager.get_connection_info()
        
        assert info["status"] == "Connected"
        assert info["provider"] == VPNProvider.PIA
        assert info["current_server"]["name"] == "us-east"
        assert info["current_server"]["country"] == "US"
    
    @pytest.mark.asyncio
    async def test_get_connection_info_no_integration(self):
        """Test getting connection info without integration"""
        manager = VPNManager(VPNProvider.PIA)
        
        info = await manager.get_connection_info()
        
        assert info["status"] == "no_integration"
        assert info["provider"] == VPNProvider.PIA
    
    @pytest.mark.asyncio
    async def test_get_available_countries(self, vpn_manager):
        """Test getting available countries"""
        await vpn_manager.initialize()
        
        countries = await vpn_manager.get_available_countries()
        
        assert len(countries) == 2
        assert "US" in countries
        assert "UK" in countries
        assert countries == ["UK", "US"]  # Should be sorted
    
    @pytest.mark.asyncio
    async def test_get_available_countries_no_integration(self):
        """Test getting available countries without integration"""
        manager = VPNManager(VPNProvider.PIA)
        
        countries = await manager.get_available_countries()
        
        assert countries == []
    
    @pytest.mark.asyncio
    async def test_get_servers_by_country(self, vpn_manager):
        """Test getting servers by country"""
        await vpn_manager.initialize()
        
        servers = await vpn_manager.get_servers_by_country("US")
        
        assert len(servers) == 2
        assert servers[0]["name"] == "us-east"  # Should be sorted by load
        assert servers[0]["country"] == "US"
        assert servers[0]["load"] == 0.3
        assert servers[1]["name"] == "us-west"
        assert servers[1]["load"] == 0.4
    
    @pytest.mark.asyncio
    async def test_get_servers_by_country_not_found(self, vpn_manager):
        """Test getting servers for non-existent country"""
        await vpn_manager.initialize()
        
        servers = await vpn_manager.get_servers_by_country("XX")
        
        assert servers == []
    
    @pytest.mark.asyncio
    async def test_health_check_connected(self, vpn_manager):
        """Test health check when connected"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.health_check()
        
        assert result is True
        vpn_manager.current_integration.check_pia_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, vpn_manager):
        """Test health check when disconnected"""
        await vpn_manager.initialize()
        
        # Mock disconnected status
        vpn_manager.current_integration.check_pia_status.return_value = "Disconnected"
        
        result = await vpn_manager.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_auto_connect_success(self, vpn_manager):
        """Test auto-connect success"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.auto_connect(["US", "UK"])
        
        assert result is True
        vpn_manager.current_integration.connect_to_server.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auto_connect_failure(self, vpn_manager):
        """Test auto-connect failure"""
        await vpn_manager.initialize()
        
        # Mock connection failure
        vpn_manager.current_integration.connect_to_server.return_value = False
        
        result = await vpn_manager.auto_connect(["XX", "YY"])
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_auto_connect_default_countries(self, vpn_manager):
        """Test auto-connect with default countries"""
        await vpn_manager.initialize()
        
        result = await vpn_manager.auto_connect()
        
        assert result is True
        # Should try with default countries ["US", "UK", "DE", "CA"]
        vpn_manager.current_integration.connect_to_server.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auto_connect_fallback_to_optimal(self, vpn_manager):
        """Test auto-connect fallback to optimal server"""
        await vpn_manager.initialize()
        
        # Mock get_servers_by_country to return empty list
        async def mock_get_servers_by_country(country):
            return []
        
        vpn_manager.get_servers_by_country = mock_get_servers_by_country
        
        result = await vpn_manager.auto_connect(["XX"])
        
        assert result is True
        # Should fall back to optimal server
        vpn_manager.current_integration.get_optimal_server.assert_called_once()
        vpn_manager.current_integration.connect_to_server.assert_called_once()


class TestPIAIntegration:
    """Test cases for PIAIntegration"""
    
    @pytest.fixture
    def pia_integration(self):
        """Fixture providing a PIA integration instance"""
        return PIAIntegration()
    
    @pytest.mark.asyncio
    async def test_initialization(self, pia_integration):
        """Test PIA integration initialization"""
        with patch.object(pia_integration, 'load_server_list') as mock_load_servers, \
             patch.object(pia_integration, 'check_pia_status') as mock_check_status:
            
            mock_load_servers.return_value = None
            mock_check_status.return_value = "Disconnected"
            
            await pia_integration.initialize()
            
            mock_load_servers.assert_called_once()
            mock_check_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_default_servers(self, pia_integration):
        """Test loading default servers"""
        pia_integration._load_default_servers()
        
        assert len(pia_integration.servers) == 8
        assert "us-east" in pia_integration.servers
        assert "uk-london" in pia_integration.servers
        assert pia_integration.servers["us-east"].country == "US"
        assert pia_integration.servers["uk-london"].country == "UK"
    
    @pytest.mark.asyncio
    async def test_get_optimal_server(self, pia_integration):
        """Test getting optimal server"""
        # Load default servers
        pia_integration._load_default_servers()
        
        optimal = await pia_integration.get_optimal_server()
        
        assert optimal is not None
        assert optimal.name in pia_integration.servers
    
    @pytest.mark.asyncio
    async def test_get_optimal_server_by_country(self, pia_integration):
        """Test getting optimal server by country"""
        # Load default servers
        pia_integration._load_default_servers()
        
        optimal = await pia_integration.get_optimal_server("US")
        
        assert optimal is not None
        assert optimal.country == "US"
    
    @pytest.mark.asyncio
    async def test_get_optimal_server_country_not_found(self, pia_integration):
        """Test getting optimal server for non-existent country"""
        # Load default servers
        pia_integration._load_default_servers()
        
        optimal = await pia_integration.get_optimal_server("XX")
        
        assert optimal is None
    
    @pytest.mark.asyncio
    async def test_get_proxy_config_connected(self, pia_integration):
        """Test getting proxy config when connected"""
        # Load default servers
        pia_integration._load_default_servers()
        pia_integration.current_server = pia_integration.servers["us-east"]
        pia_integration.connection_status = "Connected"
        
        config = pia_integration.get_proxy_config()
        
        assert config is not None
        assert config.host == "us-east.privateinternetaccess.com"
        assert config.port == 1080
        assert config.proxy_type == ProxyType.SOCKS5
        assert config.provider == ProxyProvider.PRIVATE_INTERNET_ACCESS
        assert config.country == "US"
    
    @pytest.mark.asyncio
    async def test_get_proxy_config_disconnected(self, pia_integration):
        """Test getting proxy config when disconnected"""
        pia_integration.current_server = None
        pia_integration.connection_status = "Disconnected"
        
        config = pia_integration.get_proxy_config()
        
        assert config is None
    
    @pytest.mark.asyncio
    async def test_get_connection_info(self, pia_integration):
        """Test getting connection info"""
        # Load default servers
        pia_integration._load_default_servers()
        pia_integration.current_server = pia_integration.servers["us-east"]
        pia_integration.connection_status = "Connected"
        
        info = await pia_integration.get_connection_info()
        
        assert info["status"] == "Connected"
        assert info["servers_available"] == 8
        assert info["current_server"]["name"] == "us-east"
        assert info["current_server"]["country"] == "US"
        assert "last_updated" in info


if __name__ == "__main__":
    pytest.main([__file__])