#!/usr/bin/env python3
"""
Test scraper against joshsisto.com using httpx
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import httpx
import re
from urllib.parse import urljoin, urlparse


async def scrape_joshsisto():
    """Scrape joshsisto.com and extract key information"""
    
    print("🚀 Scraping joshsisto.com")
    print("=" * 50)
    
    url = "https://joshsisto.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            # Make the request
            print(f"\n📡 Fetching {url}...")
            response = await client.get(url, headers=headers)
            
            print(f"✅ Status Code: {response.status_code}")
            print(f"📏 Content Length: {len(response.text)} characters")
            
            # Extract data
            html_content = response.text
            
            # Basic extraction using regex
            results = {
                "url": url,
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat(),
                "content_length": len(html_content),
                "extracted_data": {}
            }
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                results["extracted_data"]["title"] = title_match.group(1).strip()
                print(f"📄 Title: {results['extracted_data']['title']}")
            
            # Extract meta description
            meta_desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html_content, re.IGNORECASE)
            if meta_desc:
                results["extracted_data"]["meta_description"] = meta_desc.group(1).strip()
                print(f"📝 Description: {results['extracted_data']['meta_description'][:100]}...")
            
            # Extract all headings
            headings = []
            for level in range(1, 4):
                pattern = f'<h{level}[^>]*>(.*?)</h{level}>'
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    clean_text = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_text:
                        headings.append({
                            "level": level,
                            "text": clean_text
                        })
            
            results["extracted_data"]["headings"] = headings
            print(f"📑 Found {len(headings)} headings")
            
            # Extract all links
            link_pattern = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>'
            links = re.findall(link_pattern, html_content, re.IGNORECASE)
            
            # Process and categorize links
            internal_links = []
            external_links = []
            
            for link in links:
                if link.startswith(('http://', 'https://')):
                    if 'joshsisto.com' in link:
                        internal_links.append(link)
                    else:
                        external_links.append(link)
                elif link.startswith('/'):
                    internal_links.append(urljoin(url, link))
            
            results["extracted_data"]["links"] = {
                "total": len(links),
                "internal": list(set(internal_links)),
                "external": list(set(external_links))
            }
            
            print(f"🔗 Links: {len(internal_links)} internal, {len(external_links)} external")
            
            # Extract images
            img_pattern = r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>'
            images = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            # Process image URLs
            image_urls = []
            for img in images:
                if img.startswith(('http://', 'https://')):
                    image_urls.append(img)
                elif img.startswith('/'):
                    image_urls.append(urljoin(url, img))
            
            results["extracted_data"]["images"] = {
                "total": len(images),
                "urls": list(set(image_urls))
            }
            
            print(f"🖼️  Images: {len(image_urls)} found")
            
            # Extract text content (remove HTML tags)
            text_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
            text_content = re.sub(r'<[^>]+>', ' ', text_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            results["extracted_data"]["text_preview"] = text_content[:500] + "..."
            results["extracted_data"]["word_count"] = len(text_content.split())
            
            print(f"📊 Word Count: {results['extracted_data']['word_count']} words")
            
            # Save results
            output_dir = Path("scraped_data")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / "joshsisto_scrape_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {output_file}")
            
            # Display summary
            print("\n📋 Extraction Summary:")
            print(f"   - Title: {results['extracted_data'].get('title', 'N/A')}")
            print(f"   - Headings: {len(headings)}")
            print(f"   - Links: {results['extracted_data']['links']['total']} total")
            print(f"   - Images: {results['extracted_data']['images']['total']}")
            print(f"   - Words: {results['extracted_data']['word_count']}")
            
            # Show sample of extracted headings
            if headings:
                print("\n📑 Sample Headings:")
                for h in headings[:5]:
                    print(f"   - H{h['level']}: {h['text'][:60]}...")
            
            # Show sample of links
            if internal_links:
                print("\n🔗 Sample Internal Links:")
                for link in internal_links[:5]:
                    print(f"   - {link}")
                    
            return results
            
        except Exception as e:
            print(f"\n❌ Error scraping {url}: {e}")
            return None


async def analyze_site_structure(base_url):
    """Analyze the overall site structure"""
    
    print(f"\n🔍 Analyzing Site Structure for {base_url}")
    print("=" * 50)
    
    # Common pages to check
    common_paths = [
        "/",
        "/about",
        "/contact",
        "/blog",
        "/portfolio",
        "/projects",
        "/services",
        "/sitemap.xml",
        "/robots.txt"
    ]
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        site_map = {}
        
        for path in common_paths:
            url = urljoin(base_url, path)
            try:
                response = await client.head(url)
                site_map[path] = {
                    "url": url,
                    "status": response.status_code,
                    "exists": response.status_code < 400
                }
                
                status_icon = "✅" if response.status_code < 400 else "❌"
                print(f"{status_icon} {path}: {response.status_code}")
                
            except Exception as e:
                site_map[path] = {
                    "url": url,
                    "status": "error",
                    "exists": False,
                    "error": str(e)
                }
                print(f"❌ {path}: Error")
        
        return site_map


async def main():
    """Main entry point"""
    
    print("🕷️ Awesome Web Scraper - joshsisto.com Test")
    print("=" * 50)
    
    # First, analyze site structure
    site_structure = await analyze_site_structure("https://joshsisto.com")
    
    # Then scrape the main page
    results = await scrape_joshsisto()
    
    if results:
        print("\n✅ Scraping completed successfully!")
        print(f"📂 Check the 'scraped_data' directory for detailed results")
    else:
        print("\n❌ Scraping failed!")


if __name__ == "__main__":
    asyncio.run(main())