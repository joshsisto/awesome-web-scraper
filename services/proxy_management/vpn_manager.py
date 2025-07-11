import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
import structlog
from .pia_integration import PIAIntegration
from common.models.proxy_config import ProxyConfig

logger = structlog.get_logger()


class VPNProvider(str, Enum):
    """Supported VPN providers"""
    PIA = "pia"
    NORDVPN = "nordvpn"
    EXPRESSVPN = "expressvpn"
    SURFSHARK = "surfshark"


class VPNManager:
    """Main VPN management class"""
    
    def __init__(self, provider: VPNProvider = VPNProvider.PIA):
        self.provider = provider
        self.logger = logger.bind(service="vpn_manager")
        self.integrations: Dict[str, Any] = {}
        self.current_integration: Optional[Any] = None
    
    async def initialize(self) -> None:
        """Initialize VPN manager"""
        try:
            if self.provider == VPNProvider.PIA:
                self.integrations[VPNProvider.PIA] = PIAIntegration()
                await self.integrations[VPNProvider.PIA].initialize()
                self.current_integration = self.integrations[VPNProvider.PIA]
            else:
                raise NotImplementedError(f"Provider {self.provider} not implemented yet")
            
            self.logger.info("VPN manager initialized", provider=self.provider)
        except Exception as e:
            self.logger.error("Failed to initialize VPN manager", provider=self.provider, error=str(e))
            raise
    
    async def connect(self, server_name: Optional[str] = None, country: Optional[str] = None) -> bool:
        """Connect to VPN server"""
        if not self.current_integration:
            self.logger.error("No VPN integration available")
            return False
        
        try:
            if server_name:
                return await self.current_integration.connect_to_server(server_name)
            elif country:
                optimal_server = await self.current_integration.get_optimal_server(country)
                if optimal_server:
                    return await self.current_integration.connect_to_server(optimal_server.name)
                else:
                    self.logger.error("No servers available for country", country=country)
                    return False
            else:
                # Connect to optimal server
                optimal_server = await self.current_integration.get_optimal_server()
                if optimal_server:
                    return await self.current_integration.connect_to_server(optimal_server.name)
                else:
                    self.logger.error("No servers available")
                    return False
        except Exception as e:
            self.logger.error("Failed to connect to VPN", error=str(e))
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from VPN"""
        if not self.current_integration:
            self.logger.error("No VPN integration available")
            return False
        
        try:
            return await self.current_integration.disconnect()
        except Exception as e:
            self.logger.error("Failed to disconnect from VPN", error=str(e))
            return False
    
    async def rotate_server(self, country: Optional[str] = None) -> bool:
        """Rotate to a different VPN server"""
        if not self.current_integration:
            self.logger.error("No VPN integration available")
            return False
        
        try:
            return await self.current_integration.rotate_server(country)
        except Exception as e:
            self.logger.error("Failed to rotate VPN server", error=str(e))
            return False
    
    async def get_status(self) -> str:
        """Get current VPN status"""
        if not self.current_integration:
            return "no_integration"
        
        try:
            return await self.current_integration.check_pia_status()
        except Exception as e:
            self.logger.error("Failed to get VPN status", error=str(e))
            return "error"
    
    def get_proxy_config(self) -> Optional[ProxyConfig]:
        """Get current proxy configuration"""
        if not self.current_integration:
            return None
        
        return self.current_integration.get_proxy_config()
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        if not self.current_integration:
            return {"status": "no_integration", "provider": self.provider}
        
        try:
            info = await self.current_integration.get_connection_info()
            info["provider"] = self.provider
            return info
        except Exception as e:
            self.logger.error("Failed to get connection info", error=str(e))
            return {"status": "error", "provider": self.provider, "error": str(e)}
    
    async def get_available_countries(self) -> List[str]:
        """Get list of available countries"""
        if not self.current_integration:
            return []
        
        try:
            if hasattr(self.current_integration, 'servers'):
                countries = set()
                for server in self.current_integration.servers.values():
                    countries.add(server.country)
                return sorted(list(countries))
            return []
        except Exception as e:
            self.logger.error("Failed to get available countries", error=str(e))
            return []
    
    async def get_servers_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Get servers for a specific country"""
        if not self.current_integration:
            return []
        
        try:
            if hasattr(self.current_integration, 'servers'):
                servers = []
                for server in self.current_integration.servers.values():
                    if server.country.lower() == country.lower():
                        servers.append({
                            "name": server.name,
                            "host": server.host,
                            "country": server.country,
                            "region": server.region,
                            "city": server.city,
                            "load": server.load,
                            "latency": server.latency
                        })
                return sorted(servers, key=lambda x: x["load"])
            return []
        except Exception as e:
            self.logger.error("Failed to get servers by country", country=country, error=str(e))
            return []
    
    async def health_check(self) -> bool:
        """Perform health check on VPN connection"""
        try:
            status = await self.get_status()
            if status == "Connected":
                # Additional checks could be added here
                # e.g., test actual IP, DNS leaks, etc.
                return True
            return False
        except Exception as e:
            self.logger.error("VPN health check failed", error=str(e))
            return False
    
    async def auto_connect(self, preferred_countries: List[str] = None) -> bool:
        """Auto-connect to best available server"""
        if not preferred_countries:
            preferred_countries = ["US", "UK", "DE", "CA"]
        
        try:
            for country in preferred_countries:
                servers = await self.get_servers_by_country(country)
                if servers:
                    # Try to connect to the best server (lowest load)
                    best_server = servers[0]
                    success = await self.connect(server_name=best_server["name"])
                    if success:
                        self.logger.info("Auto-connected to VPN", server=best_server["name"])
                        return True
            
            # If no preferred countries work, try any available server
            if self.current_integration and hasattr(self.current_integration, 'servers'):
                optimal_server = await self.current_integration.get_optimal_server()
                if optimal_server:
                    success = await self.connect(server_name=optimal_server.name)
                    if success:
                        self.logger.info("Auto-connected to optimal VPN server", server=optimal_server.name)
                        return True
            
            self.logger.error("Failed to auto-connect to any VPN server")
            return False
            
        except Exception as e:
            self.logger.error("Auto-connect failed", error=str(e))
            return False