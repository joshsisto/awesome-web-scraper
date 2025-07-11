import asyncio
import json
import subprocess
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import structlog
from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider, ProxyStatus

logger = structlog.get_logger()


@dataclass
class PIAServer:
    """PIA server information"""
    name: str
    host: str
    port: int
    country: str
    region: str
    city: str
    load: float
    latency: float


class PIAIntegration:
    """Private Internet Access VPN integration"""
    
    def __init__(self, config_path: str = "/opt/pia/config"):
        self.config_path = Path(config_path)
        self.servers: Dict[str, PIAServer] = {}
        self.current_server: Optional[PIAServer] = None
        self.connection_status = "disconnected"
        self.logger = logger.bind(service="pia_integration")
    
    async def initialize(self) -> None:
        """Initialize PIA integration"""
        try:
            await self.load_server_list()
            await self.check_pia_status()
            self.logger.info("PIA integration initialized", servers_count=len(self.servers))
        except Exception as e:
            self.logger.error("Failed to initialize PIA integration", error=str(e))
            raise
    
    async def load_server_list(self) -> None:
        """Load available PIA servers"""
        try:
            # Try to get server list from PIA CLI
            result = await self._run_pia_command(["piactl", "get", "regions"])
            if result.returncode == 0:
                servers_data = json.loads(result.stdout)
                for server_info in servers_data:
                    server = PIAServer(
                        name=server_info.get("name", ""),
                        host=server_info.get("host", ""),
                        port=server_info.get("port", 1080),
                        country=server_info.get("country", ""),
                        region=server_info.get("region", ""),
                        city=server_info.get("city", ""),
                        load=server_info.get("load", 0.0),
                        latency=server_info.get("latency", 0.0)
                    )
                    self.servers[server.name] = server
            else:
                # Fallback to hardcoded popular servers
                self._load_default_servers()
        except Exception as e:
            self.logger.warning("Failed to load server list from PIA", error=str(e))
            self._load_default_servers()
    
    def _load_default_servers(self) -> None:
        """Load default PIA servers as fallback"""
        default_servers = [
            {"name": "us-east", "host": "us-east.privateinternetaccess.com", "country": "US", "region": "East Coast", "city": "New York"},
            {"name": "us-west", "host": "us-west.privateinternetaccess.com", "country": "US", "region": "West Coast", "city": "Los Angeles"},
            {"name": "uk-london", "host": "uk-london.privateinternetaccess.com", "country": "UK", "region": "England", "city": "London"},
            {"name": "de-frankfurt", "host": "de-frankfurt.privateinternetaccess.com", "country": "DE", "region": "Hesse", "city": "Frankfurt"},
            {"name": "ca-toronto", "host": "ca-toronto.privateinternetaccess.com", "country": "CA", "region": "Ontario", "city": "Toronto"},
            {"name": "au-sydney", "host": "au-sydney.privateinternetaccess.com", "country": "AU", "region": "NSW", "city": "Sydney"},
            {"name": "jp-tokyo", "host": "jp-tokyo.privateinternetaccess.com", "country": "JP", "region": "Tokyo", "city": "Tokyo"},
            {"name": "sg-singapore", "host": "sg-singapore.privateinternetaccess.com", "country": "SG", "region": "Singapore", "city": "Singapore"},
        ]
        
        for server_data in default_servers:
            server = PIAServer(
                name=server_data["name"],
                host=server_data["host"],
                port=1080,
                country=server_data["country"],
                region=server_data["region"],
                city=server_data["city"],
                load=0.5,  # Default load
                latency=100.0  # Default latency
            )
            self.servers[server.name] = server
    
    async def check_pia_status(self) -> str:
        """Check current PIA connection status"""
        try:
            result = await self._run_pia_command(["piactl", "get", "connectionstate"])
            if result.returncode == 0:
                status = result.stdout.strip()
                self.connection_status = status
                return status
            else:
                self.connection_status = "unknown"
                return "unknown"
        except Exception as e:
            self.logger.error("Failed to check PIA status", error=str(e))
            self.connection_status = "error"
            return "error"
    
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to a specific PIA server"""
        if server_name not in self.servers:
            self.logger.error("Server not found", server_name=server_name)
            return False
        
        server = self.servers[server_name]
        
        try:
            # Disconnect if already connected
            if self.connection_status == "Connected":
                await self.disconnect()
            
            # Connect to new server
            result = await self._run_pia_command(["piactl", "set", "region", server_name])
            if result.returncode != 0:
                self.logger.error("Failed to set region", server_name=server_name, error=result.stderr)
                return False
            
            result = await self._run_pia_command(["piactl", "connect"])
            if result.returncode != 0:
                self.logger.error("Failed to connect", server_name=server_name, error=result.stderr)
                return False
            
            # Wait for connection
            for _ in range(30):  # 30 second timeout
                await asyncio.sleep(1)
                status = await self.check_pia_status()
                if status == "Connected":
                    self.current_server = server
                    self.logger.info("Connected to PIA server", server_name=server_name)
                    return True
            
            self.logger.error("Connection timeout", server_name=server_name)
            return False
            
        except Exception as e:
            self.logger.error("Failed to connect to server", server_name=server_name, error=str(e))
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from PIA"""
        try:
            result = await self._run_pia_command(["piactl", "disconnect"])
            if result.returncode == 0:
                self.connection_status = "Disconnected"
                self.current_server = None
                self.logger.info("Disconnected from PIA")
                return True
            else:
                self.logger.error("Failed to disconnect", error=result.stderr)
                return False
        except Exception as e:
            self.logger.error("Failed to disconnect", error=str(e))
            return False
    
    async def get_optimal_server(self, country: Optional[str] = None) -> Optional[PIAServer]:
        """Get optimal server based on load and latency"""
        available_servers = list(self.servers.values())
        
        if country:
            available_servers = [s for s in available_servers if s.country.lower() == country.lower()]
        
        if not available_servers:
            return None
        
        # Sort by load (ascending) and latency (ascending)
        available_servers.sort(key=lambda x: (x.load, x.latency))
        return available_servers[0]
    
    async def rotate_server(self, country: Optional[str] = None) -> bool:
        """Rotate to a different server"""
        try:
            current_server_name = self.current_server.name if self.current_server else None
            
            # Get available servers excluding current one
            available_servers = [s for s in self.servers.values() if s.name != current_server_name]
            
            if country:
                available_servers = [s for s in available_servers if s.country.lower() == country.lower()]
            
            if not available_servers:
                self.logger.warning("No available servers for rotation", country=country)
                return False
            
            # Select server with lowest load
            optimal_server = min(available_servers, key=lambda x: x.load)
            
            success = await self.connect_to_server(optimal_server.name)
            if success:
                self.logger.info("Rotated to new server", server_name=optimal_server.name)
            
            return success
            
        except Exception as e:
            self.logger.error("Failed to rotate server", error=str(e))
            return False
    
    def get_proxy_config(self) -> Optional[ProxyConfig]:
        """Get current proxy configuration"""
        if not self.current_server or self.connection_status != "Connected":
            return None
        
        return ProxyConfig(
            host=self.current_server.host,
            port=self.current_server.port,
            proxy_type=ProxyType.SOCKS5,
            provider=ProxyProvider.PRIVATE_INTERNET_ACCESS,
            country=self.current_server.country,
            region=self.current_server.region,
            city=self.current_server.city,
            status=ProxyStatus.ACTIVE,
            health_score=1.0 - (self.current_server.load / 100),
            success_rate=1.0
        )
    
    async def _run_pia_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run PIA CLI command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout.decode(),
                stderr=stderr.decode()
            )
        except Exception as e:
            self.logger.error("Failed to run PIA command", command=command, error=str(e))
            raise
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        info = {
            "status": self.connection_status,
            "current_server": None,
            "servers_available": len(self.servers),
            "last_updated": time.time()
        }
        
        if self.current_server:
            info["current_server"] = {
                "name": self.current_server.name,
                "host": self.current_server.host,
                "country": self.current_server.country,
                "region": self.current_server.region,
                "city": self.current_server.city,
                "load": self.current_server.load,
                "latency": self.current_server.latency
            }
        
        return info