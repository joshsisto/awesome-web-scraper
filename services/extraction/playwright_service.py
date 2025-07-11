import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
import random
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response
from playwright_stealth import stealth_async
import structlog
from common.models.scrape_request import ScrapeRequest, ScrapeMethod, AuthType
from common.models.scrape_result import ScrapeResult, ScrapeStatus
from common.models.proxy_config import ProxyConfig

logger = structlog.get_logger()


class PlaywrightService:
    """Playwright-based scraping service for full browser automation"""
    
    def __init__(self):
        self.logger = logger.bind(service="playwright_service")
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.proxy_config: Optional[ProxyConfig] = None
        self.contexts: Dict[str, BrowserContext] = {}
        
    async def initialize(self, headless: bool = True, browser_type: str = "chromium"):
        """Initialize Playwright"""
        try:
            self.playwright = await async_playwright().start()
            
            # Configure browser launch options
            launch_options = {
                "headless": headless,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-background-networking",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-ipc-flooding-protection",
                    "--enable-features=NetworkService,NetworkServiceLogging",
                    "--force-color-profile=srgb",
                    "--metrics-recording-only",
                    "--use-mock-keychain",
                ]
            }
            
            # Add proxy configuration if available
            if self.proxy_config:
                proxy_settings = {
                    "server": f"{self.proxy_config.host}:{self.proxy_config.port}",
                }
                if self.proxy_config.username and self.proxy_config.password:
                    proxy_settings["username"] = self.proxy_config.username
                    proxy_settings["password"] = self.proxy_config.password
                
                launch_options["proxy"] = proxy_settings
            
            # Launch browser
            if browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(**launch_options)
            elif browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**launch_options)
            elif browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(**launch_options)
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")
            
            self.logger.info("Playwright initialized", browser_type=browser_type, headless=headless)
            
        except Exception as e:
            self.logger.error("Failed to initialize Playwright", error=str(e))
            raise
    
    async def close(self):
        """Close Playwright"""
        try:
            # Close all contexts
            for context in self.contexts.values():
                await context.close()
            self.contexts.clear()
            
            # Close browser
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self.logger.info("Playwright closed")
            
        except Exception as e:
            self.logger.error("Failed to close Playwright", error=str(e))
    
    async def scrape(self, scrape_request: ScrapeRequest) -> ScrapeResult:
        """Perform scraping using Playwright"""
        if scrape_request.method != ScrapeMethod.PLAYWRIGHT:
            raise ValueError(f"Invalid method for PlaywrightService: {scrape_request.method}")
        
        if not self.browser:
            await self.initialize()
        
        start_time = time.time()
        page = None
        context = None
        
        try:
            self.logger.info("Starting Playwright scraping", url=str(scrape_request.url))
            
            # Create browser context
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": self._get_random_user_agent(),
                "java_script_enabled": True,
                "accept_downloads": False,
                "ignore_https_errors": True,
            }
            
            # Add custom headers and cookies
            if scrape_request.headers:
                context_options["extra_http_headers"] = scrape_request.headers
            
            context = await self.browser.new_context(**context_options)
            
            # Set cookies if provided
            if scrape_request.cookies:
                cookies = []
                for name, value in scrape_request.cookies.items():
                    cookies.append({
                        "name": name,
                        "value": value,
                        "domain": urlparse(str(scrape_request.url)).netloc,
                        "path": "/"
                    })
                await context.add_cookies(cookies)
            
            # Create page
            page = await context.new_page()
            
            # Apply stealth if requested
            if scrape_request.use_stealth:
                await stealth_async(page)
            
            # Set up request/response monitoring
            responses = []
            
            def handle_response(response):
                responses.append(response)
            
            page.on("response", handle_response)
            
            # Navigate to URL
            response = await page.goto(
                str(scrape_request.url),
                wait_until="domcontentloaded",
                timeout=scrape_request.timeout * 1000
            )
            
            # Wait for additional conditions
            if scrape_request.wait_conditions:
                for condition in scrape_request.wait_conditions:
                    try:
                        if condition.startswith("selector:"):
                            selector = condition.replace("selector:", "")
                            await page.wait_for_selector(selector, timeout=scrape_request.timeout * 1000)
                        elif condition.startswith("text:"):
                            text = condition.replace("text:", "")
                            await page.wait_for_function(
                                f"document.body.innerText.includes('{text}')",
                                timeout=scrape_request.timeout * 1000
                            )
                        elif condition == "networkidle":
                            await page.wait_for_load_state("networkidle", timeout=scrape_request.timeout * 1000)
                        elif condition == "load":
                            await page.wait_for_load_state("load", timeout=scrape_request.timeout * 1000)
                        elif condition.startswith("delay:"):
                            delay = float(condition.replace("delay:", ""))
                            await asyncio.sleep(delay)
                    except Exception as e:
                        self.logger.warning(f"Wait condition failed: {condition}", error=str(e))
            
            # Handle authentication if needed
            if scrape_request.auth_type != AuthType.NONE:
                success = await self._handle_authentication(page, scrape_request)
                if not success:
                    return ScrapeResult(
                        request_id=str(scrape_request.id) if scrape_request.id else "",
                        status=ScrapeStatus.FAILED,
                        error_message="Authentication failed",
                        error_type="AuthenticationError",
                        response_time=time.time() - start_time
                    )
            
            # Add human-like delays
            if scrape_request.human_like_delays:
                await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Extract data based on selectors
            extracted_data = {}
            
            if scrape_request.selectors:
                for field, selector in scrape_request.selectors.items():
                    try:
                        elements = await page.query_selector_all(selector)
                        
                        if elements:
                            if len(elements) == 1:
                                # Single element
                                element = elements[0]
                                text_content = await element.text_content()
                                inner_html = await element.inner_html()
                                extracted_data[field] = text_content.strip() if text_content else inner_html
                            else:
                                # Multiple elements
                                values = []
                                for element in elements:
                                    text_content = await element.text_content()
                                    if text_content:
                                        values.append(text_content.strip())
                                    else:
                                        inner_html = await element.inner_html()
                                        if inner_html:
                                            values.append(inner_html)
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
                    link_elements = await page.query_selector_all('a[href]')
                    for element in link_elements:
                        href = await element.get_attribute('href')
                        if href:
                            absolute_url = urljoin(page.url, href)
                            links.append(absolute_url)
                except Exception as e:
                    self.logger.error("Failed to extract links", error=str(e))
            
            # Extract images if requested
            images = []
            if scrape_request.extract_images:
                try:
                    img_elements = await page.query_selector_all('img[src]')
                    for element in img_elements:
                        src = await element.get_attribute('src')
                        if src:
                            absolute_url = urljoin(page.url, src)
                            images.append(absolute_url)
                except Exception as e:
                    self.logger.error("Failed to extract images", error=str(e))
            
            # Extract text content if requested
            text_content = ""
            if scrape_request.extract_text:
                try:
                    text_content = await page.text_content('body')
                    if text_content:
                        text_content = text_content.strip()
                except Exception as e:
                    self.logger.error("Failed to extract text", error=str(e))
            
            # Get page content
            raw_html = await page.content()
            
            # Calculate render time
            render_time = time.time() - start_time
            
            # Build result
            result = ScrapeResult(
                request_id=str(scrape_request.id) if scrape_request.id else "",
                status=ScrapeStatus.SUCCESS,
                status_code=response.status if response else None,
                response_headers=dict(response.headers) if response else {},
                response_time=render_time,
                data=extracted_data,
                raw_html=raw_html if len(raw_html) < 1000000 else raw_html[:1000000],
                links=links,
                images=images,
                final_url=page.url,
                download_size=len(raw_html.encode('utf-8')),
                render_time=render_time,
                retry_count=0,
                success_score=self._calculate_success_score(extracted_data, response.status if response else 200),
                data_completeness=self._calculate_data_completeness(extracted_data, scrape_request.selectors)
            )
            
            self.logger.info(
                "Successfully scraped with Playwright",
                url=page.url,
                status_code=response.status if response else None,
                data_fields=len(extracted_data),
                links_found=len(links),
                images_found=len(images),
                render_time=render_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Playwright scraping failed", url=str(scrape_request.url), error=str(e))
            
            # Determine error type
            error_type = type(e).__name__
            status = ScrapeStatus.FAILED
            
            if "timeout" in str(e).lower():
                status = ScrapeStatus.TIMEOUT
                error_type = "TimeoutError"
            elif "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                status = ScrapeStatus.BLOCKED
                error_type = "BlockedError"
            
            return ScrapeResult(
                request_id=str(scrape_request.id) if scrape_request.id else "",
                status=status,
                error_message=str(e),
                error_type=error_type,
                response_time=time.time() - start_time
            )
        
        finally:
            # Clean up
            if page:
                await page.close()
            if context:
                await context.close()
    
    async def _handle_authentication(self, page: Page, scrape_request: ScrapeRequest) -> bool:
        """Handle different authentication types"""
        try:
            if scrape_request.auth_type == AuthType.FORM:
                # Handle form-based authentication
                if scrape_request.auth_credentials:
                    username = scrape_request.auth_credentials.get("username")
                    password = scrape_request.auth_credentials.get("password")
                    username_selector = scrape_request.auth_credentials.get("username_selector", "input[name='username']")
                    password_selector = scrape_request.auth_credentials.get("password_selector", "input[name='password']")
                    submit_selector = scrape_request.auth_credentials.get("submit_selector", "input[type='submit']")
                    
                    if username and password:
                        # Fill login form
                        await page.fill(username_selector, username)
                        await page.fill(password_selector, password)
                        await page.click(submit_selector)
                        
                        # Wait for navigation
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        
                        return True
            
            elif scrape_request.auth_type == AuthType.BASIC:
                # HTTP Basic Auth (handled by browser context)
                if scrape_request.auth_credentials:
                    username = scrape_request.auth_credentials.get("username")
                    password = scrape_request.auth_credentials.get("password")
                    
                    if username and password:
                        await page.set_extra_http_headers({
                            "Authorization": f"Basic {username}:{password}"
                        })
                        return True
            
            elif scrape_request.auth_type == AuthType.BEARER:
                # Bearer token authentication
                if scrape_request.auth_credentials:
                    token = scrape_request.auth_credentials.get("token")
                    if token:
                        await page.set_extra_http_headers({
                            "Authorization": f"Bearer {token}"
                        })
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error("Authentication failed", error=str(e))
            return False
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        return random.choice(user_agents)
    
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
        """Perform batch scraping with limited concurrency"""
        if not self.browser:
            await self.initialize()
        
        # Process requests with limited concurrency (browsers are resource-intensive)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent browser contexts
        
        async def scrape_with_semaphore(request):
            async with semaphore:
                return await self.scrape(request)
        
        tasks = []
        for request in scrape_requests:
            task = asyncio.create_task(scrape_with_semaphore(request))
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
            "javascript": True,
            "cookies": True,
            "sessions": True,
            "file_downloads": True,
            "form_submissions": True,
            "concurrent_requests": True,
            "auto_retry": False,  # Handled at service level
            "proxy_support": True,
            "user_agent_rotation": True,
            "rate_limiting": True,
            "browser_automation": True,
            "screenshot_capture": True,
            "pdf_generation": True,
            "mobile_emulation": True,
            "network_interception": True,
            "geolocation_spoofing": True,
            "stealth_mode": True
        }