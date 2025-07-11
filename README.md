# Awesome Web Scraper

A production-ready web scraper with VPN integration, multiple scraping frameworks, and microservices architecture.

## Features

### Multi-Framework Support
- **Scrapy**: Fast, scalable scraping for sites without JavaScript or anti-bot protection
- **PyDoll-style**: Fast HTTP requests with selectolax parsing for middleground scenarios
- **Playwright**: Full browser automation for JavaScript-heavy sites and complex interactions

### VPN Integration
- **Private Internet Access (PIA)** integration for IP rotation
- Automatic server selection based on load and latency
- Health monitoring and automatic failover
- Support for multiple geographic locations

### Advanced Proxy Management
- Intelligent proxy rotation strategies (round-robin, health-based, geographic)
- Circuit breaker pattern for fault tolerance
- Sticky sessions for complex workflows
- Real-time health monitoring and blacklist management

### Anti-Detection Measures
- Stealth browser configurations
- User agent rotation
- Human-like behavior simulation
- Rate limiting and exponential backoff
- Canvas and WebGL fingerprinting evasion

### Microservices Architecture
- **Orchestration Service**: Task scheduling and coordination
- **Extraction Service**: Data collection with multiple methods
- **Processing Service**: Data transformation and validation
- **Storage Service**: Persistent data management
- **Proxy Management Service**: IP rotation and VPN management

### Monitoring & Observability
- Prometheus metrics collection
- Grafana dashboards
- Structured logging with context
- Circuit breaker monitoring
- Performance metrics tracking

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Private Internet Access account (optional)
- MongoDB (via Docker)
- Redis (via Docker)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scraper
```

2. Install dependencies:
```bash
pip install -e .[dev]
```

3. Install Playwright browsers:
```bash
playwright install
```

4. Start infrastructure services:
```bash
docker-compose up -d mongodb redis prometheus grafana
```

5. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Basic Usage

```python
from common.models.scrape_request import ScrapeRequest, ScrapeMethod
from services.extraction.extraction_orchestrator import ExtractionOrchestrator

# Initialize orchestrator
orchestrator = ExtractionOrchestrator()
await orchestrator.initialize()

# Create scrape request
request = ScrapeRequest(
    url="https://example.com",
    method=ScrapeMethod.SCRAPY,
    selectors={
        "title": "h1",
        "content": ".main-content"
    },
    extract_links=True,
    use_proxy=True,
    use_stealth=True
)

# Perform scraping
result = await orchestrator.extract(request)

print(f"Status: {result.status}")
print(f"Data: {result.data}")
print(f"Links found: {len(result.links)}")
```

## Configuration

### Environment Variables

```bash
# MongoDB
MONGODB_URL=mongodb://scraper:scraper_pass@localhost:27017

# Redis
REDIS_URL=redis://localhost:6379

# PIA VPN
PIA_USERNAME=your_username
PIA_PASSWORD=your_password

# Proxy Settings
DEFAULT_PROXY_POOL=default
PROXY_ROTATION_STRATEGY=health_based

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Proxy Pool Configuration

```python
from services.proxy_management.proxy_rotator import ProxyRotator, ProxyPool, RotationStrategy
from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider

# Create proxy pool
pool = ProxyPool(
    name="datacenter_pool",
    proxies=[
        ProxyConfig(
            host="proxy1.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER,
            country="US"
        ),
        # Add more proxies...
    ],
    strategy=RotationStrategy.HEALTH_BASED
)

# Add to rotator
rotator = ProxyRotator()
await rotator.initialize()
await rotator.add_proxy_pool(pool)
```

## Testing

### Run All Tests
```bash
python scripts/run_tests.py --type all --coverage
```

### Run Unit Tests Only
```bash
python scripts/run_tests.py --type unit --verbose
```

### Run Integration Tests
```bash
python scripts/run_tests.py --type integration
```

### Run with Coverage
```bash
python scripts/run_tests.py --coverage
```

Test coverage reports are generated in `htmlcov/index.html`.

## Architecture

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Orchestration  │    │   Extraction    │    │   Processing    │
│    Service      │◄──►│    Service      │◄──►│    Service      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Proxy Mgmt     │    │    Storage      │    │   Monitoring    │
│   Service       │    │    Service      │    │    Service      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Extraction Methods Decision Tree
```
Request Analysis
       │
       ▼
JavaScript Required? ──── YES ──── Playwright
       │
       NO
       │
       ▼
Authentication Required? ── YES ── Playwright
       │
       NO
       │
       ▼
High Volume/Speed? ──── YES ──── Scrapy
       │
       NO
       │
       ▼
     PyDoll
```

## Deployment

### Docker Deployment

1. Build services:
```bash
docker-compose build
```

2. Deploy stack:
```bash
docker-compose up -d
```

3. Scale services:
```bash
docker-compose up -d --scale extraction=3 --scale processing=2
```

### Kubernetes Deployment

1. Apply configurations:
```bash
kubectl apply -f k8s/
```

2. Scale deployments:
```bash
kubectl scale deployment extraction-service --replicas=3
```

### Production Considerations

- Use external MongoDB cluster for production
- Configure proper secrets management
- Set up log aggregation (ELK stack)
- Configure alerting rules
- Use load balancers for high availability
- Set up backup and disaster recovery

## Monitoring

### Metrics Available

- **Request Metrics**: Success rate, response time, error rate
- **Proxy Metrics**: Health score, rotation frequency, geographic distribution
- **Service Metrics**: Circuit breaker state, throughput, resource usage
- **VPN Metrics**: Connection status, server load, rotation events

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (admin/admin)

Pre-configured dashboards:
- Scraping Overview
- Proxy Management
- Service Health
- VPN Status

### Alerts

Configure alerts for:
- High error rates (>5%)
- Proxy health degradation
- VPN connection failures
- Circuit breaker trips
- Resource exhaustion

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions
- Write comprehensive tests
- Use structured logging

### Testing Requirements

- Minimum 80% code coverage
- All tests must pass
- Include unit, integration, and E2E tests
- Mock external dependencies

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation
- Review existing issues

## Roadmap

- [ ] Add more VPN providers (NordVPN, ExpressVPN)
- [ ] Implement AI-powered anti-detection
- [ ] Add GraphQL scraping support
- [ ] Implement distributed crawling
- [ ] Add CAPTCHA solving integration
- [ ] Create web UI dashboard
- [ ] Add more export formats
- [ ] Implement data validation rules