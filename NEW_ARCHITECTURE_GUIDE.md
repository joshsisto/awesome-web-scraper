# 🚀 New Architecture Guide

Welcome to the redesigned **Awesome Web Scraper**! The scraper has been completely restructured with a command-line interface and API service architecture.

---

## 🎯 **New Architecture Overview**

### **1. Master Scraper (`master_scraper.py`)**
- Command-line interface for scraping websites
- Progressive scraping strategy: **Scrapy → PyDoll → Playwright**
- Automatic database storage
- Comprehensive logging

### **2. Data Retriever (`data_retriever.py`)**
- Query and analyze scraped data from database
- Export to multiple formats (JSON, CSV)
- Search and filter capabilities
- Statistics and analytics

### **3. API Service (`api_service.py`)**
- RESTful API for remote scraping
- Background task processing
- Rate limiting and authentication ready
- OpenAPI documentation

---

## 🛠️ **Installation**

### Install Dependencies
```bash
pip install -r requirements-api.txt
```

### Initialize Database
The database is automatically created when you run your first scrape.

---

## 📋 **Usage Examples**

### **Master Scraper**

#### Basic Scraping
```bash
# Scrape a website (auto-detects best method)
python master_scraper.py joshsisto.com

# Scrape with HTTPS
python master_scraper.py https://example.com

# Specific output format
python master_scraper.py example.com --output json

# Save to file
python master_scraper.py example.com --save-to results.json

# Verbose logging
python master_scraper.py example.com --verbose
```

#### Advanced Options
```bash
# Try only specific methods
python master_scraper.py example.com --methods scrapy pydoll

# Disable SSL verification (for testing)
python master_scraper.py example.com --verify-ssl

# Custom timeout
python master_scraper.py example.com --timeout 60

# Skip database storage
python master_scraper.py example.com --no-db
```

### **Data Retriever**

#### Query Data
```bash
# List all scraped URLs
python data_retriever.py --list

# Get data for specific URL
python data_retriever.py --url joshsisto.com

# Get all data for a domain
python data_retriever.py --domain example.com

# Get recent data (last 24 hours)
python data_retriever.py --recent 24

# Search for content
python data_retriever.py --search "contact"

# Show database statistics
python data_retriever.py --stats
```

#### Export Data
```bash
# Export all data to CSV
python data_retriever.py --list --export csv

# Export specific domain to JSON
python data_retriever.py --domain example.com --export json --output domain_data.json

# Export search results
python data_retriever.py --search "news" --export csv --limit 100
```

#### Data Management
```bash
# Clean up old data (older than 30 days)
python data_retriever.py --cleanup 30

# Custom database file
python data_retriever.py --db custom.db --stats
```

### **API Service**

#### Start the API Server
```bash
# Start on default port (8000)
python api_service.py

# Start on custom port
python api_service.py --port 8080

# Bind to all interfaces
python api_service.py --host 0.0.0.0 --port 8000

# Development mode with auto-reload
python api_service.py --reload --log-level debug
```

#### API Usage Examples
```bash
# Scrape a URL via API
curl -X POST "http://localhost:8000/scrape" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'

# Get task status
curl "http://localhost:8000/tasks/task_1234567890"

# List all results
curl "http://localhost:8000/results"

# Get specific result
curl "http://localhost:8000/results/1"

# Search content
curl "http://localhost:8000/search?q=contact&limit=10"

# Get statistics
curl "http://localhost:8000/stats"

# Health check
curl "http://localhost:8000/health"
```

---

## 🔄 **Progressive Scraping Strategy**

The scraper automatically tries methods in this order:

### **1. 🕷️ Scrapy Method (First Try)**
- **Best for:** Static HTML content, news sites, blogs
- **Speed:** ⚡ Fastest
- **Features:** Basic HTML parsing, link extraction
- **Use case:** Standard websites without JavaScript

### **2. ⚡ PyDoll Method (Fallback)**
- **Best for:** APIs, JSON endpoints, enhanced parsing
- **Speed:** 🚀 Fast
- **Features:** JSON parsing, meta tag extraction, headers analysis
- **Use case:** API endpoints, sites with structured data

### **3. 🎭 Playwright Method (Final Fallback)**
- **Best for:** JavaScript-heavy sites, SPAs, dynamic content
- **Speed:** 🐌 Slower but thorough
- **Features:** Full browser automation, screenshot capture, dynamic content
- **Use case:** React/Vue/Angular apps, complex interactions

---

## 📊 **Database Schema**

The scraper stores data in SQLite with this schema:

