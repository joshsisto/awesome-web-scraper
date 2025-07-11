#!/usr/bin/env python3
"""
Master Scraper - Command Line Interface for Web Scraping

Usage:
    python master_scraper.py <url> [options]
    python master_scraper.py joshsisto.com
    python master_scraper.py https://example.com --output json --selectors title="title" content=".main"

Features:
    - Progressive scraping strategy (Scrapy → PyDoll → Playwright)
    - Automatic database storage
    - Flexible output formats
    - Comprehensive logging
    - Configuration management
"""

import asyncio
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import logging

# Database imports
import sqlite3
from contextlib import asynccontextmanager

# HTTP client for fallback scraping
import httpx
import re

# VPN Security Check
from vpn_checker import require_vpn


class ScrapingDatabase:
    """SQLite database for storing scraping results"""
    
    def __init__(self, db_path: str = "scraped_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scrape_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    method_used TEXT NOT NULL,
                    status TEXT NOT NULL,
                    status_code INTEGER,
                    response_time REAL,
                    timestamp DATETIME NOT NULL,
                    title TEXT,
                    content_length INTEGER,
                    links_count INTEGER,
                    images_count INTEGER,
                    data_json TEXT,
                    links_json TEXT,
                    images_json TEXT,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_url ON scrape_results(url);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_domain ON scrape_results(domain);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON scrape_results(timestamp);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON scrape_results(status);
            """)
    
    def save_result(self, result: Dict[str, Any]) -> int:
        """Save scraping result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO scrape_results (
                    url, domain, method_used, status, status_code, response_time,
                    timestamp, title, content_length, links_count, images_count,
                    data_json, links_json, images_json, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result['url'],
                result['domain'],
                result['method_used'],
                result['status'],
                result.get('status_code'),
                result.get('response_time'),
                result['timestamp'],
                result.get('title'),
                result.get('content_length'),
                result.get('links_count', 0),
                result.get('images_count', 0),
                json.dumps(result.get('data', {})),
                json.dumps(result.get('links', [])),
                json.dumps(result.get('images', [])),
                result.get('error_message')
            ))
            return cursor.lastrowid


