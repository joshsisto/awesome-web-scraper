import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
import scrapy
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from twisted.internet import reactor, defer
import structlog
from fake_useragent import UserAgent
from common.models.scrape_request import ScrapeRequest, ScrapeMethod
from common.models.scrape_result import ScrapeResult, ScrapeStatus
from common.models.proxy_config import ProxyConfig

logger = structlog.get_logger()


class CustomUserAgentMiddleware(UserAgentMiddleware):
    """Custom user agent middleware for rotation"""
    
    def __init__(self):
        super().__init__()
        self.ua = UserAgent()
    
    def process_request(self, request, spider):
        request.headers['User-Agent'] = self.ua.random
        return None


class ProxyMiddleware:
    """Custom proxy middleware"""
    
    def __init__(self):
        self.proxy_config: Optional[ProxyConfig] = None
    
    def set_proxy(self, proxy_config: ProxyConfig):
        self.proxy_config = proxy_config
    
    def process_request(self, request, spider):
        if self.proxy_config:
            request.meta['proxy'] = self.proxy_config.get_proxy_url()
            if self.proxy_config.username and self.proxy_config.password:
                request.meta['proxy_auth'] = f"{self.proxy_config.username}:{self.proxy_config.password}"
        return None


class ScrapyExtractorSpider(Spider):
    """Dynamic Scrapy spider for extraction"""
    
    name = 'scraper_spider'
    
    def __init__(self, scrape_request: ScrapeRequest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scrape_request = scrape_request
        self.start_urls = [str(scrape_request.url)]
        self.results = []
        self.logger = logger.bind(service="scrapy_spider")
        
        # Configure spider settings
        self.download_delay = 1 if scrape_request.human_like_delays else 0
        self.randomize_download_delay = scrape_request.human_like_delays
        
    def start_requests(self):
        """Generate initial requests"""
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                headers=self.scrape_request.headers,
                cookies=self.scrape_request.cookies,
                meta={
                    'download_timeout': self.scrape_request.timeout,
                    'dont_retry': self.scrape_request.max_retries == 0,
                    'retry_times': self.scrape_request.max_retries,
                    'scrape_request': self.scrape_request
                }
            )
    
    def parse(self, response: Response):
        """Parse response and extract data"""
        start_time = time.time()
        
        try:
            # Extract data based on selectors
            extracted_data = {}
            
            if self.scrape_request.selectors:
                for field, selector in self.scrape_request.selectors.items():
                    try:
                        if selector.startswith('//'):
                            # XPath selector
                            elements = response.xpath(selector)
                        else:
                            # CSS selector
                            elements = response.css(selector)
                        
                        if elements:
                            if len(elements) == 1:
                                extracted_data[field] = elements.get()
                            else:
                                extracted_data[field] = elements.getall()
                        else:
                            extracted_data[field] = None
                    except Exception as e:
                        self.logger.error(f"Failed to extract {field}", selector=selector, error=str(e))
                        extracted_data[field] = None
            
            # Extract links if requested
            links = []
            if self.scrape_request.extract_links:
                try:
                    link_elements = response.css('a::attr(href)').getall()
                    for link in link_elements:
                        absolute_url = urljoin(response.url, link)
                        links.append(absolute_url)
                except Exception as e:
                    self.logger.error("Failed to extract links", error=str(e))
            
            # Extract images if requested
            images = []
            if self.scrape_request.extract_images:
                try:
                    img_elements = response.css('img::attr(src)').getall()
                    for img in img_elements:
                        absolute_url = urljoin(response.url, img)
                        images.append(absolute_url)
                except Exception as e:
                    self.logger.error("Failed to extract images", error=str(e))
            
            # Extract text content if requested
            text_content = ""
            if self.scrape_request.extract_text:
                try:
                    text_content = response.css('body::text').getall()
                    text_content = ' '.join(text_content).strip()
                except Exception as e:
                    self.logger.error("Failed to extract text", error=str(e))
            
            # Build result
            result = ScrapeResult(
                request_id=str(self.scrape_request.id) if self.scrape_request.id else "",
                status=ScrapeStatus.SUCCESS,
                status_code=response.status,
                response_headers=dict(response.headers),
                response_time=time.time() - start_time,
                data=extracted_data,
                raw_html=response.text if len(response.text) < 1000000 else response.text[:1000000],  # Limit raw HTML
                links=links,
                images=images,
                final_url=response.url,
                success_score=self._calculate_success_score(extracted_data, response)
            )
            
            self.results.append(result)
            
            # Log success
            self.logger.info(
                "Successfully scraped page",
                url=response.url,
                status_code=response.status,
                data_fields=len(extracted_data),
                links_found=len(links),
                images_found=len(images)
            )
            
        except Exception as e:
            # Handle parsing errors
            error_result = ScrapeResult(
                request_id=str(self.scrape_request.id) if self.scrape_request.id else "",
                status=ScrapeStatus.FAILED,
                status_code=response.status,
                response_time=time.time() - start_time,
                error_message=str(e),
                error_type=type(e).__name__,
                final_url=response.url
            )
            
            self.results.append(error_result)
            self.logger.error("Failed to parse response", url=response.url, error=str(e))
    
    def _calculate_success_score(self, extracted_data: Dict[str, Any], response: Response) -> float:
        """Calculate success score based on extracted data quality"""
        score = 0.0
        
        # Base score for successful response
        if response.status == 200:
            score += 0.3
        
        # Score for extracted data
        if extracted_data:
            non_empty_fields = sum(1 for v in extracted_data.values() if v is not None and v != "")
            total_fields = len(extracted_data)
            if total_fields > 0:
                score += 0.7 * (non_empty_fields / total_fields)
        
        return min(1.0, score)


