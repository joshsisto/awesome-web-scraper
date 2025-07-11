from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import Field, HttpUrl
from .base import BaseModel


class ScrapeMethod(str, Enum):
    """Scraping method to use"""
    SCRAPY = "scrapy"
    PYDOLL = "pydoll"  # Using httpx + selectolax
    PLAYWRIGHT = "playwright"


class AuthType(str, Enum):
    """Authentication type"""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH = "oauth"
    FORM = "form"
    CUSTOM = "custom"


class Priority(str, Enum):
    """Request priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ScrapeRequest(BaseModel):
    """Model for scraping requests"""
    
    url: HttpUrl = Field(..., description="Target URL to scrape")
    method: ScrapeMethod = Field(default=ScrapeMethod.SCRAPY, description="Scraping method")
    priority: Priority = Field(default=Priority.NORMAL, description="Request priority")
    
    # Authentication
    auth_type: AuthType = Field(default=AuthType.NONE, description="Authentication type")
    auth_credentials: Optional[Dict[str, str]] = Field(default=None, description="Auth credentials")
    
    # Headers and cookies
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    cookies: Dict[str, str] = Field(default_factory=dict, description="HTTP cookies")
    
    # Scraping configuration
    selectors: Dict[str, str] = Field(default_factory=dict, description="CSS/XPath selectors")
    wait_conditions: List[str] = Field(default_factory=list, description="Wait conditions for dynamic content")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # Proxy configuration
    use_proxy: bool = Field(default=True, description="Use proxy for request")
    proxy_type: Optional[str] = Field(default=None, description="Proxy type preference")
    
    # Anti-detection
    use_stealth: bool = Field(default=True, description="Use stealth mode")
    human_like_delays: bool = Field(default=True, description="Use human-like delays")
    
    # Retry configuration
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")
    
    # Data extraction
    extract_links: bool = Field(default=False, description="Extract all links from page")
    extract_images: bool = Field(default=False, description="Extract image URLs")
    extract_text: bool = Field(default=True, description="Extract text content")
    
    # Callback configuration
    callback_url: Optional[HttpUrl] = Field(default=None, description="Webhook URL for results")
    
    # Custom configuration
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "method": "scrapy",
                "priority": "normal",
                "auth_type": "none",
                "headers": {"User-Agent": "Mozilla/5.0..."},
                "selectors": {
                    "title": "h1",
                    "content": ".content"
                },
                "use_proxy": True,
                "use_stealth": True,
                "timeout": 30
            }
        }