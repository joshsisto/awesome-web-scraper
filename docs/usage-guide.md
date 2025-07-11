# 📚 Complete Usage Guide

This guide will walk you through everything you need to know about using the Awesome Web Scraper, from basic scraping to advanced data retrieval.

---

## 🎯 Table of Contents

1. [Quick Start - Your First Scrape](#quick-start)
2. [How to Scrape Any Website](#scraping-websites)
3. [Retrieving Your Scraped Data](#retrieving-data)
4. [Advanced Usage](#advanced-usage)
5. [Real-World Examples](#real-examples)
6. [Troubleshooting](#troubleshooting)

---

<a name="quick-start"></a>
## 🚀 Quick Start - Your First Scrape

### Step 1: Create Your Scraping Script

Create a new Python file `my_scraper.py`:

```python
import asyncio
import json
from services.extraction.extraction_orchestrator import ExtractionOrchestrator
from common.models.scrape_request import ScrapeRequest, ScrapeMethod

async def scrape_website():
    # Initialize the orchestrator
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    # Create a scraping request
    request = ScrapeRequest(
        url="https://example.com",
        selectors={
            "title": "title",
            "headings": "h1, h2",
            "paragraphs": "p",
            "links": "a[href]"
        },
        extract_links=True,
        extract_images=True
    )
    
    # Execute the scrape
    result = await orchestrator.extract(request)
    
    # Save results
    if result.status.value == "success":
        with open("scraped_data.json", "w") as f:
            json.dump({
                "url": str(result.url),
                "data": result.data,
                "links": result.links,
                "images": result.images
            }, f, indent=2)
        print("✅ Scraping successful! Data saved to scraped_data.json")
    else:
        print(f"❌ Scraping failed: {result.error_message}")
    
    await orchestrator.close()

# Run the scraper
asyncio.run(scrape_website())
```

### Step 2: Run Your Scraper

```bash
python my_scraper.py
```

---

<a name="scraping-websites"></a>
## 🕷️ How to Scrape Any Website

### 1. Basic HTML Scraping

For static websites with simple HTML:

```python
async def scrape_static_site(url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=url,
        method=ScrapeMethod.SCRAPY,  # Best for static HTML
        selectors={
            # CSS Selectors
            "title": "title",
            "article_title": "article h1",
            "article_content": "article .content",
            "author": ".author-name",
            "date": "time[datetime]",
            
            # Multiple elements
            "all_paragraphs": "p",  # Returns list
            "all_links": "a[href]",
            
            # Attribute extraction
            "image_sources": "img[src]",
            "link_urls": "a[href]"
        },
        extract_links=True,
        extract_images=True,
        extract_text=True
    )
    
    result = await orchestrator.extract(request)
    await orchestrator.close()
    
    return result
```

### 2. JavaScript-Heavy Sites

For single-page applications or dynamic content:

```python
async def scrape_dynamic_site(url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=url,
        method=ScrapeMethod.PLAYWRIGHT,  # Full browser automation
        selectors={
            "dynamic_content": "[data-react-component]",
            "lazy_loaded_images": "img[data-src]",
            "ajax_content": ".ajax-loaded"
        },
        wait_conditions=[
            "networkidle",  # Wait for network to be idle
            "domcontentloaded",  # Wait for DOM
            "selector:.dynamic-content",  # Wait for specific element
            "delay:2"  # Additional 2-second delay
        ],
        capture_screenshot=True,
        use_stealth=True,  # Anti-detection
        human_like_delays=True
    )
    
    result = await orchestrator.extract(request)
    await orchestrator.close()
    
    return result
```

### 3. API and JSON Data

For REST APIs or JSON endpoints:

```python
async def scrape_api(api_url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=api_url,
        method=ScrapeMethod.PYDOLL,  # Optimized for APIs
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer YOUR_TOKEN"  # If needed
        },
        extract_text=True  # Get raw response
    )
    
    result = await orchestrator.extract(request)
    
    # Parse JSON from response
    if result.status.value == "success":
        json_data = json.loads(result.raw_html)
        result.data["parsed_json"] = json_data
    
    await orchestrator.close()
    
    return result
```

### 4. E-commerce Product Scraping

```python
async def scrape_product(product_url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=product_url,
        selectors={
            # Product information
            "product_name": "h1.product-title",
            "price": ".price-now",
            "original_price": ".price-was",
            "description": ".product-description",
            "specifications": ".specs-list li",
            "availability": ".stock-status",
            "rating": ".rating-value",
            "review_count": ".review-count",
            
            # Images
            "main_image": ".product-photo img[src]",
            "gallery_images": ".thumbnail-list img[src]",
            
            # Variations
            "sizes": ".size-selector option",
            "colors": ".color-selector button[data-color]"
        },
        use_proxy=True,  # Avoid rate limiting
        use_stealth=True  # Avoid detection
    )
    
    result = await orchestrator.extract(request)
    await orchestrator.close()
    
    return result
```

### 5. Pagination and Multiple Pages

```python
async def scrape_with_pagination(base_url, max_pages=10):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    all_results = []
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        
        request = ScrapeRequest(
            url=url,
            selectors={
                "items": ".item-listing",
                "next_page": "a.next-page[href]"
            }
        )
        
        result = await orchestrator.extract(request)
        
        if result.status.value == "success":
            all_results.extend(result.data.get("items", []))
            
            # Check if there's a next page
            if not result.data.get("next_page"):
                break
        else:
            break
            
        # Be nice to the server
        await asyncio.sleep(1)
    
    await orchestrator.close()
    
    return all_results
```

---

<a name="retrieving-data"></a>
## 📊 Retrieving Your Scraped Data

### 1. Basic Data Retrieval

```python
# After scraping
result = await orchestrator.extract(request)

# Access scraped data
if result.status.value == "success":
    # Basic data access
    title = result.data.get("title")
    headings = result.data.get("headings", [])
    
    # All extracted links
    all_links = result.links
    
    # All extracted images
    all_images = result.images
    
    # Raw HTML (if needed)
    raw_html = result.raw_html
    
    # Metadata
    status_code = result.status_code
    response_time = result.response_time
    method_used = result.method_used
```

### 2. Saving Data to Different Formats

#### JSON Format
```python
def save_as_json(result, filename="data.json"):
    data = {
        "url": str(result.url),
        "timestamp": result.timestamp.isoformat(),
        "status": result.status.value,
        "data": result.data,
        "links": result.links,
        "images": result.images,
        "metrics": result.metrics
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

#### CSV Format
```python
import csv

def save_as_csv(results, filename="data.csv"):
    # For list of products/items
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if results and isinstance(results[0].data, dict):
            keys = results[0].data.keys()
            writer = csv.DictWriter(f, fieldnames=keys)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result.data)
```

#### Excel Format
```python
import pandas as pd

def save_as_excel(results, filename="data.xlsx"):
    # Convert to DataFrame
    data = [r.data for r in results if r.status.value == "success"]
    df = pd.DataFrame(data)
    
    # Save to Excel with multiple sheets if needed
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name='Scraped Data', index=False)
        
        # Add metadata sheet
        metadata = pd.DataFrame([{
            'Total Records': len(data),
            'Scrape Date': datetime.now().isoformat(),
            'Success Rate': f"{len(data)/len(results)*100:.2f}%"
        }])
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
```

### 3. Database Storage

#### MongoDB Storage
```python
from motor.motor_asyncio import AsyncIOMotorClient

async def save_to_mongodb(result):
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.scraped_data
    collection = db.websites
    
    document = {
        "url": str(result.url),
        "timestamp": result.timestamp,
        "data": result.data,
        "links": result.links,
        "images": result.images,
        "status": result.status.value
    }
    
    await collection.insert_one(document)
    print(f"Saved to MongoDB with ID: {document['_id']}")
```

#### SQLite Storage
```python
import sqlite3
import json

def save_to_sqlite(result, db_name="scraped_data.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            timestamp TEXT,
            status TEXT,
            data TEXT,
            links TEXT,
            images TEXT
        )
    ''')
    
    # Insert data
    cursor.execute('''
        INSERT INTO scraped_pages (url, timestamp, status, data, links, images)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        str(result.url),
        result.timestamp.isoformat(),
        result.status.value,
        json.dumps(result.data),
        json.dumps(result.links),
        json.dumps(result.images)
    ))
    
    conn.commit()
    conn.close()
```

### 4. Real-time Data Processing

```python
async def scrape_and_process():
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    # Define processing pipeline
    async def process_result(result):
        if result.status.value == "success":
            # Extract specific fields
            processed = {
                "title": result.data.get("title", "").strip(),
                "price": float(result.data.get("price", "0").replace("$", "")),
                "in_stock": "in stock" in result.data.get("availability", "").lower(),
                "images": len(result.images),
                "scraped_at": result.timestamp
            }
            
            # Real-time notification
            if processed["in_stock"] and processed["price"] < 100:
                print(f"🎯 Deal Alert: {processed['title']} - ${processed['price']}")
            
            return processed
    
    # Scrape multiple URLs
    urls = ["https://example.com/product1", "https://example.com/product2"]
    
    processed_results = []
    for url in urls:
        request = ScrapeRequest(url=url, selectors={...})
        result = await orchestrator.extract(request)
        processed = await process_result(result)
        processed_results.append(processed)
    
    await orchestrator.close()
    return processed_results
```

---

<a name="advanced-usage"></a>
## 🔧 Advanced Usage

### 1. Batch Processing with Concurrency

```python
async def batch_scrape(urls, max_concurrent=5):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    # Create semaphore for concurrency control
    sem = asyncio.Semaphore(max_concurrent)
    
    async def scrape_with_limit(url):
        async with sem:
            request = ScrapeRequest(
                url=url,
                selectors={"title": "title", "content": "body"},
                timeout=30
            )
            return await orchestrator.extract(request)
    
    # Scrape all URLs concurrently
    tasks = [scrape_with_limit(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    await orchestrator.close()
    
    # Filter successful results
    successful = [r for r in results if r.status.value == "success"]
    print(f"Successfully scraped {len(successful)}/{len(urls)} pages")
    
    return results
```

### 2. Custom Headers and Authentication

```python
async def scrape_with_auth(url, auth_token):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=url,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "User-Agent": "MyBot/1.0",
            "Accept": "text/html,application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache"
        },
        cookies={
            "session_id": "abc123",
            "preferences": "dark_mode=true"
        },
        auth_credentials={
            "username": "user",
            "password": "pass"
        }  # For basic auth
    )
    
    result = await orchestrator.extract(request)
    await orchestrator.close()
    
    return result
```

### 3. Proxy and VPN Rotation

```python
async def scrape_with_proxy_rotation(urls):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    results = []
    
    for i, url in enumerate(urls):
        request = ScrapeRequest(
            url=url,
            use_proxy=True,
            proxy_config={
                "type": "rotating",  # or "sticky"
                "country": "US",  # Specific country
                "protocol": "http"  # or "socks5"
            },
            use_stealth=True,
            # Force new IP every 5 requests
            force_new_proxy=(i % 5 == 0)
        )
        
        result = await orchestrator.extract(request)
        results.append(result)
        
        # Check proxy used
        if result.proxy_used:
            print(f"Used proxy: {result.proxy_used}")
    
    await orchestrator.close()
    return results
```

### 4. Handling Captchas and Anti-Bot

```python
async def scrape_with_antibot_bypass(url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=url,
        method=ScrapeMethod.PLAYWRIGHT,
        use_stealth=True,
        human_like_delays=True,
        browser_config={
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone": "America/New_York",
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "permissions": ["geolocation"]
        },
        # Simulate human behavior
        interactions=[
            {"action": "wait", "time": 2},
            {"action": "move_mouse", "x": 100, "y": 200},
            {"action": "scroll", "direction": "down", "amount": 300},
            {"action": "wait", "time": 1},
            {"action": "click", "selector": ".accept-cookies"}
        ]
    )
    
    result = await orchestrator.extract(request)
    await orchestrator.close()
    
    return result
```

### 5. Data Monitoring and Alerts

```python
import smtplib
from email.mime.text import MIMEText

async def monitor_website_changes(url, check_interval=3600):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    previous_data = None
    
    while True:
        request = ScrapeRequest(
            url=url,
            selectors={
                "price": ".price",
                "stock": ".stock-status",
                "title": "h1"
            }
        )
        
        result = await orchestrator.extract(request)
        
        if result.status.value == "success":
            current_data = result.data
            
            # Check for changes
            if previous_data and current_data != previous_data:
                changes = []
                for key in current_data:
                    if current_data.get(key) != previous_data.get(key):
                        changes.append(f"{key}: {previous_data.get(key)} → {current_data.get(key)}")
                
                # Send alert
                if changes:
                    alert_message = f"Website changes detected:\n" + "\n".join(changes)
                    print(f"🚨 {alert_message}")
                    # send_email_alert(alert_message)
            
            previous_data = current_data
        
        # Wait before next check
        await asyncio.sleep(check_interval)
```

---

<a name="real-examples"></a>
## 🌟 Real-World Examples

### Example 1: News Article Scraper

```python
async def scrape_news_article(article_url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=article_url,
        selectors={
            "headline": "h1.article-title",
            "author": ".author-name",
            "publish_date": "time[datetime]",
            "content": "div.article-content p",
            "tags": ".article-tags a",
            "related_articles": ".related-articles a[href]"
        },
        extract_text=True,
        extract_links=True
    )
    
    result = await orchestrator.extract(request)
    
    if result.status.value == "success":
        # Process and structure the data
        article = {
            "url": article_url,
            "headline": result.data.get("headline", ""),
            "author": result.data.get("author", ""),
            "date": result.data.get("publish_date", ""),
            "content": " ".join(result.data.get("content", [])),
            "tags": result.data.get("tags", []),
            "word_count": len(" ".join(result.data.get("content", [])).split()),
            "related": result.data.get("related_articles", [])
        }
        
        # Save to file
        with open(f"article_{article['headline'][:30]}.json", "w") as f:
            json.dump(article, f, indent=2)
    
    await orchestrator.close()
    return article
```

### Example 2: Real Estate Listings

```python
async def scrape_property_listings(search_url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    all_listings = []
    page = 1
    
    while True:
        request = ScrapeRequest(
            url=f"{search_url}&page={page}",
            selectors={
                "listings": ".property-card",
                "price": ".property-price",
                "address": ".property-address",
                "bedrooms": ".property-beds",
                "bathrooms": ".property-baths",
                "sqft": ".property-sqft",
                "image": ".property-image img[src]",
                "link": "a.property-link[href]",
                "next_page": "a.pagination-next[href]"
            },
            use_proxy=True
        )
        
        result = await orchestrator.extract(request)
        
        if result.status.value == "success":
            # Process each listing
            listings = result.data.get("listings", [])
            
            for i, listing in enumerate(listings):
                property_data = {
                    "price": result.data.get("price", [])[i] if i < len(result.data.get("price", [])) else None,
                    "address": result.data.get("address", [])[i] if i < len(result.data.get("address", [])) else None,
                    "bedrooms": result.data.get("bedrooms", [])[i] if i < len(result.data.get("bedrooms", [])) else None,
                    "bathrooms": result.data.get("bathrooms", [])[i] if i < len(result.data.get("bathrooms", [])) else None,
                    "sqft": result.data.get("sqft", [])[i] if i < len(result.data.get("sqft", [])) else None,
                    "image": result.data.get("image", [])[i] if i < len(result.data.get("image", [])) else None,
                    "url": result.data.get("link", [])[i] if i < len(result.data.get("link", [])) else None
                }
                all_listings.append(property_data)
            
            # Check for next page
            if not result.data.get("next_page"):
                break
            
            page += 1
            await asyncio.sleep(2)  # Be respectful
        else:
            break
    
    await orchestrator.close()
    
    # Save all listings
    df = pd.DataFrame(all_listings)
    df.to_csv("property_listings.csv", index=False)
    
    return all_listings
```

### Example 3: Social Media Profile

```python
async def scrape_social_profile(profile_url):
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    request = ScrapeRequest(
        url=profile_url,
        method=ScrapeMethod.PLAYWRIGHT,  # Needed for dynamic content
        selectors={
            "username": ".profile-username",
            "bio": ".profile-bio",
            "followers": ".followers-count",
            "following": ".following-count",
            "posts": ".post-count",
            "recent_posts": ".post-item",
            "verified": ".verified-badge"
        },
        wait_conditions=["networkidle", "selector:.profile-loaded"],
        use_stealth=True,
        capture_screenshot=True
    )
    
    result = await orchestrator.extract(request)
    
    if result.status.value == "success":
        profile = {
            "url": profile_url,
            "username": result.data.get("username"),
            "bio": result.data.get("bio"),
            "followers": result.data.get("followers"),
            "following": result.data.get("following"),
            "posts": result.data.get("posts"),
            "is_verified": bool(result.data.get("verified")),
            "recent_posts": result.data.get("recent_posts", [])[:10],
            "screenshot": result.screenshot  # Base64 encoded
        }
        
        # Save profile data
        with open(f"profile_{profile['username']}.json", "w") as f:
            json.dump(profile, f, indent=2)
    
    await orchestrator.close()
    return profile
```

---

<a name="troubleshooting"></a>
## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. SSL Certificate Errors
```python
# For development/testing only
request = ScrapeRequest(
    url=url,
    verify_ssl=False  # Disable SSL verification
)
```

#### 2. Timeout Issues
```python
request = ScrapeRequest(
    url=url,
    timeout=60,  # Increase timeout to 60 seconds
    wait_conditions=["networkidle"],
    max_wait_time=30  # Maximum wait for conditions
)
```

#### 3. Rate Limiting
```python
# Add delays between requests
for url in urls:
    result = await orchestrator.extract(request)
    await asyncio.sleep(random.uniform(1, 3))  # Random delay
```

#### 4. Dynamic Content Not Loading
```python
request = ScrapeRequest(
    url=url,
    method=ScrapeMethod.PLAYWRIGHT,
    wait_conditions=[
        "domcontentloaded",
        "networkidle",
        "selector:.dynamic-content",  # Wait for specific element
        "function:() => window.jQuery !== undefined"  # Wait for jQuery
    ]
)
```

#### 5. Blocked by Anti-Bot
```python
request = ScrapeRequest(
    url=url,
    use_stealth=True,
    use_proxy=True,
    headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    browser_config={
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox"
        ]
    }
)
```

---

## 📚 Additional Resources

- [API Reference](api-reference.md) - Complete API documentation
- [Configuration Guide](configuration.md) - Advanced configuration options
- [VPN Setup](vpn.md) - Configure IP rotation
- [Performance Tuning](performance.md) - Optimize for speed and scale

---

## 💡 Best Practices

1. **Always respect robots.txt** - Check if scraping is allowed
2. **Add delays between requests** - Don't overwhelm servers
3. **Use appropriate User-Agent** - Identify your bot
4. **Handle errors gracefully** - Implement retry logic
5. **Store data efficiently** - Use appropriate formats
6. **Monitor your scraping** - Track success rates
7. **Update selectors regularly** - Websites change

**Happy Scraping! 🚀**