class ScrapyService:
    """Scrapy-based scraping service"""
    
    def __init__(self):
        self.logger = logger.bind(service="scrapy_service")
        self.proxy_middleware = ProxyMiddleware()
        self.runner: Optional[CrawlerRunner] = None
        self.setup_runner()
    
    def setup_runner(self):
        """Setup Scrapy crawler runner"""
        settings = get_project_settings()
        
        # Configure settings
        settings.update({
            'ROBOTSTXT_OBEY': False,
            'DOWNLOAD_DELAY': 1,
            'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
            'CONCURRENT_REQUESTS': 16,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 1,
            'AUTOTHROTTLE_MAX_DELAY': 10,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
            'AUTOTHROTTLE_DEBUG': False,
            'COOKIES_ENABLED': True,
            'TELNETCONSOLE_ENABLED': False,
            'LOG_LEVEL': 'INFO',
            'RETRY_ENABLED': True,
            'RETRY_TIMES': 3,
            'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
            'DOWNLOADER_MIDDLEWARES': {
                'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
                'services.extraction.scrapy_service.CustomUserAgentMiddleware': 400,
                'services.extraction.scrapy_service.ProxyMiddleware': 350,
                'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
            }
        })
        
        self.runner = CrawlerRunner(settings)
    
    async def scrape(self, scrape_request: ScrapeRequest) -> ScrapeResult:
        """Perform scraping using Scrapy"""
        if scrape_request.method != ScrapeMethod.SCRAPY:
            raise ValueError(f"Invalid method for ScrapyService: {scrape_request.method}")
        
        try:
            self.logger.info("Starting Scrapy scraping", url=str(scrape_request.url))
            
            # Set up proxy if provided
            if scrape_request.use_proxy and hasattr(self, 'proxy_config') and self.proxy_config:
                self.proxy_middleware.set_proxy(self.proxy_config)
            
            # Create and run spider
            spider = ScrapyExtractorSpider(scrape_request)
            
            # Run spider in reactor
            deferred = self.runner.crawl(spider)
            await self._twisted_to_asyncio(deferred)
            
            # Get results
            if spider.results:
                return spider.results[0]  # Return first result
            else:
                # No results, create error result
                return ScrapeResult(
                    request_id=str(scrape_request.id) if scrape_request.id else "",
                    status=ScrapeStatus.FAILED,
                    error_message="No results returned from spider",
                    error_type="NoResultsError"
                )
                
        except Exception as e:
            self.logger.error("Scrapy scraping failed", url=str(scrape_request.url), error=str(e))
            return ScrapeResult(
                request_id=str(scrape_request.id) if scrape_request.id else "",
                status=ScrapeStatus.FAILED,
                error_message=str(e),
                error_type=type(e).__name__
            )
    
    async def _twisted_to_asyncio(self, deferred):
        """Convert Twisted deferred to asyncio future"""
        future = asyncio.Future()
        
        def success(result):
            if not future.done():
                future.set_result(result)
        
        def error(failure):
            if not future.done():
                future.set_exception(failure.value)
        
        deferred.addCallback(success)
        deferred.addErrback(error)
        
        return await future
    
    def set_proxy_config(self, proxy_config: ProxyConfig):
        """Set proxy configuration"""
        self.proxy_config = proxy_config
        self.proxy_middleware.set_proxy(proxy_config)
    
    async def batch_scrape(self, scrape_requests: List[ScrapeRequest]) -> List[ScrapeResult]:
        """Perform batch scraping"""
        results = []
        
        for request in scrape_requests:
            try:
                result = await self.scrape(request)
                results.append(result)
            except Exception as e:
                error_result = ScrapeResult(
                    request_id=str(request.id) if request.id else "",
                    status=ScrapeStatus.FAILED,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                results.append(error_result)
        
        return results
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Get supported features for this service"""
        return {
            "javascript": False,
            "cookies": True,
            "sessions": True,
            "file_downloads": True,
            "form_submissions": True,
            "concurrent_requests": True,
            "auto_retry": True,
            "proxy_support": True,
            "user_agent_rotation": True,
            "rate_limiting": True
        }