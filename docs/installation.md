# Installation Guide

This guide will help you install and set up the Awesome Web Scraper on your system.

## 📋 Prerequisites

### System Requirements
- **Python 3.11+** (recommended: Python 3.12)
- **Docker** and **Docker Compose** (for infrastructure services)
- **Git** (for cloning the repository)
- **4GB+ RAM** (recommended for Playwright browser automation)
- **Linux/macOS/Windows** (tested on all platforms)

### Optional Requirements
- **Private Internet Access account** (for VPN features)
- **Kubernetes cluster** (for production deployment)

---

## 🚀 Quick Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd awesome-scraper
```

### 2. Run the Setup Script
```bash
# Make the setup script executable
chmod +x setup_dev.py

# Run the automated setup
python setup_dev.py
```

The setup script will:
- ✅ Create environment configuration
- ✅ Check Docker availability
- ✅ Start infrastructure services (MongoDB, Redis)
- ✅ Verify service health

---

## 🔧 Manual Installation

If you prefer manual setup or the automated script fails:

### 1. Python Environment Setup

#### Option A: Using Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Using Poetry
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
poetry shell
```

### 2. Install Browser Dependencies
```bash
# Install Playwright browsers
playwright install chromium

# Optional: Install all browsers
playwright install
```

### 3. Infrastructure Services

#### Using Docker Compose (Recommended)
```bash
# Start essential services
docker-compose up -d mongodb redis

# Start monitoring services (optional)
docker-compose up -d prometheus grafana

# Verify services are running
docker-compose ps
```

#### Manual Service Installation
If you prefer not to use Docker:

**MongoDB:**
```bash
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS
brew install mongodb/brew/mongodb-community

# Start MongoDB
sudo systemctl start mongod
```

**Redis:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

---

## ⚙️ Environment Configuration

### Basic Configuration (.env)
```bash
# Database Configuration
MONGODB_URL=mongodb://scraper:scraper_pass@localhost:27017/scraper
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Proxy Settings
DEFAULT_PROXY_POOL=default
PROXY_ROTATION_STRATEGY=health_based

# Performance
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### VPN Configuration (Optional)
```bash
# Private Internet Access
PIA_USERNAME=your_username
PIA_PASSWORD=your_password
VPN_AUTO_CONNECT=true
VPN_PREFERRED_COUNTRIES=US,UK,DE,CA

# VPN Settings
USE_VPN=true
VPN_ROTATION_INTERVAL=3600  # 1 hour
```

### Anti-Detection Settings
```bash
# Stealth Configuration
USE_STEALTH_MODE=true
HUMAN_LIKE_DELAYS=true
USER_AGENT_ROTATION=true

# Request Patterns
MIN_REQUEST_DELAY=1
MAX_REQUEST_DELAY=5
RANDOMIZE_DELAYS=true
```

---

## 🧪 Verify Installation

### 1. Run the Validation Script
```bash
python validate_implementation.py
```

Expected output:
```
🔍 Validating implementation...
✅ Project structure is correct
✅ Models imported successfully
✅ Basic model creation works
✅ Proxy URL generation works
✅ Health score update works
```

### 2. Run Integration Tests
```bash
python integration_tests.py
```

### 3. Run the Complete Test Suite
```bash
python final_test_suite.py
```

You should see 100% success rate across all tests.

---

## 🐳 Docker Installation

### Full Docker Setup
```bash
# Build all services
docker-compose build

# Start complete stack
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Docker Services
- **MongoDB** - `localhost:27017`
- **Redis** - `localhost:6379`
- **Prometheus** - `localhost:9090`
- **Grafana** - `localhost:3000` (admin/admin)

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check if ports are in use
netstat -tulpn | grep :27017
netstat -tulpn | grep :6379

# Stop conflicting services
sudo systemctl stop mongod
sudo systemctl stop redis
```

#### 2. Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Restart session or run:
newgrp docker
```

#### 3. Python Module Not Found
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. Playwright Browser Installation
```bash
# Install system dependencies for Playwright
sudo apt-get install libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libgtk-3-0 libasound2

# Reinstall browsers
playwright install --with-deps chromium
```

### Health Checks

#### Service Health Check
```bash
# MongoDB
docker exec scraper_mongodb mongosh --eval "db.adminCommand('ping')"

# Redis
docker exec scraper_redis redis-cli ping

# All services
python -c "
import asyncio
from setup_dev import check_services
asyncio.run(check_services())
"
```

#### Network Connectivity
```bash
# Test external connectivity
curl -I https://httpbin.org/get

# Test proxy detection
curl -I https://httpbin.org/ip
```

---

## 🎯 Next Steps

After successful installation:

1. **[Quick Start Tutorial](quick-start.md)** - Run your first scraping job
2. **[Configuration Guide](configuration.md)** - Customize for your needs
3. **[VPN Setup](vpn.md)** - Configure Private Internet Access
4. **[API Reference](api-reference.md)** - Explore available features

---

## 📞 Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review service logs: `docker-compose logs`
3. Verify environment configuration
4. Run health checks and validation scripts

**Installation successful?** Proceed to the [Quick Start Tutorial](quick-start.md)!