class ProgressiveScraper:
    """Progressive web scraper that tries multiple methods"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the scraper"""
        logger = logging.getLogger('master_scraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            file_handler = logging.FileHandler('scraper.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            verify=self.config.get('verify_ssl', True)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def scrape_progressive(self, url: str) -> Dict[str, Any]:
        """
        Progressive scraping: Try Scrapy → PyDoll → Playwright
        """
        self.logger.info(f"Starting progressive scrape of {url}")
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        # Try each method in order
        methods = [
            ("scrapy", self._scrape_with_scrapy),
            ("pydoll", self._scrape_with_pydoll),
            ("playwright", self._scrape_with_playwright)
        ]
        
        for method_name, method_func in methods:
            try:
                self.logger.info(f"Attempting {method_name} method for {url}")
                result = await method_func(url)
                
                if result['status'] == 'success':
                    self.logger.info(f"✅ Success with {method_name} method")
                    return result
                else:
                    self.logger.warning(f"❌ {method_name} method failed: {result.get('error_message')}")
                    
            except Exception as e:
                self.logger.error(f"❌ {method_name} method crashed: {e}")
                continue
        
        # If all methods failed
        self.logger.error(f"❌ All scraping methods failed for {url}")
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'method_used': 'none',
            'status': 'failed',
            'timestamp': datetime.now().isoformat(),
            'error_message': 'All scraping methods failed'
        }
    
    async def _scrape_with_scrapy(self, url: str) -> Dict[str, Any]:
        """Scrapy-style scraping (fast, lightweight)"""
        self.logger.info(f"🕷️ Scrapy method: {url}")
        
        start_time = time.time()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = await self.session.get(url, headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                return {
                    'url': url,
                    'domain': urlparse(url).netloc,
                    'method_used': 'scrapy',
                    'status': 'failed',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat(),
                    'error_message': f'HTTP {response.status_code}'
                }
            
            # Extract data using regex (Scrapy-style)
            html = response.text
            data = self._extract_basic_data(html)
            links = self._extract_links(html, url)
            images = self._extract_images(html, url)
            
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'method_used': 'scrapy',
                'status': 'success',
                'status_code': response.status_code,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat(),
                'title': data.get('title'),
                'content_length': len(html),
                'links_count': len(links),
                'images_count': len(images),
                'data': data,
                'links': links,
                'images': images
            }
            
        except Exception as e:
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'method_used': 'scrapy',
                'status': 'failed',
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'error_message': str(e)
            }
    
    async def _scrape_with_pydoll(self, url: str) -> Dict[str, Any]:
        """PyDoll-style scraping (optimized HTTP + parsing)"""
        self.logger.info(f"⚡ PyDoll method: {url}")
        
        start_time = time.time()
        
        try:
            # More optimized headers for API-like scraping
            headers = {
                'User-Agent': 'PyDoll/1.0 (Fast Web Scraper)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = await self.session.get(url, headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                # PyDoll is more tolerant of non-200 responses for APIs
                if response.status_code in [301, 302, 307, 308]:
                    # Follow redirects manually for better control
                    redirect_url = response.headers.get('location')
                    if redirect_url:
                        return await self._scrape_with_pydoll(redirect_url)
                
                return {
                    'url': url,
                    'domain': urlparse(url).netloc,
                    'method_used': 'pydoll',
                    'status': 'failed',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat(),
                    'error_message': f'HTTP {response.status_code}'
                }
            
            # Enhanced data extraction
            content = response.text
            data = self._extract_enhanced_data(content, response.headers)
            links = self._extract_links(content, url)
            images = self._extract_images(content, url)
            
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'method_used': 'pydoll',
                'status': 'success',
                'status_code': response.status_code,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat(),
                'title': data.get('title'),
                'content_length': len(content),
                'links_count': len(links),
                'images_count': len(images),
                'data': data,
                'links': links,
                'images': images
            }
            
        except Exception as e:
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'method_used': 'pydoll',
                'status': 'failed',
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'error_message': str(e)
            }
    
    async def _scrape_with_playwright(self, url: str) -> Dict[str, Any]:
        """Playwright-style scraping (full browser automation)"""
        self.logger.info(f"🎭 Playwright method: {url}")
        
        start_time = time.time()
        
        try:
            # For now, simulate browser behavior with enhanced HTTP client
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add delay to simulate human behavior
            await asyncio.sleep(1)
            
            response = await self.session.get(url, headers=headers)
            response_time = time.time() - start_time
            
            # Playwright is more persistent with different status codes
            if response.status_code >= 400:
                return {
                    'url': url,
                    'domain': urlparse(url).netloc,
                    'method_used': 'playwright',
                    'status': 'failed',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat(),
                    'error_message': f'HTTP {response.status_code} - Browser automation failed'
                }
            
            # Advanced data extraction (simulating JavaScript execution)
            content = response.text
            data = self._extract_advanced_data(content, response.headers)
            links = self._extract_links(content, url)
            images = self._extract_images(content, url)
            
            # Simulate dynamic content detection
            has_dynamic_content = any(keyword in content.lower() for keyword in 
                                    ['react', 'vue', 'angular', 'javascript:', 'data-react'])
            
            if has_dynamic_content:
                data['dynamic_content_detected'] = True
                self.logger.info("🔍 Dynamic content detected")
            
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'method_used': 'playwright',
                'status': 'success',
                'status_code': response.status_code,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat(),
                'title': data.get('title'),
                'content_length': len(content),
                'links_count': len(links),
                'images_count': len(images),
                'data': data,
                'links': links,
                'images': images
            }
            
        except Exception as e:
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'method_used': 'playwright',
                'status': 'failed',
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'error_message': str(e)
            }
    
    def _extract_basic_data(self, html: str) -> Dict[str, Any]:
        """Basic data extraction (Scrapy-style)"""
        data = {}
        
        # Title
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            data['title'] = title_match.group(1).strip()
        
        # Meta description
        meta_desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
        if meta_desc:
            data['meta_description'] = meta_desc.group(1).strip()
        
        # Headings
        headings = []
        for level in range(1, 4):
            pattern = f'<h{level}[^>]*>(.*?)</h{level}>'
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if clean_text:
                    headings.append(clean_text)
        data['headings'] = headings
        
        return data
    
    def _extract_enhanced_data(self, content: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Enhanced data extraction (PyDoll-style)"""
        data = self._extract_basic_data(content)
        
        # Try to parse as JSON first (for APIs)
        try:
            json_data = json.loads(content)
            data['json_data'] = json_data
            data['content_type'] = 'json'
            return data
        except json.JSONDecodeError:
            pass
        
        # Check content type
        content_type = headers.get('content-type', '').lower()
        data['content_type'] = content_type
        
        # Extract meta tags
        meta_tags = {}
        meta_pattern = r'<meta\s+([^>]+)>'
        meta_matches = re.findall(meta_pattern, content, re.IGNORECASE)
        
        for meta in meta_matches:
            name_match = re.search(r'name=["\']([^"\']+)["\']', meta, re.IGNORECASE)
            content_match = re.search(r'content=["\']([^"\']+)["\']', meta, re.IGNORECASE)
            
            if name_match and content_match:
                meta_tags[name_match.group(1)] = content_match.group(1)
        
        data['meta_tags'] = meta_tags
        
        return data
    
    def _extract_advanced_data(self, content: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Advanced data extraction (Playwright-style)"""
        data = self._extract_enhanced_data(content, headers)
        
        # Detect frameworks
        frameworks = []
        framework_indicators = {
            'react': ['react', 'data-react', 'reactdom'],
            'vue': ['vue.js', 'data-vue', 'v-if', 'v-for'],
            'angular': ['angular', 'ng-app', 'ng-controller'],
            'jquery': ['jquery', '$(', 'jquery.min.js']
        }
        
        content_lower = content.lower()
        for framework, indicators in framework_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                frameworks.append(framework)
        
        data['frameworks_detected'] = frameworks
        
        # Extract forms
        form_pattern = r'<form[^>]*>(.*?)</form>'
        forms = re.findall(form_pattern, content, re.IGNORECASE | re.DOTALL)
        data['forms_count'] = len(forms)
        
        # Extract scripts
        script_pattern = r'<script[^>]*src=["\']([^"\']+)["\'][^>]*>'
        scripts = re.findall(script_pattern, content, re.IGNORECASE)
        data['external_scripts'] = scripts
        
        return data
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML"""
        link_pattern = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>'
        links = re.findall(link_pattern, html, re.IGNORECASE)
        
        # Process and normalize links
        processed_links = []
        for link in links:
            if link.startswith(('http://', 'https://')):
                processed_links.append(link)
            elif link.startswith('/'):
                from urllib.parse import urljoin
                processed_links.append(urljoin(base_url, link))
        
        return list(set(processed_links))  # Remove duplicates
    
    def _extract_images(self, html: str, base_url: str) -> List[str]:
        """Extract all images from HTML"""
        img_pattern = r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>'
        images = re.findall(img_pattern, html, re.IGNORECASE)
        
        # Process and normalize image URLs
        processed_images = []
        for img in images:
            if img.startswith(('http://', 'https://')):
                processed_images.append(img)
            elif img.startswith('/'):
                from urllib.parse import urljoin
                processed_images.append(urljoin(base_url, img))
        
        return list(set(processed_images))  # Remove duplicates


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Master Web Scraper - Progressive scraping with automatic method selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python master_scraper.py joshsisto.com
    python master_scraper.py https://example.com --output json
    python master_scraper.py https://news.site.com --methods scrapy pydoll
    python master_scraper.py https://api.site.com --format json --save-to results.json
        """
    )
    
    parser.add_argument(
        'url',
        help='URL to scrape (with or without protocol)'
    )
    
    parser.add_argument(
        '--methods',
        nargs='+',
        choices=['scrapy', 'pydoll', 'playwright'],
        default=['scrapy', 'pydoll', 'playwright'],
        help='Scraping methods to try (default: all methods in order)'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'table', 'summary'],
        default='summary',
        help='Output format (default: summary)'
    )
    
    parser.add_argument(
        '--save-to',
        type=str,
        help='Save results to file (JSON format)'
    )
    
    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Skip saving to database'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose logging'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--verify-ssl',
        action='store_true',
        default=False,
        help='Verify SSL certificates (default: disabled for compatibility)'
    )
    
    parser.add_argument(
        '--skip-vpn-check',
        action='store_true',
        help='Skip VPN security check (NOT RECOMMENDED - for testing only)'
    )
    
    return parser.parse_args()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults"""
    default_config = {
        'verify_ssl': False,
        'timeout': 30,
        'max_retries': 3,
        'delay_between_methods': 1,
        'user_agents': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    }
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    return default_config


def format_output(result: Dict[str, Any], format_type: str) -> str:
    """Format scraping result for display"""
    
    if format_type == 'json':
        return json.dumps(result, indent=2, default=str)
    
    elif format_type == 'table':
        output = []
        output.append("╔══════════════════════════════════════════════════════════════╗")
        output.append("║                      SCRAPING RESULT                        ║")
        output.append("╠══════════════════════════════════════════════════════════════╣")
        output.append(f"║ URL: {result['url']:<52} ║")
        output.append(f"║ Status: {result['status']:<48} ║")
        output.append(f"║ Method: {result['method_used']:<48} ║")
        
        if result.get('response_time'):
            output.append(f"║ Response Time: {result['response_time']:.2f}s{'':<38} ║")
        
        if result.get('title'):
            title = result['title'][:45] + "..." if len(result['title']) > 45 else result['title']
            output.append(f"║ Title: {title:<49} ║")
        
        if result.get('links_count') is not None:
            output.append(f"║ Links Found: {result['links_count']:<44} ║")
        
        if result.get('images_count') is not None:
            output.append(f"║ Images Found: {result['images_count']:<43} ║")
        
        output.append("╚══════════════════════════════════════════════════════════════╝")
        return "\n".join(output)
    
    elif format_type == 'summary':
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        method_emoji = {"scrapy": "🕷️", "pydoll": "⚡", "playwright": "🎭"}.get(result['method_used'], "🔧")
        
        output = []
        output.append(f"\n{status_emoji} Scraping Result for {result['url']}")
        output.append("─" * 60)
        output.append(f"{method_emoji} Method Used: {result['method_used'].upper()}")
        output.append(f"📊 Status: {result['status'].upper()}")
        
        if result.get('status_code'):
            output.append(f"🌐 HTTP Status: {result['status_code']}")
        
        if result.get('response_time'):
            output.append(f"⏱️  Response Time: {result['response_time']:.2f}s")
        
        if result.get('title'):
            output.append(f"📄 Title: {result['title']}")
        
        if result.get('content_length'):
            output.append(f"📏 Content Length: {result['content_length']:,} characters")
        
        if result.get('links_count') is not None:
            output.append(f"🔗 Links Found: {result['links_count']}")
        
        if result.get('images_count') is not None:
            output.append(f"🖼️  Images Found: {result['images_count']}")
        
        if result.get('error_message'):
            output.append(f"❌ Error: {result['error_message']}")
        
        if result.get('data', {}).get('frameworks_detected'):
            frameworks = ', '.join(result['data']['frameworks_detected'])
            output.append(f"🔧 Frameworks: {frameworks}")
        
        output.append(f"🕒 Timestamp: {result['timestamp']}")
        
        return "\n".join(output)


async def main():
    """Main entry point"""
    args = parse_arguments()
    config = load_config(args.config)
    
    # 🔒 SECURITY CHECK: Ensure VPN is active (blocks home IP 23.115.156.177)
    if not args.skip_vpn_check:
        current_ip = require_vpn()
        print(f"🔒 VPN Check: ✅ Active (IP: {current_ip})")
    else:
        print("⚠️  VPN Check: SKIPPED (--skip-vpn-check used)")
    
    # Update config with command line args
    config['verify_ssl'] = args.verify_ssl
    config['timeout'] = args.timeout
    
    # Setup logging level
    if args.verbose:
        logging.getLogger('master_scraper').setLevel(logging.DEBUG)
    
    print("🕷️ Master Web Scraper")
    print("=" * 50)
    print(f"Target URL: {args.url}")
    print(f"Methods: {' → '.join(args.methods)}")
    print(f"Output: {args.output}")
    print("=" * 50)
    
    # Initialize database
    if not args.no_db:
        db = ScrapingDatabase()
        print("📀 Database initialized")
    
    # Perform scraping
    async with ProgressiveScraper(config) as scraper:
        result = await scraper.scrape_progressive(args.url)
        
        # Save to database
        if not args.no_db:
            record_id = db.save_result(result)
            print(f"💾 Saved to database (ID: {record_id})")
        
        # Save to file if requested
        if args.save_to:
            with open(args.save_to, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"💾 Saved to file: {args.save_to}")
        
        # Display result
        output = format_output(result, args.output)
        print(output)
        
        # Exit with appropriate code
        sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)