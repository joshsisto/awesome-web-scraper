from enum import Enum
from typing import Optional, Dict, Any
from pydantic import Field, validator
from .base import BaseModel


class ProxyType(str, Enum):
    """Proxy type"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    VPN = "vpn"


class ProxyProvider(str, Enum):
    """Proxy provider"""
    PRIVATE_INTERNET_ACCESS = "pia"
    BRIGHT_DATA = "bright_data"
    SMARTPROXY = "smartproxy"
    OXYLABS = "oxylabs"
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"


class ProxyStatus(str, Enum):
    """Proxy status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    FAILED = "failed"


class ProxyConfig(BaseModel):
    """Model for proxy configuration"""
    
    # Basic proxy information
    host: str = Field(..., description="Proxy host")
    port: int = Field(..., description="Proxy port")
    proxy_type: ProxyType = Field(..., description="Proxy type")
    provider: ProxyProvider = Field(..., description="Proxy provider")
    
    # Authentication
    username: Optional[str] = Field(default=None, description="Proxy username")
    password: Optional[str] = Field(default=None, description="Proxy password")
    
    # Geographic information
    country: Optional[str] = Field(default=None, description="Proxy country code")
    region: Optional[str] = Field(default=None, description="Proxy region")
    city: Optional[str] = Field(default=None, description="Proxy city")
    
    # Status and health
    status: ProxyStatus = Field(default=ProxyStatus.ACTIVE, description="Proxy status")
    health_score: float = Field(default=1.0, description="Health score (0-1)")
    success_rate: float = Field(default=1.0, description="Success rate (0-1)")
    
    # Performance metrics
    average_response_time: Optional[float] = Field(default=None, description="Average response time")
    last_used: Optional[str] = Field(default=None, description="Last used timestamp")
    total_requests: int = Field(default=0, description="Total requests made")
    failed_requests: int = Field(default=0, description="Failed requests count")
    
    # Rate limiting
    requests_per_minute: Optional[int] = Field(default=None, description="Rate limit per minute")
    concurrent_limit: Optional[int] = Field(default=None, description="Concurrent request limit")
    
    # VPN specific configuration
    vpn_config: Optional[Dict[str, Any]] = Field(default=None, description="VPN configuration")
    
    # Custom configuration
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('health_score', 'success_rate')
    def validate_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v
    
    def get_proxy_url(self) -> str:
        """Generate proxy URL string"""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"
    
    def update_health_score(self, success: bool) -> None:
        """Update health score based on request success"""
        self.total_requests += 1
        if not success:
            self.failed_requests += 1
        
        # Calculate success rate
        self.success_rate = (self.total_requests - self.failed_requests) / self.total_requests
        
        # Update health score (weighted average)
        if success:
            self.health_score = min(1.0, self.health_score + 0.01)
        else:
            self.health_score = max(0.0, self.health_score - 0.05)
    
    class Config:
        json_schema_extra = {
            "example": {
                "host": "proxy.privateinternetaccess.com",
                "port": 1080,
                "proxy_type": "socks5",
                "provider": "pia",
                "username": "username",
                "password": "password",
                "country": "US",
                "region": "California",
                "city": "Los Angeles",
                "status": "active",
                "health_score": 0.95,
                "success_rate": 0.98
            }
        }