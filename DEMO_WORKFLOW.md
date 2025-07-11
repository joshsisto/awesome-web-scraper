# 🎬 Demo Workflow - Complete Scraper Usage

This demo shows the complete workflow of the new command-line architecture.

---

## 🚀 **Quick Demo**

### **1. Basic Scraping**
```bash
# Scrape a website (your site + httpbin for demo)
$ python master_scraper.py joshsisto.com
🕷️ Master Web Scraper
==================================================
Target URL: joshsisto.com
Methods: scrapy → pydoll → playwright
Output: summary
==================================================
📀 Database initialized
💾 Saved to database (ID: 1)

✅ Scraping Result for https://joshsisto.com
────────────────────────────────────────────────────────────
🕷️ Method Used: SCRAPY
📊 Status: SUCCESS
🌐 HTTP Status: 200
⏱️  Response Time: 0.06s
📄 Title: Error | OPNsense
📏 Content Length: 1,603 characters
🔗 Links Found: 2
🖼️  Images Found: 0
🕒 Timestamp: 2025-07-11T15:57:42.699163
```

### **2. Scrape Another Site**
```bash
$ python master_scraper.py httpbin.org --output json
{
  "url": "https://httpbin.org",
  "domain": "httpbin.org", 
  "method_used": "scrapy",
  "status": "success",
  "status_code": 200,
  "response_time": 0.36,
  "title": "httpbin.org",
  "data": {
    "title": "httpbin.org",
    "headings": ["httpbin.org", "Other Utilities"]
  },
  "links": [
    "https://github.com/requests/httpbin",
    "https://github.com/rochacbruno/flasgger",
    "https://kennethreitz.org",
    "https://httpbin.org/forms/post"
  ]
}
```

### **3. View All Results**
```bash
$ python data_retriever.py --list
📊 Data Retriever
========================================
📋 Scraped URLs
================================================================================
ID    Status   Method     URL                                      Title               
--------------------------------------------------------------------------------
2     ✅        scrapy     https://httpbin.org                      httpbin.org         
1     ✅        scrapy     https://joshsisto.com                    Error | OPNsense    
```

### **4. Get Detailed Results**
```bash
$ python data_retriever.py --url httpbin.org
🔍 Detailed Result for https://httpbin.org
================================================================================
✅ Status: SUCCESS
🕷️ Method: SCRAPY
🌐 HTTP Status: 200
⏱️  Response Time: 0.359s
🕒 Timestamp: 2025-07-11T16:02:12.655712
📄 Title: httpbin.org
📏 Content Length: 9,591 characters
🔗 Links Found: 4
🖼️  Images Found: 0

📊 Extracted Data:
----------------------------------------
  title: httpbin.org
  headings: 2 items
    - httpbin.org
    - Other Utilities

🔗 Sample Links (showing first 4 of 4):
----------------------------------------
  - https://github.com/requests/httpbin
  - https://github.com/rochacbruno/flasgger  
  - https://kennethreitz.org
  - https://httpbin.org/forms/post
```

### **5. Database Statistics**
```bash
$ python data_retriever.py --stats
📊 Database Statistics
============================================================
📈 Total Results: 2
✅ Successful: 2
❌ Failed: 0
📊 Success Rate: 100.0%

🔧 Method Performance:
------------------------------
  🕷️ Scrapy: 2 uses, 0.212s avg

⏱️  Response Times:
--------------------
  Average: 0.212s
  Fastest: 0.064s
  Slowest: 0.359s

🌐 Top Domains:
--------------------
  httpbin.org: 1 results
  joshsisto.com: 1 results

📅 Recent Activity:
--------------------
  2025-07-11: 2 scrapes
```

### **6. Search Content**
```bash
$ python data_retriever.py --search "httpbin"
🔍 Search Results for 'httpbin'
============================================================
Found 1 matching results

1. ✅ https://httpbin.org
   📊 Relevance: 16 | Method: scrapy | 2025-07-11T16:02:12.655712
   📄 httpbin.org
```

### **7. Export Data**
```bash
$ python data_retriever.py --list --export csv --output demo_export.csv
💾 Exported 2 records to demo_export.csv

$ python data_retriever.py --domain httpbin.org --export json
💾 Exported 1 records to httpbin_export.json
```

---

## 🌐 **API Service Demo**

### **Start API Server**
```bash
$ python api_service.py --port 8080
🚀 Starting Awesome Web Scraper API Service
==================================================
Host: 127.0.0.1
Port: 8080
Docs: http://127.0.0.1:8080/docs
==================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080
```

