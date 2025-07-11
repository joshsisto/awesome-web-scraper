from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import Field, HttpUrl
from .base import BaseModel


class ScrapeStatus(str, Enum):
    """Scraping status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"


class ScrapeResult(BaseModel):
    """Model for scraping results"""
    
    request_id: str = Field(..., description="Reference to original request")
    status: ScrapeStatus = Field(..., description="Scraping status")
    
    # Response details
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    response_headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")
    
    # Extracted data
    data: Dict[str, Any] = Field(default_factory=dict, description="Extracted data")
    raw_html: Optional[str] = Field(default=None, description="Raw HTML content")
    
    # Links and media
    links: List[str] = Field(default_factory=list, description="Extracted links")
    images: List[str] = Field(default_factory=list, description="Extracted image URLs")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(default=None, description="Error type")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace for debugging")
    
    # Proxy information
    proxy_used: Optional[str] = Field(default=None, description="Proxy used for request")
    proxy_country: Optional[str] = Field(default=None, description="Proxy country")
    
    # Performance metrics
    download_size: Optional[int] = Field(default=None, description="Downloaded content size in bytes")
    render_time: Optional[float] = Field(default=None, description="Page render time for JS-heavy sites")
    
    # Retry information
    retry_count: int = Field(default=0, description="Number of retries attempted")
    final_url: Optional[HttpUrl] = Field(default=None, description="Final URL after redirects")
    
    # Quality metrics
    success_score: Optional[float] = Field(default=None, description="Success score (0-1)")
    data_completeness: Optional[float] = Field(default=None, description="Data completeness score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "64a1b2c3d4e5f6789012345",
                "status": "success",
                "status_code": 200,
                "response_time": 2.5,
                "data": {
                    "title": "Example Page",
                    "content": "This is example content..."
                },
                "links": ["https://example.com/page1", "https://example.com/page2"],
                "proxy_used": "192.168.1.100:8080",
                "success_score": 0.95
            }
        }