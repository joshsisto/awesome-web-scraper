# Awesome Web Scraper Documentation

Welcome to the comprehensive documentation for the Awesome Web Scraper - a production-ready, multi-framework web scraping solution with VPN integration and intelligent orchestration.

## 📚 Documentation Index

### Quick Start
- [Installation Guide](installation.md) - Get up and running in minutes
- [Quick Start Tutorial](quick-start.md) - Your first scraping job
- [Configuration Guide](configuration.md) - Environment setup and customization

### Core Concepts
- [Architecture Overview](architecture.md) - Understanding the system design
- [Multi-Framework Selection](frameworks.md) - When to use Scrapy, PyDoll, or Playwright
- [Data Models](models.md) - Request and response structures

### Features
- [VPN Integration](vpn.md) - Private Internet Access setup and usage
- [Proxy Management](proxy.md) - Rotation strategies and health monitoring
- [Anti-Detection](anti-detection.md) - Stealth techniques and evasion
- [Error Handling](error-handling.md) - Retries, circuit breakers, and fault tolerance

### Advanced Usage
- [API Reference](api-reference.md) - Complete API documentation
- [Custom Extensions](extensions.md) - Building custom scrapers
- [Performance Tuning](performance.md) - Optimization techniques
- [Monitoring & Alerting](monitoring.md) - Observability and metrics

### Deployment
- [Docker Deployment](docker.md) - Containerized deployment
- [Kubernetes](kubernetes.md) - Scalable cluster deployment
- [Production Checklist](production.md) - Pre-deployment validation

### Development
- [Contributing](contributing.md) - Development workflow and guidelines
- [Testing](testing.md) - Running and writing tests
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

---

## 🎯 What This Scraper Does

The Awesome Web Scraper is an intelligent, production-ready web scraping platform that automatically selects the best scraping method for each target:

- **🕷️ Scrapy** for fast, large-scale crawling of static content
- **⚡ PyDoll** for optimized API and structured data extraction  
- **🎭 Playwright** for JavaScript-heavy sites and complex interactions

### Key Features

✅ **Multi-Framework Intelligence** - Automatic method selection  
✅ **VPN Integration** - Private Internet Access support with server rotation  
✅ **Advanced Anti-Detection** - Stealth mode, UA rotation, human-like behavior  
✅ **Robust Error Handling** - Circuit breakers, retries, graceful degradation  
✅ **Comprehensive Monitoring** - Prometheus metrics, Grafana dashboards  
✅ **Production Ready** - Docker/Kubernetes deployment, horizontal scaling  

---

## 🚀 Quick Start Example

```python
from services.extraction.extraction_orchestrator import ExtractionOrchestrator
from common.models.scrape_request import ScrapeRequest

# Initialize the orchestrator
orchestrator = ExtractionOrchestrator()
await orchestrator.initialize()

# Create a scraping request
request = ScrapeRequest(
    url="https://example.com",
    selectors={
        "title": "h1",
        "content": ".main-content",
        "price": ".price"
    },
    extract_links=True,
    use_proxy=True,
    use_stealth=True
)

# The orchestrator automatically selects the best method
result = await orchestrator.extract(request)

print(f"Status: {result.status}")
print(f"Data: {result.data}")
print(f"Links found: {len(result.links)}")
```

---

## 📖 Next Steps

1. **Start with [Installation Guide](installation.md)** to set up your environment
2. **Follow the [Quick Start Tutorial](quick-start.md)** for your first scraping job
3. **Configure [VPN Integration](vpn.md)** for IP rotation
4. **Explore [Advanced Features](frameworks.md)** for complex scenarios

---

**Need help?** Check our [Troubleshooting Guide](troubleshooting.md) or [API Reference](api-reference.md).