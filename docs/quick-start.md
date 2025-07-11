# Quick Start Tutorial

This tutorial will guide you through your first web scraping job using the Awesome Web Scraper. You'll learn the basics of creating requests, extracting data, and using different frameworks.

## 🎯 What You'll Learn

- How to create and execute scraping requests
- Understanding automatic framework selection
- Data extraction with selectors
- Basic proxy and stealth usage
- Monitoring scraping results

---

## 🚀 Your First Scraping Job

### 1. Basic Setup

Create a new Python file for your scraping experiments:

```python
# my_first_scraper.py
import asyncio
import json
from datetime import datetime

# Import the core components
from services.extraction.extraction_orchestrator import ExtractionOrchestrator
from common.models.scrape_request import ScrapeRequest, ScrapeMethod, Priority
from common.models.scrape_result import ScrapeStatus

async def main():
    # Initialize the orchestrator
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    print("🚀 Awesome Web Scraper is ready!")
    
    # Your scraping code will go here
    
    # Clean up
    await orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Simple Web Page Scraping

Let's scrape a simple webpage:

```python
async def scrape_simple_page():
    """Scrape a simple webpage with basic data extraction"""
    
    # Create a scraping request
    request = ScrapeRequest(
        url="https://httpbin.org/html",
        method=ScrapeMethod.SCRAPY,  # Explicit method selection
        selectors={
            "title": "title",
            "heading": "h1", 
            "paragraphs": "p"
        },
        extract_links=True,
        use_proxy=False,  # Disable for first test
        use_stealth=False,  # Disable for first test
        timeout=30
    )
    
    # Execute the scraping
    result = await orchestrator.extract(request)
    
    # Check results
    if result.status == ScrapeStatus.SUCCESS:
        print("✅ Scraping successful!")
        print(f"Status Code: {result.status_code}")
        print(f"Response Time: {result.response_time:.2f}s")
        print(f"Data Extracted: {json.dumps(result.data, indent=2)}")
        print(f"Links Found: {len(result.links)}")
    else:
        print("❌ Scraping failed!")
        print(f"Error: {result.error_message}")
    
    return result
```

### 3. JSON API Scraping

Now let's scrape a JSON API using the PyDoll method:

```python
async def scrape_api_data():
    """Scrape JSON API data using PyDoll method"""
    
    request = ScrapeRequest(
        url="https://httpbin.org/json",
        method=ScrapeMethod.PYDOLL,  # Best for APIs
        extract_text=True,
        use_proxy=False,
        timeout=15
    )
    
    result = await orchestrator.extract(request)
    
    if result.status == ScrapeStatus.SUCCESS:
        print("✅ API scraping successful!")
        print(f"Response Time: {result.response_time:.2f}s")
        
        # For JSON APIs, data is usually in raw_html
        try:
            json_data = json.loads(result.raw_html)
            print(f"JSON Data: {json.dumps(json_data, indent=2)}")
        except json.JSONDecodeError:
            print("Data is not valid JSON")
    
    return result
```

### 4. Complex Browser Automation

For JavaScript-heavy sites, use Playwright:

```python
async def scrape_with_browser():
    """Scrape using browser automation for complex sites"""
    
    request = ScrapeRequest(
        url="https://httpbin.org/delay/2",  # Simulates slow-loading content
        method=ScrapeMethod.PLAYWRIGHT,
        selectors={
            "response_data": "pre"  # HTTPBin shows JSON in <pre> tags
        },
        wait_conditions=[
            "networkidle",  # Wait for network to be idle
            "delay:3"       # Additional 3-second delay
        ],
        use_stealth=True,
        human_like_delays=True,
        timeout=30
    )
    
    result = await orchestrator.extract(request)
    
    if result.status == ScrapeStatus.SUCCESS:
        print("✅ Browser automation successful!")
        print(f"Response Time: {result.response_time:.2f}s")
        print(f"Render Time: {result.render_time:.2f}s")
        print(f"Data: {json.dumps(result.data, indent=2)}")
    
    return result
```

---

## 🤖 Automatic Framework Selection

The orchestrator can automatically choose the best method:

```python
async def auto_framework_selection():
    """Let the orchestrator choose the best framework"""
    
    # Don't specify method - let orchestrator decide
    request = ScrapeRequest(
        url="https://httpbin.org/html",
        selectors={
            "title": "title",
            "content": "body"
        },
        # The orchestrator will analyze these characteristics:
        extract_links=True,      # Suggests Scrapy for link extraction
        use_proxy=True,          # Enables proxy rotation
        use_stealth=True,        # Enables anti-detection
        priority=Priority.HIGH   # Might prefer faster methods
    )
    
    # Get suggestion
    suggested_method = orchestrator.suggest_method(request)
    print(f"🤖 Suggested method: {suggested_method}")
    
    # Execute with automatic selection
    result = await orchestrator.extract(request)
    
    return result
```

---

## 🔄 Batch Processing

Process multiple URLs efficiently:

```python
async def batch_scraping():
    """Scrape multiple URLs in batch"""
    
    urls_to_scrape = [
        "https://httpbin.org/html",
        "https://httpbin.org/json", 
        "https://httpbin.org/xml"
    ]
    
    # Create multiple requests
    requests = []
    for url in urls_to_scrape:
        request = ScrapeRequest(
            url=url,
            selectors={"content": "body"},
            use_proxy=True,
            timeout=30
        )
        requests.append(request)
    
    # Process in batch
    results = await orchestrator.batch_extract(requests)
    
    # Analyze results
    successful = len([r for r in results if r.status == ScrapeStatus.SUCCESS])
    print(f"✅ Batch completed: {successful}/{len(results)} successful")
    
    for i, result in enumerate(results):
        url = urls_to_scrape[i]
        status = "✅" if result.status == ScrapeStatus.SUCCESS else "❌"
        print(f"{status} {url}: {result.status}")
    
    return results
