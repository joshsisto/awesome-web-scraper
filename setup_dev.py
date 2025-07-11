#!/usr/bin/env python3
"""
Development setup script for the web scraper
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, description="", check=True):
    """Run a command with error handling"""
    print(f"🔧 {description}: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is available"""
    print("🐳 Checking Docker availability...")
    if run_command(["docker", "--version"], "Docker version check", check=False):
        if run_command(["docker", "info"], "Docker daemon check", check=False):
            print("   ✅ Docker is running")
            return True
        else:
            print("   ❌ Docker daemon is not running")
            return False
    else:
        print("   ❌ Docker not found")
        return False

def setup_environment():
    """Set up environment variables"""
    print("🌍 Setting up environment...")
    
    env_content = """# Web Scraper Environment Configuration
# Database
MONGODB_URL=mongodb://scraper:scraper_pass@localhost:27017/scraper
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Proxy Settings
DEFAULT_PROXY_POOL=default
PROXY_ROTATION_STRATEGY=health_based
PROXY_HEALTH_CHECK_INTERVAL=300

# VPN Settings (Optional - requires PIA account)
PIA_USERNAME=your_username
PIA_PASSWORD=your_password
VPN_AUTO_CONNECT=true
VPN_PREFERRED_COUNTRIES=US,UK,DE,CA

# Anti-Detection
USE_STEALTH_MODE=true
HUMAN_LIKE_DELAYS=true
USER_AGENT_ROTATION=true

# Performance
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=5

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Development
DEBUG=true
TEST_MODE=false
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        env_file.write_text(env_content)
        print("   ✅ Created .env file")
    else:
        print("   ℹ️  .env file already exists")

def start_infrastructure():
    """Start infrastructure services"""
    print("🏗️  Starting infrastructure services...")
    
    # Check if services are already running
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if "scraper_mongodb" in result.stdout and "scraper_redis" in result.stdout:
            print("   ℹ️  Infrastructure services already running")
            return True
    except:
        pass
    
    # Start essential services
    services = ["mongodb", "redis"]
    
    for service in services:
        if run_command(["docker-compose", "up", "-d", service], f"Starting {service}"):
            print(f"   ✅ {service} started")
        else:
            print(f"   ❌ Failed to start {service}")
            return False
    
    # Wait for services to be ready
    print("   ⏳ Waiting for services to be ready...")
    import time
    time.sleep(5)
    
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print("🐍 Installing Python dependencies...")
    
    # Try to install in a way that works with externally managed environments
    try:
        # First try with pip
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Dependencies installed successfully")
            return True
        else:
            print("   ⚠️  Regular pip install failed, trying alternative method...")
            
            # Try with --user flag
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Dependencies installed with --user flag")
                return True
            else:
                print("   ❌ Failed to install dependencies")
                print(f"   Error: {result.stderr}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error installing dependencies: {e}")
        return False

def setup_playwright():
    """Setup Playwright browsers"""
    print("🎭 Setting up Playwright browsers...")
    
    try:
        # Install Playwright browsers
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Playwright browsers installed")
            return True
        else:
            print("   ❌ Failed to install Playwright browsers")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error setting up Playwright: {e}")
        return False

def check_services():
    """Check if all services are running"""
    print("🔍 Checking service health...")
    
    checks = [
        ("MongoDB", ["docker", "exec", "scraper_mongodb", "mongosh", "--eval", "db.adminCommand('ping')"]),
        ("Redis", ["docker", "exec", "scraper_redis", "redis-cli", "ping"]),
    ]
    
    for service_name, cmd in checks:
        if run_command(cmd, f"Checking {service_name}", check=False):
            print(f"   ✅ {service_name} is healthy")
        else:
            print(f"   ❌ {service_name} is not responding")
            return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Web Scraper Development Environment")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    steps = [
        ("Environment Setup", setup_environment),
        ("Docker Check", check_docker),
        ("Infrastructure Services", start_infrastructure),
        ("Service Health Check", check_services),
    ]
    
    # Run setup steps
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        if not step_func():
            print(f"❌ Setup failed at step: {step_name}")
            return 1
    
    print("\n🎉 Development environment setup complete!")
    print("\n📝 Next steps:")
    print("1. Configure your .env file with VPN credentials (optional)")
    print("2. Run test scenarios: python test_scenarios.py")
    print("3. Start monitoring: docker-compose up -d prometheus grafana")
    print("4. View Grafana dashboard: http://localhost:3000 (admin/admin)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())