```sql
CREATE TABLE scrape_results (
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
    data_json TEXT,          -- Extracted data as JSON
    links_json TEXT,         -- All links as JSON array
    images_json TEXT,        -- All images as JSON array
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎨 **Output Formats**

### **Summary Format (Default)**
```
✅ Scraping Result for https://example.com
────────────────────────────────────────────────────────────
🕷️ Method Used: SCRAPY
📊 Status: SUCCESS
🌐 HTTP Status: 200
⏱️  Response Time: 0.85s
📄 Title: Example Domain
📏 Content Length: 1,256 characters
🔗 Links Found: 5
🖼️  Images Found: 2
🕒 Timestamp: 2025-07-11T15:57:42.699163
```

### **JSON Format**
```json
{
  "url": "https://example.com",
  "status": "success",
  "method_used": "scrapy",
  "status_code": 200,
  "response_time": 0.85,
  "title": "Example Domain",
  "data": {
    "title": "Example Domain",
    "headings": ["Welcome", "About", "Contact"],
    "meta_description": "Example site description"
  },
  "links": ["https://example.com/about", "https://example.com/contact"],
  "images": ["https://example.com/logo.png"]
}
```

### **Table Format**
```
╔══════════════════════════════════════════════════════════════╗
║                      SCRAPING RESULT                        ║
╠══════════════════════════════════════════════════════════════╣
║ URL: https://example.com                                     ║
║ Status: success                                              ║
║ Method: scrapy                                               ║
║ Response Time: 0.85s                                         ║
║ Title: Example Domain                                        ║
║ Links Found: 5                                               ║
║ Images Found: 2                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database configuration
SCRAPER_DB_PATH=custom_scraper.db

# API configuration
SCRAPER_API_HOST=0.0.0.0
SCRAPER_API_PORT=8000

# Scraping configuration
SCRAPER_DEFAULT_TIMEOUT=30
SCRAPER_VERIFY_SSL=false
SCRAPER_MAX_RETRIES=3
```

### **Config File (config.json)**
```json
{
  "verify_ssl": false,
  "timeout": 30,
  "max_retries": 3,
  "delay_between_methods": 1,
  "user_agents": [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  ]
}
```

Use config file:
```bash
python master_scraper.py example.com --config config.json
```

---

## 🚀 **API Documentation**

When you start the API service, visit:
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### **Main Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scrape` | Start scraping a URL |
| `GET` | `/tasks/{task_id}` | Get task status |
| `GET` | `/results` | List all results |
| `GET` | `/results/{id}` | Get specific result |
| `GET` | `/results/url/{url}` | Get results for URL |
| `GET` | `/results/domain/{domain}` | Get results for domain |
| `GET` | `/search?q={query}` | Search results |
| `GET` | `/stats` | Get statistics |
| `DELETE` | `/results/{id}` | Delete result |
| `GET` | `/health` | Health check |

---

## 🎯 **Real-World Examples**

### **Monitoring a Website**
```bash
# Scrape and monitor a site every hour
while true; do
    python master_scraper.py mysite.com
    echo "Scraped at $(date)"
    sleep 3600
done
```

### **Batch Processing**
```bash
# Scrape multiple sites
for site in site1.com site2.com site3.com; do
    python master_scraper.py $site --output json --save-to "${site}_data.json"
done

# Check results
python data_retriever.py --recent 1 --export csv
```

### **Research Data Collection**
```bash
# Collect data from multiple domains
python master_scraper.py news-site.com
python master_scraper.py research-portal.org
python master_scraper.py data-source.net

# Analyze collected data
python data_retriever.py --stats
python data_retriever.py --search "research" --export json
```

### **API Integration**
```python
import requests

# Start API service
# python api_service.py &

# Scrape via API
response = requests.post('http://localhost:8000/scrape', 
                        json={'url': 'https://example.com'})
task_id = response.json()['task_id']

# Check status
status = requests.get(f'http://localhost:8000/tasks/{task_id}')
print(status.json())

# Get results
results = requests.get('http://localhost:8000/results')
print(results.json())
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Database Locked Error**
```bash
# Stop any running processes
pkill -f master_scraper
pkill -f api_service

# Check database
python data_retriever.py --stats
```

#### **2. SSL Certificate Errors**
```bash
# Disable SSL verification
python master_scraper.py example.com --verify-ssl=false
```

#### **3. Timeout Issues**
```bash
# Increase timeout
python master_scraper.py slow-site.com --timeout 60
```

#### **4. Method Failures**
```bash
# Try specific methods only
python master_scraper.py problematic-site.com --methods playwright
```

### **Debug Mode**
```bash
# Enable verbose logging
python master_scraper.py example.com --verbose

# Check logs
tail -f scraper.log
```

---

## 🎉 **Migration from Old Architecture**

If you were using the previous framework-based architecture:

### **Old Way:**
```python
from services.extraction.extraction_orchestrator import ExtractionOrchestrator
orchestrator = ExtractionOrchestrator()
result = await orchestrator.extract(request)
```

### **New Way:**
```bash
# Command line
python master_scraper.py example.com

# Or via API
curl -X POST "http://localhost:8000/scrape" -d '{"url": "example.com"}'
```

The new architecture is:
- ✅ **Simpler** - Command-line driven
- ✅ **Faster** - Direct progressive strategy
- ✅ **More Robust** - Better error handling
- ✅ **Production Ready** - Database storage and API
- ✅ **Scalable** - Can run as a service

---

## 🔮 **Next Steps**

Your scraper is now ready for production use! Consider:

1. **Set up monitoring** with the API health endpoint
2. **Create dashboards** using the statistics endpoint
3. **Implement authentication** for the API service
4. **Scale horizontally** by running multiple API instances
5. **Add custom scrapers** for specific site types

**Happy Scraping! 🚀**