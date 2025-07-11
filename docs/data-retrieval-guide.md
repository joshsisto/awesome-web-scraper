# 📊 Data Retrieval & Storage Guide

This comprehensive guide covers everything you need to know about retrieving, processing, and storing your scraped data.

---

## 📋 Table of Contents

1. [Understanding Scrape Results](#understanding-results)
2. [Accessing Your Data](#accessing-data)
3. [Data Storage Options](#storage-options)
4. [Data Processing & Analysis](#data-processing)
5. [Export Formats](#export-formats)
6. [Database Integration](#database-integration)
7. [Real-Time Data Pipelines](#real-time-pipelines)
8. [Data Visualization](#data-visualization)

---

<a name="understanding-results"></a>
## 🔍 Understanding Scrape Results

### The ScrapeResult Object

When you scrape a website, you get a `ScrapeResult` object with the following structure:

```python
ScrapeResult:
├── status: ScrapeStatus (SUCCESS, FAILED, TIMEOUT, ERROR)
├── url: HttpUrl (the URL that was scraped)
├── status_code: int (HTTP status code)
├── response_time: float (seconds)
├── render_time: float (for browser-based scraping)
├── method_used: ScrapeMethod (SCRAPY, PYDOLL, PLAYWRIGHT)
├── timestamp: datetime (when scraped)
├── data: Dict[str, Any] (extracted data based on selectors)
├── links: List[str] (all extracted links)
├── images: List[str] (all extracted images)
├── raw_html: str (complete HTML content)
├── text_content: str (extracted text without HTML)
├── screenshot: Optional[str] (base64 encoded screenshot)
├── cookies: Dict[str, str] (cookies from response)
├── headers: Dict[str, str] (response headers)
├── error_message: Optional[str] (error details if failed)
├── metrics: Dict[str, Any] (performance metrics)
└── proxy_used: Optional[str] (proxy IP if used)
```

### Example: Accessing Result Data

```python
# After scraping
result = await orchestrator.extract(request)

# Check if successful
if result.status == ScrapeStatus.SUCCESS:
    # Access basic info
    print(f"URL: {result.url}")
    print(f"Status Code: {result.status_code}")
    print(f"Response Time: {result.response_time}s")
    
    # Access extracted data
    title = result.data.get("title", "No title found")
    paragraphs = result.data.get("paragraphs", [])
    
    # Access links and images
    print(f"Found {len(result.links)} links")
    print(f"Found {len(result.images)} images")
    
    # Access raw content
    html_length = len(result.raw_html)
    text_length = len(result.text_content)
    
else:
    print(f"Scraping failed: {result.error_message}")
```

---

<a name="accessing-data"></a>
## 🔑 Accessing Your Data

### 1. Direct Field Access

```python
# Single value selectors
title = result.data.get("title")  # Returns string or None

# Multiple value selectors (returns list)
all_paragraphs = result.data.get("paragraphs", [])
all_headings = result.data.get("headings", [])

# Nested data
author_name = result.data.get("author", {}).get("name")

# With default values
price = result.data.get("price", "0.00")
stock_status = result.data.get("in_stock", False)
```

### 2. Structured Data Extraction

```python
def extract_product_data(result):
    """Extract and structure product information"""
    
    if result.status != ScrapeStatus.SUCCESS:
        return None
    
    # Clean and structure the data
    product = {
        "basic_info": {
            "name": result.data.get("product_name", "").strip(),
            "brand": result.data.get("brand", "").strip(),
            "sku": result.data.get("sku", "").strip(),
        },
        "pricing": {
            "current_price": parse_price(result.data.get("price")),
            "original_price": parse_price(result.data.get("original_price")),
            "discount": calculate_discount(
                result.data.get("price"),
                result.data.get("original_price")
            ),
            "currency": result.data.get("currency", "USD")
        },
        "availability": {
            "in_stock": "in stock" in result.data.get("availability", "").lower(),
            "quantity": extract_number(result.data.get("stock_count", "0")),
            "shipping": result.data.get("shipping_info", "")
        },
        "media": {
            "main_image": result.images[0] if result.images else None,
            "gallery": result.images[1:] if len(result.images) > 1 else [],
            "videos": result.data.get("product_videos", [])
        },
        "metadata": {
            "url": str(result.url),
            "scraped_at": result.timestamp.isoformat(),
            "response_time": result.response_time
        }
    }
    
    return product

def parse_price(price_str):
    """Convert price string to float"""
    if not price_str:
        return 0.0
    # Remove currency symbols and convert
    price = re.sub(r'[^\d.,]', '', str(price_str))
    price = price.replace(',', '')
    try:
        return float(price)
    except:
        return 0.0
```

### 3. Batch Data Processing

```python
async def process_multiple_results(results):
    """Process multiple scrape results"""
    
    processed_data = []
    failed_urls = []
    
    for result in results:
        if result.status == ScrapeStatus.SUCCESS:
            # Extract relevant data
            data = {
                "url": str(result.url),
                "title": result.data.get("title"),
                "content": result.data.get("content"),
                "timestamp": result.timestamp
            }
            processed_data.append(data)
        else:
            failed_urls.append({
                "url": str(result.url),
                "error": result.error_message,
                "status_code": result.status_code
            })
    
    # Summary statistics
    summary = {
        "total_urls": len(results),
        "successful": len(processed_data),
        "failed": len(failed_urls),
        "success_rate": len(processed_data) / len(results) * 100,
        "average_response_time": sum(r.response_time for r in results if r.response_time) / len(results)
    }
    
    return {
        "data": processed_data,
        "failed": failed_urls,
        "summary": summary
    }
```

---

<a name="storage-options"></a>
## 💾 Data Storage Options

### 1. JSON Storage (Simple & Portable)

```python
import json
from pathlib import Path

class JSONStorage:
    def __init__(self, base_dir="scraped_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def save_result(self, result, filename=None):
        """Save a single scrape result"""
        if filename is None:
            # Generate filename from URL and timestamp
            domain = urlparse(str(result.url)).netloc
            timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{domain}_{timestamp}.json"
        
        filepath = self.base_dir / filename
        
        data = {
            "url": str(result.url),
            "status": result.status.value,
            "timestamp": result.timestamp.isoformat(),
            "data": result.data,
            "links": result.links,
            "images": result.images,
            "metrics": result.metrics
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_result(self, filename):
        """Load a previously saved result"""
        filepath = self.base_dir / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def search_results(self, **criteria):
        """Search saved results by criteria"""
        matching_results = []
        
        for filepath in self.base_dir.glob("*.json"):
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                # Check criteria
                match = True
                for key, value in criteria.items():
                    if key in data and data[key] != value:
                        match = False
                        break
                
                if match:
                    matching_results.append(data)
        
        return matching_results
```

### 2. CSV Storage (For Tabular Data)

```python
import csv
import pandas as pd

class CSVStorage:
    def __init__(self, filename="scraped_data.csv"):
        self.filename = filename
        self.fieldnames = None
    
    def save_results(self, results, fieldnames=None):
        """Save multiple results to CSV"""
        
        # Flatten nested data
        rows = []
        for result in results:
            if result.status == ScrapeStatus.SUCCESS:
                row = self._flatten_dict(result.data)
                row['_url'] = str(result.url)
                row['_timestamp'] = result.timestamp.isoformat()
                row['_response_time'] = result.response_time
                rows.append(row)
        
        if not rows:
            return
        
        # Determine fieldnames
        if fieldnames is None:
            all_keys = set()
            for row in rows:
                all_keys.update(row.keys())
            fieldnames = sorted(list(all_keys))
        
        # Write to CSV
        with open(self.filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    def _flatten_dict(self, d, parent_key='', sep='_'):
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, ', '.join(str(i) for i in v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def load_to_dataframe(self):
        """Load CSV data into pandas DataFrame"""
        return pd.read_csv(self.filename)
```

### 3. Excel Storage (Multi-sheet Support)

```python
import pandas as pd
from datetime import datetime

class ExcelStorage:
    def __init__(self, filename="scraped_data.xlsx"):
        self.filename = filename
        self.writer = None
    
    def save_results_categorized(self, results):
        """Save results to Excel with multiple sheets"""
        
        with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
            # Main data sheet
            main_data = []
            for result in results:
                if result.status == ScrapeStatus.SUCCESS:
                    main_data.append({
                        'URL': str(result.url),
                        'Title': result.data.get('title', ''),
                        'Timestamp': result.timestamp,
                        'Response Time': result.response_time,
                        'Method': result.method_used.value if result.method_used else ''
                    })
            
            if main_data:
                df_main = pd.DataFrame(main_data)
                df_main.to_excel(writer, sheet_name='Main Data', index=False)
            
            # Links sheet
            all_links = []
            for result in results:
                for link in result.links:
                    all_links.append({
                        'Source URL': str(result.url),
                        'Link': link,
                        'Type': 'internal' if urlparse(str(result.url)).netloc in link else 'external'
                    })
            
            if all_links:
                df_links = pd.DataFrame(all_links)
                df_links.to_excel(writer, sheet_name='Links', index=False)
            
            # Images sheet
            all_images = []
            for result in results:
                for img in result.images:
                    all_images.append({
                        'Source URL': str(result.url),
                        'Image URL': img
                    })
            
            if all_images:
                df_images = pd.DataFrame(all_images)
                df_images.to_excel(writer, sheet_name='Images', index=False)
            
            # Summary sheet
            summary_data = [{
                'Total URLs': len(results),
                'Successful': len([r for r in results if r.status == ScrapeStatus.SUCCESS]),
                'Failed': len([r for r in results if r.status != ScrapeStatus.SUCCESS]),
                'Total Links': sum(len(r.links) for r in results),
                'Total Images': sum(len(r.images) for r in results),
                'Scrape Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
```

---

<a name="data-processing"></a>
## 🔄 Data Processing & Analysis

### 1. Data Cleaning Pipeline

```python
class DataCleaner:
    @staticmethod
    def clean_text(text):
        """Clean and normalize text data"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters (keep alphanumeric and basic punctuation)
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Remove multiple punctuation
        text = re.sub(r'([.,!?])\1+', r'\1', text)
        
        return text.strip()
    
    @staticmethod
    def clean_price(price_str):
        """Extract numeric price from string"""
        if not price_str:
            return None
        
        # Remove currency symbols and text
        price = re.sub(r'[^\d.,]', '', str(price_str))
        price = price.replace(',', '')
        
        try:
            return float(price)
        except ValueError:
            return None
    
    @staticmethod
    def clean_url(url, base_url=None):
        """Clean and normalize URLs"""
        if not url:
            return None
        
        # Handle relative URLs
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        # Remove fragment
        parsed = urlparse(url)
        clean_url = urlunparse(parsed._replace(fragment=''))
        
        return clean_url
    
    @staticmethod
    def extract_numbers(text):
        """Extract all numbers from text"""
        if not text:
            return []
        
        numbers = re.findall(r'\d+(?:\.\d+)?', str(text))
        return [float(n) for n in numbers]
```

### 2. Data Validation

```python
from typing import Dict, Any, List
import jsonschema

class DataValidator:
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
    
    def validate_result(self, result: ScrapeResult) -> Dict[str, Any]:
        """Validate scraped data against schema"""
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if result.status != ScrapeStatus.SUCCESS:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Scrape failed: {result.error_message}")
            return validation_result
        
        # Check required fields
        for field in self.schema.get("required", []):
            if field not in result.data or not result.data[field]:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Validate data types
        for field, expected_type in self.schema.get("properties", {}).items():
            if field in result.data:
                actual_value = result.data[field]
                
                if expected_type == "number":
                    try:
                        float(actual_value)
                    except (ValueError, TypeError):
                        validation_result["warnings"].append(
                            f"Field '{field}' should be numeric but got: {actual_value}"
                        )
                
                elif expected_type == "url":
                    if not self._is_valid_url(actual_value):
                        validation_result["warnings"].append(
                            f"Field '{field}' contains invalid URL: {actual_value}"
                        )
        
        return validation_result
    
    @staticmethod
    def _is_valid_url(url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

# Example usage
product_schema = {
    "required": ["product_name", "price"],
    "properties": {
        "product_name": "string",
        "price": "number",
        "url": "url",
        "stock_count": "number"
    }
}

validator = DataValidator(product_schema)
validation = validator.validate_result(scrape_result)
```

### 3. Data Enrichment

```python
class DataEnricher:
    def __init__(self):
        self.currency_rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.0
        }
    
    async def enrich_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich product data with additional information"""
        
        enriched = product_data.copy()
        
        # Add price conversions
        if "price" in enriched and "currency" in enriched:
            base_price = enriched["price"]
            base_currency = enriched["currency"]
            
            enriched["price_conversions"] = {}
            for currency, rate in self.currency_rates.items():
                if currency != base_currency:
                    converted_price = base_price * rate / self.currency_rates.get(base_currency, 1.0)
                    enriched["price_conversions"][currency] = round(converted_price, 2)
        
        # Add category inference
        if "title" in enriched:
            enriched["inferred_category"] = self._infer_category(enriched["title"])
        
        # Add data quality score
        enriched["data_quality_score"] = self._calculate_quality_score(enriched)
        
        # Add timestamp
        enriched["enriched_at"] = datetime.now().isoformat()
        
        return enriched
    
    def _infer_category(self, title: str) -> str:
        """Infer product category from title"""
        title_lower = title.lower()
        
        categories = {
            "electronics": ["phone", "laptop", "computer", "tablet", "camera"],
            "clothing": ["shirt", "pants", "dress", "shoes", "jacket"],
            "books": ["book", "novel", "guide", "manual"],
            "home": ["furniture", "decor", "kitchen", "bathroom"],
            "toys": ["toy", "game", "puzzle", "doll"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return "other"
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score (0-1)"""
        score = 0.0
        total_fields = 0
        
        important_fields = ["title", "price", "description", "images", "availability"]
        
        for field in important_fields:
            total_fields += 1
            if field in data and data[field]:
                score += 1
                
                # Extra points for rich data
                if field == "description" and len(str(data[field])) > 100:
                    score += 0.5
                elif field == "images" and isinstance(data[field], list) and len(data[field]) > 3:
                    score += 0.5
        
        return min(score / total_fields, 1.0)
```

---

<a name="export-formats"></a>
## 📤 Export Formats

### 1. Multiple Format Exporter

```python
class DataExporter:
    def __init__(self, results: List[ScrapeResult]):
        self.results = results
        self.successful_results = [r for r in results if r.status == ScrapeStatus.SUCCESS]
    
    def to_json(self, filename: str, pretty: bool = True):
        """Export to JSON format"""
        data = []
        for result in self.successful_results:
            data.append({
                "url": str(result.url),
                "timestamp": result.timestamp.isoformat(),
                "data": result.data,
                "links_count": len(result.links),
                "images_count": len(result.images)
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
    
    def to_csv(self, filename: str, fields: List[str] = None):
        """Export to CSV format"""
        if not self.successful_results:
            return
        
        # Determine fields if not specified
        if fields is None:
            all_fields = set()
            for result in self.successful_results:
                all_fields.update(result.data.keys())
            fields = ['url', 'timestamp'] + sorted(list(all_fields))
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for result in self.successful_results:
                row = {'url': str(result.url), 'timestamp': result.timestamp.isoformat()}
                row.update(result.data)
                writer.writerow(row)
    
    def to_xml(self, filename: str):
        """Export to XML format"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("scrape_results")
        
        for result in self.successful_results:
            result_elem = ET.SubElement(root, "result")
            
            # Add metadata
            ET.SubElement(result_elem, "url").text = str(result.url)
            ET.SubElement(result_elem, "timestamp").text = result.timestamp.isoformat()
            
            # Add data fields
            data_elem = ET.SubElement(result_elem, "data")
            for key, value in result.data.items():
                field_elem = ET.SubElement(data_elem, key)
                if isinstance(value, list):
                    for item in value:
                        ET.SubElement(field_elem, "item").text = str(item)
                else:
                    field_elem.text = str(value)
        
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
    
    def to_markdown(self, filename: str):
        """Export to Markdown format"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Scrape Results\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, result in enumerate(self.successful_results, 1):
                f.write(f"## Result {i}\n\n")
                f.write(f"- **URL**: {result.url}\n")
                f.write(f"- **Timestamp**: {result.timestamp}\n")
                f.write(f"- **Response Time**: {result.response_time:.2f}s\n\n")
                
                f.write("### Data\n\n")
                for key, value in result.data.items():
                    if isinstance(value, list):
                        f.write(f"**{key}**:\n")
                        for item in value:
                            f.write(f"  - {item}\n")
                    else:
                        f.write(f"**{key}**: {value}\n")
                f.write("\n---\n\n")
```

### 2. Custom Template Exporter

```python
from jinja2 import Template

class TemplateExporter:
    def __init__(self, template_string: str):
        self.template = Template(template_string)
    
    def export(self, results: List[ScrapeResult], output_file: str):
        """Export using custom template"""
        
        # Prepare data for template
        data = {
            "results": [
                {
                    "url": str(r.url),
                    "timestamp": r.timestamp,
                    "data": r.data,
                    "links": r.links,
                    "images": r.images,
                    "success": r.status == ScrapeStatus.SUCCESS
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "successful": len([r for r in results if r.status == ScrapeStatus.SUCCESS]),
                "failed": len([r for r in results if r.status != ScrapeStatus.SUCCESS]),
                "export_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # Render template
        output = self.template.render(**data)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)

# Example HTML template
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Scrape Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .result { border: 1px solid #ddd; padding: 10px; margin: 10px 0; }
        .success { background-color: #f0fff0; }
        .failed { background-color: #fff0f0; }
    </style>
</head>
<body>
    <h1>Scrape Results</h1>
    <p>Exported: {{ summary.export_date }}</p>
    <p>Total: {{ summary.total }} | Success: {{ summary.successful }} | Failed: {{ summary.failed }}</p>
    
    {% for result in results %}
    <div class="result {% if result.success %}success{% else %}failed{% endif %}">
        <h3>{{ result.url }}</h3>
        <p>Scraped: {{ result.timestamp }}</p>
        
        {% if result.data %}
        <h4>Data:</h4>
        <ul>
            {% for key, value in result.data.items() %}
            <li><strong>{{ key }}:</strong> {{ value }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if result.links %}
        <details>
            <summary>Links ({{ result.links|length }})</summary>
            <ul>
                {% for link in result.links[:10] %}
                <li><a href="{{ link }}">{{ link }}</a></li>
                {% endfor %}
            </ul>
        </details>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
"""

# Usage
exporter = TemplateExporter(html_template)
exporter.export(results, "results.html")
```

---

<a name="database-integration"></a>
## 🗄️ Database Integration

### 1. MongoDB Integration

```python
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any
import pymongo

class MongoDBStorage:
    def __init__(self, connection_string: str = "mongodb://localhost:27017", 
                 database: str = "web_scraper", 
                 collection: str = "scraped_data"):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[database]
        self.collection = self.db[collection]
        
        # Create indexes for better performance
        self.collection.create_index([("url", pymongo.ASCENDING)])
        self.collection.create_index([("timestamp", pymongo.DESCENDING)])
        self.collection.create_index([("domain", pymongo.ASCENDING)])
    
    async def save_result(self, result: ScrapeResult) -> str:
        """Save a scrape result to MongoDB"""
        
        document = {
            "url": str(result.url),
            "domain": urlparse(str(result.url)).netloc,
            "status": result.status.value,
            "status_code": result.status_code,
            "timestamp": result.timestamp,
            "response_time": result.response_time,
            "method_used": result.method_used.value if result.method_used else None,
            "data": result.data,
            "links": result.links,
            "images": result.images,
            "text_length": len(result.text_content) if result.text_content else 0,
            "error_message": result.error_message,
            "proxy_used": result.proxy_used
        }
        
        # Insert document
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def find_by_url(self, url: str) -> List[Dict[str, Any]]:
        """Find all results for a specific URL"""
        cursor = self.collection.find({"url": url}).sort("timestamp", -1)
        return await cursor.to_list(length=None)
    
    async def find_by_domain(self, domain: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Find all results for a specific domain"""
        cursor = self.collection.find({"domain": domain}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    async def find_recent(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Find recent scrape results"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cursor = self.collection.find({
            "timestamp": {"$gte": cutoff_time}
        }).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    async def aggregate_stats(self, domain: str = None) -> Dict[str, Any]:
        """Get aggregated statistics"""
        match_stage = {"$match": {"domain": domain}} if domain else {"$match": {}}
        
        pipeline = [
            match_stage,
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_response_time": {"$avg": "$response_time"},
                    "min_response_time": {"$min": "$response_time"},
                    "max_response_time": {"$max": "$response_time"}
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        
        stats = {
            "by_status": {r["_id"]: r for r in results},
            "total": sum(r["count"] for r in results)
        }
        
        return stats
    
    async def search_content(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for content in scraped data"""
        # Create text index if not exists
        await self.collection.create_index([("data.$**", "text")])
        
        cursor = self.collection.find({
            "$text": {"$search": search_term}
        }, {
            "score": {"$meta": "textScore"}
        }).sort([("score", {"$meta": "textScore"})]).limit(limit)
        
        return await cursor.to_list(length=None)
    
    async def cleanup_old_data(self, days: int = 30):
        """Remove data older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        result = await self.collection.delete_many({
            "timestamp": {"$lt": cutoff_time}
        })
        return result.deleted_count
```

### 2. PostgreSQL Integration

```python
import asyncpg
from typing import List, Dict, Any

class PostgreSQLStorage:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool and create tables"""
        self.pool = await asyncpg.create_pool(self.connection_string)
        
        async with self.pool.acquire() as conn:
            # Create tables
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS scrape_results (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    status TEXT NOT NULL,
                    status_code INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    response_time FLOAT,
                    method_used TEXT,
                    data JSONB,
                    links TEXT[],
                    images TEXT[],
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_url ON scrape_results(url);
                CREATE INDEX IF NOT EXISTS idx_domain ON scrape_results(domain);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON scrape_results(timestamp);
                CREATE INDEX IF NOT EXISTS idx_data ON scrape_results USING GIN(data);
            ''')
    
    async def save_result(self, result: ScrapeResult) -> int:
        """Save result to PostgreSQL"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO scrape_results 
                (url, domain, status, status_code, timestamp, response_time, 
                 method_used, data, links, images, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            ''', 
                str(result.url),
                urlparse(str(result.url)).netloc,
                result.status.value,
                result.status_code,
                result.timestamp,
                result.response_time,
                result.method_used.value if result.method_used else None,
                json.dumps(result.data),
                result.links,
                result.images,
                result.error_message
            )
            return row['id']
    
    async def find_by_json_field(self, field_path: str, value: Any) -> List[Dict[str, Any]]:
        """Find results by JSON field value"""
        async with self.pool.acquire() as conn:
            # Use JSONB operators for querying
            rows = await conn.fetch('''
                SELECT * FROM scrape_results
                WHERE data @> %s
                ORDER BY timestamp DESC
                LIMIT 100
            ''', json.dumps({field_path: value}))
            
            return [dict(row) for row in rows]
    
    async def full_text_search(self, search_term: str) -> List[Dict[str, Any]]:
        """Full text search in JSON data"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT *, 
                       ts_rank(to_tsvector('english', data::text), 
                              plainto_tsquery('english', $1)) AS rank
                FROM scrape_results
                WHERE to_tsvector('english', data::text) @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT 50
            ''', search_term)
            
            return [dict(row) for row in rows]
```

### 3. Redis Cache Integration

```python
import redis.asyncio as redis
import json
from typing import Optional, Dict, Any

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.client = None
        self.default_ttl = 3600  # 1 hour
    
    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.from_url(self.redis_url)
    
    async def cache_result(self, result: ScrapeResult, ttl: int = None):
        """Cache scrape result"""
        if ttl is None:
            ttl = self.default_ttl
        
        # Create cache key from URL
        cache_key = f"scrape:{urlparse(str(result.url)).netloc}:{result.url}"
        
        # Prepare data for caching
        cache_data = {
            "status": result.status.value,
            "timestamp": result.timestamp.isoformat(),
            "data": result.data,
            "links": result.links,
            "images": result.images,
            "response_time": result.response_time
        }
        
        # Set with expiration
        await self.client.setex(
            cache_key,
            ttl,
            json.dumps(cache_data)
        )
        
        # Also add to recent scrapes list
        await self.client.lpush("recent_scrapes", cache_key)
        await self.client.ltrim("recent_scrapes", 0, 99)  # Keep last 100
    
    async def get_cached_result(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached result for URL"""
        cache_key = f"scrape:{urlparse(url).netloc}:{url}"
        
        cached = await self.client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    async def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        cursor = 0
        while True:
            cursor, keys = await self.client.scan(cursor, match=pattern)
            if keys:
                await self.client.delete(*keys)
            if cursor == 0:
                break
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        info = await self.client.info()
        recent = await self.client.lrange("recent_scrapes", 0, 10)
        
        return {
            "used_memory": info.get("used_memory_human"),
            "total_keys": await self.client.dbsize(),
            "recent_scrapes": [k.decode() for k in recent],
            "hit_rate": info.get("keyspace_hits", 0) / 
                       (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
        }
```

---

<a name="real-time-pipelines"></a>
## 🚀 Real-Time Data Pipelines

### 1. Streaming Data Processor

```python
import asyncio
from asyncio import Queue
from typing import Callable, Any

class StreamingProcessor:
    def __init__(self, max_workers: int = 5):
        self.input_queue = Queue()
        self.output_queue = Queue()
        self.max_workers = max_workers
        self.processors = []
        self.running = False
    
    def add_processor(self, processor: Callable[[ScrapeResult], Any]):
        """Add a processing function to the pipeline"""
        self.processors.append(processor)
    
    async def process_worker(self):
        """Worker that processes items from the queue"""
        while self.running:
            try:
                result = await asyncio.wait_for(
                    self.input_queue.get(), 
                    timeout=1.0
                )
                
                # Apply all processors
                processed_data = result
                for processor in self.processors:
                    if asyncio.iscoroutinefunction(processor):
                        processed_data = await processor(processed_data)
                    else:
                        processed_data = processor(processed_data)
                
                # Put processed data in output queue
                await self.output_queue.put(processed_data)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Processing error: {e}")
    
    async def start(self):
        """Start the streaming processor"""
        self.running = True
        
        # Start worker tasks
        workers = []
        for i in range(self.max_workers):
            worker = asyncio.create_task(self.process_worker())
            workers.append(worker)
        
        return workers
    
    async def stop(self):
        """Stop the streaming processor"""
        self.running = False
    
    async def submit(self, result: ScrapeResult):
        """Submit a result for processing"""
        await self.input_queue.put(result)
    
    async def get_processed(self, timeout: float = 1.0) -> Any:
        """Get processed data from output queue"""
        try:
            return await asyncio.wait_for(
                self.output_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

# Example usage
async def example_streaming_pipeline():
    processor = StreamingProcessor(max_workers=3)
    
    # Add processing steps
    processor.add_processor(lambda r: {
        "url": str(r.url),
        "title": r.data.get("title"),
        "timestamp": r.timestamp
    })
    
    processor.add_processor(lambda d: {
        **d,
        "title_length": len(d.get("title", ""))
    })
    
    # Start processor
    workers = await processor.start()
    
    # Submit results for processing
    orchestrator = ExtractionOrchestrator()
    await orchestrator.initialize()
    
    urls = ["https://example1.com", "https://example2.com"]
    
    for url in urls:
        request = ScrapeRequest(url=url, selectors={"title": "title"})
        result = await orchestrator.extract(request)
        await processor.submit(result)
    
    # Get processed results
    processed_results = []
    while True:
        processed = await processor.get_processed()
        if processed:
            processed_results.append(processed)
        else:
            break
    
    # Cleanup
    await processor.stop()
    await orchestrator.close()
    
    return processed_results
```

### 2. WebSocket Real-Time Updates

```python
import websockets
import json

class WebSocketDataStreamer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients = set()
    
    async def handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
    
    async def broadcast_result(self, result: ScrapeResult):
        """Broadcast scrape result to all connected clients"""
        
        message = {
            "type": "scrape_result",
            "url": str(result.url),
            "status": result.status.value,
            "timestamp": result.timestamp.isoformat(),
            "data": result.data,
            "metrics": {
                "response_time": result.response_time,
                "links_found": len(result.links),
                "images_found": len(result.images)
            }
        }
        
        # Send to all connected clients
        if self.clients:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.clients],
                return_exceptions=True
            )
    
    async def start_server(self):
        """Start WebSocket server"""
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # Run forever

# Client example
async def websocket_client():
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] == "scrape_result":
                print(f"New result: {data['url']} - {data['status']}")
                print(f"Data: {data['data']}")
```

---

<a name="data-visualization"></a>
## 📈 Data Visualization

### 1. Dashboard Generator

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class ScrapeDashboard:
    def __init__(self, results: List[ScrapeResult]):
        self.results = results
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame"""
        data = []
        for result in self.results:
            data.append({
                'url': str(result.url),
                'domain': urlparse(str(result.url)).netloc,
                'status': result.status.value,
                'status_code': result.status_code,
                'response_time': result.response_time,
                'timestamp': result.timestamp,
                'links_count': len(result.links),
                'images_count': len(result.images),
                'method': result.method_used.value if result.method_used else 'unknown'
            })
        return pd.DataFrame(data)
    
    def create_dashboard(self, output_file: str = "dashboard.html"):
        """Create interactive dashboard"""
        
        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Success Rate by Domain', 'Response Times', 
                          'Scraping Methods Used', 'Timeline'),
            specs=[[{'type': 'domain'}, {'type': 'box'}],
                   [{'type': 'bar'}, {'type': 'scatter'}]]
        )
        
        # 1. Success rate pie chart
        status_counts = self.df['status'].value_counts()
        fig.add_trace(
            go.Pie(labels=status_counts.index, values=status_counts.values),
            row=1, col=1
        )
        
        # 2. Response time box plot by domain
        domains = self.df['domain'].unique()[:10]  # Top 10 domains
        for domain in domains:
            domain_data = self.df[self.df['domain'] == domain]
            fig.add_trace(
                go.Box(y=domain_data['response_time'], name=domain),
                row=1, col=2
            )
        
        # 3. Methods bar chart
        method_counts = self.df['method'].value_counts()
        fig.add_trace(
            go.Bar(x=method_counts.index, y=method_counts.values),
            row=2, col=1
        )
        
        # 4. Timeline scatter
        fig.add_trace(
            go.Scatter(
                x=self.df['timestamp'],
                y=self.df['response_time'],
                mode='markers',
                marker=dict(
                    color=self.df['status_code'],
                    colorscale='Viridis',
                    showscale=True
                )
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title="Web Scraping Dashboard",
            showlegend=False,
            height=800
        )
        
        # Save to HTML
        fig.write_html(output_file)
        
        return fig
    
    def generate_report(self, output_file: str = "report.md"):
        """Generate markdown report"""
        
        total = len(self.df)
        successful = len(self.df[self.df['status'] == 'success'])
        
        report = f"""# Web Scraping Report

## Summary
- **Total URLs Scraped**: {total}
- **Successful**: {successful} ({successful/total*100:.1f}%)
- **Failed**: {total - successful} ({(total-successful)/total*100:.1f}%)
- **Average Response Time**: {self.df['response_time'].mean():.2f}s
- **Date Range**: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}

## Top Domains
"""
        
        # Add top domains
        top_domains = self.df.groupby('domain').agg({
            'url': 'count',
            'response_time': 'mean',
            'status': lambda x: (x == 'success').sum() / len(x) * 100
        }).round(2).sort_values('url', ascending=False).head(10)
        
        report += top_domains.to_markdown()
        
        with open(output_file, 'w') as f:
            f.write(report)
```

---

## 🎯 Quick Reference

### Essential Commands

```python
# Initialize orchestrator
orchestrator = ExtractionOrchestrator()
await orchestrator.initialize()

# Create request
request = ScrapeRequest(
    url="https://example.com",
    selectors={"title": "title", "content": ".content"},
    extract_links=True
)

# Execute scrape
result = await orchestrator.extract(request)

# Check success
if result.status == ScrapeStatus.SUCCESS:
    # Access data
    data = result.data
    links = result.links
    
    # Save to JSON
    with open("data.json", "w") as f:
        json.dump({"data": data, "links": links}, f)

# Cleanup
await orchestrator.close()
```

### Common Patterns

```python
# Batch processing
results = await orchestrator.batch_extract(requests)

# With proxy
request.use_proxy = True

# With stealth
request.use_stealth = True

# Wait for element
request.wait_conditions = ["selector:.dynamic-content"]

# Custom headers
request.headers = {"Authorization": "Bearer token"}
```

**Happy Data Retrieval! 📊**