### **API Usage Examples**
```bash
# Health check
$ curl http://localhost:8080/health
{
  "status": "healthy",
  "timestamp": "2025-07-11T16:05:30.123456",
  "database": "healthy",
  "active_tasks": 0,
  "completed_tasks": 0
}

# Start scraping task
$ curl -X POST "http://localhost:8080/scrape" \
       -H "Content-Type: application/json" \
       -d '{"url": "https://example.com"}'
{
  "task_id": "task_1720728000123",
  "status": "started", 
  "message": "Scraping task started for https://example.com",
  "estimated_completion": "2025-07-11T16:06:00.123456"
}

# Check task status
$ curl http://localhost:8080/tasks/task_1720728000123
{
  "task_id": "task_1720728000123",
  "url": "https://example.com",
  "status": "completed",
  "created_at": "2025-07-11T16:05:30.123456",
  "completed_at": "2025-07-11T16:05:32.987654",
  "result_id": 3
}

# Get all results via API
$ curl http://localhost:8080/results
{
  "results": [
    {
      "id": 3,
      "url": "https://example.com",
      "status": "success",
      "method_used": "scrapy",
      "title": "Example Domain"
    }
  ],
  "count": 1,
  "limit": 50,
  "offset": 0
}

# Get statistics via API
$ curl http://localhost:8080/stats
{
  "total_results": 3,
  "successful_results": 3,
  "failed_results": 0,
  "success_rate": 100.0,
  "method_statistics": {
    "scrapy": {
      "count": 3,
      "avg_response_time": 0.245
    }
  }
}
```

---

## 🎯 **Real-World Scenarios**

### **Scenario 1: Monitor Multiple Sites**
```bash
# Create monitoring script
for site in joshsisto.com httpbin.org example.com; do
    echo "Monitoring $site..."
    python master_scraper.py $site --timeout 30
done

# Check results
python data_retriever.py --recent 1 --export csv --output monitoring_report.csv
```

### **Scenario 2: Progressive Scraping**
```bash
# Try a complex site that requires different methods
python master_scraper.py spa-website.com --verbose

# This will show progression:
# 🕷️ Scrapy method: spa-website.com
# ❌ Scrapy method failed: Limited content
# ⚡ PyDoll method: spa-website.com  
# ❌ PyDoll method failed: Dynamic content
# 🎭 Playwright method: spa-website.com
# ✅ Success with playwright method
```

### **Scenario 3: Data Analysis**
```bash
# Scrape multiple related sites
python master_scraper.py news-site-1.com
python master_scraper.py news-site-2.com
python master_scraper.py news-site-3.com

# Analyze the data
python data_retriever.py --search "news" --limit 20
python data_retriever.py --stats
python data_retriever.py --recent 24 --export json --output news_analysis.json
```

### **Scenario 4: API Integration**
```python
#!/usr/bin/env python3
# api_integration_demo.py

import requests
import time
import json

API_BASE = "http://localhost:8080"

def scrape_and_wait(url):
    """Scrape URL and wait for completion"""
    
    # Start scraping
    response = requests.post(f"{API_BASE}/scrape", 
                           json={"url": url})
    task_id = response.json()["task_id"]
    print(f"Started task: {task_id}")
    
    # Wait for completion
    while True:
        status = requests.get(f"{API_BASE}/tasks/{task_id}")
        task_data = status.json()
        
        if task_data["status"] == "completed":
            result_id = task_data["result_id"]
            break
        elif task_data["status"] == "failed":
            print(f"Task failed: {task_data.get('error')}")
            return None
            
        time.sleep(1)
    
    # Get result
    result = requests.get(f"{API_BASE}/results/{result_id}")
    return result.json()

# Usage
if __name__ == "__main__":
    sites = ["https://httpbin.org", "https://example.com"]
    
    for site in sites:
        print(f"\nScraping {site}...")
        result = scrape_and_wait(site)
        if result:
            print(f"✅ Success: {result['title']}")
            print(f"📊 Links: {result['links_count']}")
```

---

## 📊 **Performance Comparison**

### **Method Performance**
```bash
# Test different methods on the same site
python master_scraper.py httpbin.org --methods scrapy --save-to scrapy_test.json
python master_scraper.py httpbin.org --methods pydoll --save-to pydoll_test.json  
python master_scraper.py httpbin.org --methods playwright --save-to playwright_test.json

# Compare results
python data_retriever.py --domain httpbin.org --format table
```

**Expected Results:**
- **Scrapy:** ~0.3s (fastest, basic extraction)
- **PyDoll:** ~0.5s (medium speed, enhanced parsing)
- **Playwright:** ~2.0s (slower, comprehensive extraction)

---

## 🔧 **Advanced Usage**

### **Custom Configuration**
```json
// config.json
{
  "verify_ssl": false,
  "timeout": 60,
  "max_retries": 5,
  "delay_between_methods": 2,
  "user_agents": [
    "Custom-Scraper/1.0",
    "Research-Bot/2.0"
  ]
}
```

```bash
python master_scraper.py difficult-site.com --config config.json
```

### **Batch Processing**
```bash
# Create URL list
echo "site1.com" > urls.txt
echo "site2.com" >> urls.txt
echo "site3.com" >> urls.txt

# Process batch
while read url; do
    python master_scraper.py "$url" --output json --save-to "${url//[^a-zA-Z0-9]/_}.json"
done < urls.txt

# Consolidate results
python data_retriever.py --recent 1 --export csv --output batch_results.csv
```

---

## 🎉 **Success Metrics**

After running this demo, you'll have:

✅ **Scraped multiple websites** with automatic method selection  
✅ **Stored data in database** with full history  
✅ **Retrieved and analyzed** data with multiple query options  
✅ **Exported data** in multiple formats  
✅ **API service running** for remote access  
✅ **Real-time statistics** and monitoring  
✅ **Production-ready system** for scaling  

**Your scraper is now ready for any web scraping challenge! 🚀**