```

---

## 🛡️ Using Stealth and Proxies

Enable anti-detection features:

```python
async def stealth_scraping():
    """Scrape with full stealth and proxy features"""
    
    request = ScrapeRequest(
        url="https://httpbin.org/user-agent",
        method=ScrapeMethod.PLAYWRIGHT,  # Best for stealth
        selectors={
            "user_agent": "pre"
        },
        # Anti-detection features
        use_stealth=True,
        human_like_delays=True,
        use_proxy=True,
        
        # Custom headers
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
        },
        
        timeout=30
    )
    
    result = await orchestrator.extract(request)
    
    if result.status == ScrapeStatus.SUCCESS:
        print("🛡️ Stealth scraping completed!")
        print(f"User Agent Detected: {result.data}")
        print(f"Proxy Used: {result.proxy_used}")
    
    return result
```

---

## 📊 Complete Example

Here's a complete script combining all concepts:

```python
# complete_example.py
import asyncio
import json
from datetime import datetime

from services.extraction.extraction_orchestrator import ExtractionOrchestrator
from common.models.scrape_request import ScrapeRequest, ScrapeMethod, Priority
from common.models.scrape_result import ScrapeStatus

async def complete_scraping_example():
    """Complete example showing different scraping scenarios"""
    
    # Initialize
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    print("🚀 Starting Complete Scraping Example")
    print("=" * 50)
    
    # 1. Simple HTML Scraping
    print("1. 🕷️ Simple HTML Scraping (Scrapy)")
    html_request = ScrapeRequest(
        url="https://httpbin.org/html",
        method=ScrapeMethod.SCRAPY,
        selectors={
            "title": "title",
            "heading": "h1"
        }
    )
    html_result = await orchestrator.extract(html_request)
    print(f"   Status: {html_result.status}")
    print(f"   Data: {html_result.data}")
    print()
    
    # 2. API Data Extraction
    print("2. ⚡ API Data Extraction (PyDoll)")
    api_request = ScrapeRequest(
        url="https://httpbin.org/json",
        method=ScrapeMethod.PYDOLL
    )
    api_result = await orchestrator.extract(api_request)
    print(f"   Status: {api_result.status}")
    print(f"   Response Time: {api_result.response_time:.3f}s")
    print()
    
    # 3. Browser Automation
    print("3. 🎭 Browser Automation (Playwright)")
    browser_request = ScrapeRequest(
        url="https://httpbin.org/delay/1",
        method=ScrapeMethod.PLAYWRIGHT,
        use_stealth=True,
        wait_conditions=["networkidle"]
    )
    browser_result = await orchestrator.extract(browser_request)
    print(f"   Status: {browser_result.status}")
    print(f"   Render Time: {browser_result.render_time:.3f}s")
    print()
    
    # 4. Automatic Method Selection
    print("4. 🤖 Automatic Method Selection")
    auto_request = ScrapeRequest(
        url="https://httpbin.org/headers",
        selectors={"headers": "pre"},
        use_proxy=True,
        use_stealth=True
    )
    suggested = orchestrator.suggest_method(auto_request)
    print(f"   Suggested Method: {suggested}")
    auto_result = await orchestrator.extract(auto_request)
    print(f"   Status: {auto_result.status}")
    print()
    
    # 5. Performance Summary
    print("📊 Performance Summary")
    all_results = [html_result, api_result, browser_result, auto_result]
    successful = len([r for r in all_results if r.status == ScrapeStatus.SUCCESS])
    total_time = sum([r.response_time for r in all_results if r.response_time])
    
    print(f"   Total Requests: {len(all_results)}")
    print(f"   Successful: {successful}")
    print(f"   Success Rate: {successful/len(all_results):.2%}")
    print(f"   Total Time: {total_time:.3f}s")
    print(f"   Average Time: {total_time/len(all_results):.3f}s")
    
    # Cleanup
    await orchestrator.close()
    print("\n✅ Example completed successfully!")

if __name__ == "__main__":
    asyncio.run(complete_scraping_example())
```

---

## 🎯 Running Your Scripts

### 1. Save and Execute
```bash
# Save any of the above examples as a .py file
python my_first_scraper.py
```

### 2. Expected Output
```
🚀 Awesome Web Scraper is ready!
✅ Scraping successful!
Status Code: 200
Response Time: 0.85s
Data Extracted: {
  "title": "Herman Melville - Moby-Dick",
  "heading": "Herman Melville - Moby-Dick"
}
Links Found: 0
```

### 3. Troubleshooting
If you encounter errors:
- Ensure services are running: `docker-compose ps`
- Check network connectivity: `curl -I https://httpbin.org/get`
- Verify dependencies: `pip list | grep -E "(httpx|pydantic)"`

---

## 🎓 What's Next?

Now that you've completed your first scraping jobs:

1. **[Configuration Guide](configuration.md)** - Customize settings for your needs
2. **[VPN Setup](vpn.md)** - Enable IP rotation with Private Internet Access
3. **[Frameworks Guide](frameworks.md)** - Deep dive into when to use each method
4. **[Anti-Detection](anti-detection.md)** - Advanced stealth techniques
5. **[API Reference](api-reference.md)** - Complete feature documentation

---

## 💡 Pro Tips

- **Start simple** - Begin with basic requests before adding stealth features
- **Use automatic selection** - Let the orchestrator choose the best method
- **Monitor performance** - Check response times and success rates
- **Test incrementally** - Add one feature at a time when troubleshooting
- **Check logs** - Use structured logging to understand what's happening

**Ready for more advanced features?** Continue to the [Configuration Guide](configuration.md)!