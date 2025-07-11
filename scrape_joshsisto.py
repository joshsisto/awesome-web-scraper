#!/usr/bin/env python3
"""
Scrape joshsisto.com - A practical example of using the Awesome Web Scraper
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Import our scraper components
from services.extraction.extraction_orchestrator import ExtractionOrchestrator
from common.models.scrape_request import ScrapeRequest, ScrapeMethod, Priority
from common.models.scrape_result import ScrapeStatus


async def scrape_joshsisto_site():
    """Scrape joshsisto.com and extract key information"""
    
    # Initialize the orchestrator
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    print("🚀 Starting scrape of joshsisto.com")
    print("=" * 50)
    
    # 1. First, let's do a basic scrape to understand the site structure
    print("\n📋 Phase 1: Basic Site Analysis")
    basic_request = ScrapeRequest(
        url="https://joshsisto.com",
        method=ScrapeMethod.SCRAPY,  # Start with Scrapy for static content
        selectors={
            "title": "title",
            "headings": "h1, h2, h3",
            "navigation": "nav a",
            "main_content": "main, article, .content",
            "footer": "footer"
        },
        extract_links=True,
        extract_images=True,
        use_proxy=False,  # Start without proxy
        use_stealth=False,
        timeout=30
    )
    
    basic_result = await orchestrator.extract(basic_request)
    
    if basic_result.status == ScrapeStatus.SUCCESS:
        print("✅ Basic scrape successful!")
        print(f"   Status Code: {basic_result.status_code}")
        print(f"   Response Time: {basic_result.response_time:.2f}s")
        print(f"   Links Found: {len(basic_result.links)}")
        print(f"   Images Found: {len(basic_result.images)}")
        
        # Save basic results
        save_results(basic_result, "joshsisto_basic_scrape.json")
    else:
        print("❌ Basic scrape failed!")
        print(f"   Error: {basic_result.error_message}")
    
    # 2. Now let's use PyDoll for faster API-style extraction
    print("\n⚡ Phase 2: Fast Content Extraction (PyDoll)")
    pydoll_request = ScrapeRequest(
        url="https://joshsisto.com",
        method=ScrapeMethod.PYDOLL,
        selectors={
            "page_title": "title",
            "meta_description": "meta[name='description']",
            "meta_keywords": "meta[name='keywords']",
            "all_text": "body",
            "scripts": "script[src]",
            "stylesheets": "link[rel='stylesheet']"
        },
        extract_metadata=True,
        use_proxy=False,
        timeout=15
    )
    
    pydoll_result = await orchestrator.extract(pydoll_request)
    
    if pydoll_result.status == ScrapeStatus.SUCCESS:
        print("✅ PyDoll extraction successful!")
        print(f"   Response Time: {pydoll_result.response_time:.2f}s")
        save_results(pydoll_result, "joshsisto_pydoll_extract.json")
    
    # 3. Use Playwright for JavaScript-rendered content
    print("\n🎭 Phase 3: Browser Automation (Playwright)")
    playwright_request = ScrapeRequest(
        url="https://joshsisto.com",
        method=ScrapeMethod.PLAYWRIGHT,
        selectors={
            "dynamic_content": "[data-dynamic], [data-react], [data-vue]",
            "interactive_elements": "button, a[onclick], [data-action]",
            "forms": "form",
            "media": "video, audio, iframe"
        },
        wait_conditions=["networkidle", "domcontentloaded"],
        use_stealth=True,
        human_like_delays=True,
        capture_screenshot=True,
        timeout=30
    )
    
    playwright_result = await orchestrator.extract(playwright_request)
    
    if playwright_result.status == ScrapeStatus.SUCCESS:
        print("✅ Playwright automation successful!")
        print(f"   Render Time: {playwright_result.render_time:.2f}s")
        if playwright_result.screenshot:
            print("   Screenshot captured!")
        save_results(playwright_result, "joshsisto_playwright_render.json")
    
    # 4. Extract specific data points
    print("\n🎯 Phase 4: Targeted Data Extraction")
    
    # Combine all results
    all_data = {
        "scrape_timestamp": datetime.now().isoformat(),
        "site_url": "https://joshsisto.com",
        "extraction_summary": {
            "title": basic_result.data.get("title") if basic_result.status == ScrapeStatus.SUCCESS else None,
            "total_links": len(basic_result.links) if basic_result.status == ScrapeStatus.SUCCESS else 0,
            "total_images": len(basic_result.images) if basic_result.status == ScrapeStatus.SUCCESS else 0,
            "has_dynamic_content": bool(playwright_result.data.get("dynamic_content")) if playwright_result.status == ScrapeStatus.SUCCESS else False,
        },
        "performance_metrics": {
            "scrapy_time": basic_result.response_time if basic_result.status == ScrapeStatus.SUCCESS else None,
            "pydoll_time": pydoll_result.response_time if pydoll_result.status == ScrapeStatus.SUCCESS else None,
            "playwright_time": playwright_result.response_time if playwright_result.status == ScrapeStatus.SUCCESS else None,
        }
    }
    
    # Save combined analysis
    save_json(all_data, "joshsisto_complete_analysis.json")
    
    print("\n📊 Scraping Complete!")
    print("=" * 50)
    print(f"✅ Results saved to:")
    print("   - joshsisto_basic_scrape.json")
    print("   - joshsisto_pydoll_extract.json")
    print("   - joshsisto_playwright_render.json")
    print("   - joshsisto_complete_analysis.json")
    
    # Cleanup
    await orchestrator.close()
    
    return all_data


def save_results(result, filename):
    """Save scraping results to a JSON file"""
    data = {
        "status": result.status.value,
        "url": str(result.url),
        "status_code": result.status_code,
        "response_time": result.response_time,
        "render_time": result.render_time,
        "method_used": result.method_used.value if result.method_used else None,
        "timestamp": result.timestamp.isoformat() if result.timestamp else None,
        "data": result.data,
        "links": result.links,
        "images": result.images,
        "error_message": result.error_message,
        "metrics": result.metrics
    }
    save_json(data, filename)


def save_json(data, filename):
    """Save data to JSON file"""
    output_dir = Path("scraped_data")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"   💾 Saved: {output_path}")


async def main():
    """Main entry point"""
    try:
        results = await scrape_joshsisto_site()
        
        # Display summary
        print("\n🎉 Scraping Summary:")
        print(json.dumps(results["extraction_summary"], indent=2))
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())