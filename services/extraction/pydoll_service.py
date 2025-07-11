import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
import httpx
from selectolax.parser import HTMLParser
from fake_useragent import UserAgent
import structlog
from common.models.scrape_request import ScrapeRequest, ScrapeMethod
from common.models.scrape_result import ScrapeResult, ScrapeStatus
from common.models.proxy_config import ProxyConfig

logger = structlog.get_logger()


class PyDollService:
    """PyDoll-style service using httpx + selectolax for fast middleground scraping"""
    
    def __init__(self):
        self.logger = logger.bind(service="pydoll_service")
        self.ua = UserAgent()
        self.proxy_config: Optional[ProxyConfig] = None
        self.session: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize the service"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        self.logger.info("PyDoll service initialized")
    
    async def close(self):
        """Close the service"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def scrape(self, scrape_request: ScrapeRequest) -> ScrapeResult:
        """Perform scraping using httpx + selectolax"""
        if scrape_request.method != ScrapeMethod.PYDOLL:
            raise ValueError(f"Invalid method for PyDollService: {scrape_request.method}")
        
        if not self.session:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            self.logger.info("Starting PyDoll scraping", url=str(scrape_request.url))
            
            # Prepare headers
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Add custom headers
            if scrape_request.headers:
                headers.update(scrape_request.headers)
            
            # Prepare cookies
            cookies = scrape_request.cookies or {}
            
            # Configure proxy
            proxies = None
            if scrape_request.use_proxy and self.proxy_config:
                proxies = {
                    'http://': self.proxy_config.get_proxy_url(),
                    'https://': self.proxy_config.get_proxy_url()
                }
            
            # Add human-like delay
            if scrape_request.human_like_delays:
                await asyncio.sleep(0.5 + (time.time() % 2))
            
            # Make request with retries
            response = None
            last_error = None
            
            for attempt in range(scrape_request.max_retries + 1):
                try:
                    response = await self.session.get(
                        str(scrape_request.url),
                        headers=headers,
                        cookies=cookies,
                        timeout=scrape_request.timeout,
                        proxies=proxies
                    )
                    
                    # Check if request was successful
                    if response.status_code in [200, 201, 202]:
                        break
                    elif response.status_code == 429:  # Rate limited
                        if attempt < scrape_request.max_retries:
                            wait_time = (2 ** attempt) + (time.time() % 3)  # Exponential backoff with jitter
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return self._create_error_result(
                                scrape_request, 
                                "Rate limited", 
                                "RateLimitError", 
                                response.status_code,
                                time.time() - start_time
                            )
                    else:
                        # Other HTTP errors
                        if attempt < scrape_request.max_retries:
                            wait_time = scrape_request.retry_delay + (time.time() % 2)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return self._create_error_result(
                                scrape_request,
                                f"HTTP {response.status_code}",
                                "HTTPError",
                                response.status_code,
                                time.time() - start_time
                            )
                
                except httpx.TimeoutException as e:
                    last_error = e
                    if attempt < scrape_request.max_retries:
                        wait_time = scrape_request.retry_delay + (time.time() % 2)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return self._create_error_result(
                            scrape_request,
                            "Request timeout",
                            "TimeoutError",
                            None,
                            time.time() - start_time
                        )
                
                except Exception as e:
                    last_error = e
                    if attempt < scrape_request.max_retries:
                        wait_time = scrape_request.retry_delay + (time.time() % 2)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return self._create_error_result(
                            scrape_request,
                            str(e),
                            type(e).__name__,
                            None,
                            time.time() - start_time
                        )
            
            if not response:
                return self._create_error_result(
                    scrape_request,
                    str(last_error) if last_error else "Unknown error",
                    "RequestError",
                    None,
                    time.time() - start_time
                )
            
            # Parse HTML using selectolax
            parser = HTMLParser(response.text)
            
            # Extract data based on selectors
            extracted_data = {}
            
            if scrape_request.selectors:
                for field, selector in scrape_request.selectors.items():
                    try:
                        elements = parser.css(selector)
                        
                        if elements:
                            if len(elements) == 1:
                                # Single element
                                element = elements[0]
                                if element.text():
                                    extracted_data[field] = element.text().strip()
                                else:
                                    extracted_data[field] = element.html if element.html else None
                            else:
                                # Multiple elements
                                values = []
                                for element in elements:
                                    if element.text():
                                        values.append(element.text().strip())
                                    elif element.html:
                                        values.append(element.html)
                                extracted_data[field] = values
                        else:
                            extracted_data[field] = None
                    except Exception as e:
                        self.logger.error(f"Failed to extract {field}", selector=selector, error=str(e))
                        extracted_data[field] = None
            
            # Extract links if requested
            links = []
            if scrape_request.extract_links:
                try:
                    link_elements = parser.css('a')
                    for element in link_elements:
                        href = element.attributes.get('href')
                        if href:
                            absolute_url = urljoin(str(response.url), href)
                            links.append(absolute_url)
                except Exception as e:
                    self.logger.error("Failed to extract links", error=str(e))
            
            # Extract images if requested
            images = []
            if scrape_request.extract_images:
                try:
                    img_elements = parser.css('img')
                    for element in img_elements:
                        src = element.attributes.get('src')
                        if src:
                            absolute_url = urljoin(str(response.url), src)
                            images.append(absolute_url)
                except Exception as e:
                    self.logger.error("Failed to extract images", error=str(e))
            
            # Extract text content if requested
            text_content = ""
            if scrape_request.extract_text:
                try:
                    body = parser.css_first('body')
                    if body:
                        text_content = body.text(strip=True)
                except Exception as e:
                    self.logger.error("Failed to extract text", error=str(e))
            
            # Build result
            result = ScrapeResult(
                request_id=str(scrape_request.id) if scrape_request.id else "",
                status=ScrapeStatus.SUCCESS,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_time=time.time() - start_time,
                data=extracted_data,
                raw_html=response.text if len(response.text) < 1000000 else response.text[:1000000],
                links=links,
                images=images,
                final_url=str(response.url),
                download_size=len(response.content) if response.content else 0,
                retry_count=0,  # Would need to track this properly
                success_score=self._calculate_success_score(extracted_data, response.status_code),
                data_completeness=self._calculate_data_completeness(extracted_data, scrape_request.selectors)
            )
            
            self.logger.info(
                "Successfully scraped with PyDoll",
                url=str(response.url),
                status_code=response.status_code,
                data_fields=len(extracted_data),
                links_found=len(links),
                images_found=len(images),
                response_time=result.response_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error("PyDoll scraping failed", url=str(scrape_request.url), error=str(e))
            return self._create_error_result(
                scrape_request,
                str(e),
                type(e).__name__,
                None,
                time.time() - start_time
            )
    
    def _create_error_result(
        self, 
        scrape_request: ScrapeRequest, 
        error_message: str, 
        error_type: str, 
        status_code: Optional[int],
        response_time: float
    ) -> ScrapeResult:
        """Create error result"""
        status = ScrapeStatus.FAILED
        
        if error_type == "TimeoutError":
            status = ScrapeStatus.TIMEOUT
        elif error_type == "RateLimitError":
            status = ScrapeStatus.RATE_LIMITED
        elif status_code and status_code == 403:
            status = ScrapeStatus.BLOCKED
        
        return ScrapeResult(
            request_id=str(scrape_request.id) if scrape_request.id else "",
            status=status,
            status_code=status_code,
            response_time=response_time,
            error_message=error_message,
            error_type=error_type
        )
    
    def _calculate_success_score(self, extracted_data: Dict[str, Any], status_code: int) -> float:
        """Calculate success score based on extracted data quality"""
        score = 0.0
        
        # Base score for successful response
        if status_code == 200:
            score += 0.3
        elif 200 <= status_code < 300:
            score += 0.2
        
        # Score for extracted data
        if extracted_data:
            non_empty_fields = sum(1 for v in extracted_data.values() if v is not None and v != "" and v != [])
            total_fields = len(extracted_data)
            if total_fields > 0:
                score += 0.7 * (non_empty_fields / total_fields)
        
        return min(1.0, score)
    
    def _calculate_data_completeness(self, extracted_data: Dict[str, Any], selectors: Dict[str, str]) -> float:
        """Calculate data completeness score"""
        if not selectors:
            return 1.0
        
        if not extracted_data:
            return 0.0
        
        successful_extractions = sum(1 for field in selectors.keys() if field in extracted_data and extracted_data[field] is not None)
        return successful_extractions / len(selectors)
    
    def set_proxy_config(self, proxy_config: ProxyConfig):
        """Set proxy configuration"""
        self.proxy_config = proxy_config
    
    async def batch_scrape(self, scrape_requests: List[ScrapeRequest]) -> List[ScrapeResult]:
        """Perform batch scraping with concurrency"""
        if not self.session:
            await self.initialize()
        
        # Process requests concurrently
        tasks = []
        for request in scrape_requests:
            task = asyncio.create_task(self.scrape(request))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ScrapeResult(
                    request_id=str(scrape_requests[i].id) if scrape_requests[i].id else "",
                    status=ScrapeStatus.FAILED,
                    error_message=str(result),
                    error_type=type(result).__name__
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
        
        return final_results
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Get supported features for this service"""
        return {
            "javascript": False,
            "cookies": True,
            "sessions": True,
            "file_downloads": True,
            "form_submissions": False,
            "concurrent_requests": True,
            "auto_retry": True,
            "proxy_support": True,
            "user_agent_rotation": True,
            "rate_limiting": True,
            "fast_parsing": True,
            "memory_efficient": True
        }