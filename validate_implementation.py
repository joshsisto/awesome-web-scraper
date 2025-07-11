#!/usr/bin/env python3
"""
Simple validation script to check if the implementation can be imported
and basic functionality works without external dependencies.
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_model_imports():
    """Test importing models"""
    try:
        from common.models.scrape_request import ScrapeRequest, ScrapeMethod, AuthType
        from common.models.scrape_result import ScrapeResult, ScrapeStatus
        from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider
        print("✅ Models imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False

def test_basic_model_creation():
    """Test basic model creation"""
    try:
        from common.models.scrape_request import ScrapeRequest, ScrapeMethod
        from common.models.scrape_result import ScrapeResult, ScrapeStatus
        from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider
        
        # Test ScrapeRequest
        request = ScrapeRequest(
            url="https://example.com",
            method=ScrapeMethod.SCRAPY,
            selectors={"title": "h1"}
        )
        assert str(request.url) == "https://example.com/"
        assert request.method == ScrapeMethod.SCRAPY
        
        # Test ScrapeResult
        result = ScrapeResult(
            request_id="test123",
            status=ScrapeStatus.SUCCESS,
            data={"title": "Test"}
        )
        assert result.request_id == "test123"
        assert result.status == ScrapeStatus.SUCCESS
        
        # Test ProxyConfig
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER
        )
        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080
        
        print("✅ Basic model creation works")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create models: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_proxy_url_generation():
    """Test proxy URL generation"""
    try:
        from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider
        
        # Test without auth
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER
        )
        url = proxy.get_proxy_url()
        assert url == "http://proxy.example.com:8080"
        
        # Test with auth
        proxy.username = "user"
        proxy.password = "pass"
        url = proxy.get_proxy_url()
        assert url == "http://user:pass@proxy.example.com:8080"
        
        print("✅ Proxy URL generation works")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate proxy URL: {e}")
        return False

def test_health_score_update():
    """Test health score update"""
    try:
        from common.models.proxy_config import ProxyConfig, ProxyType, ProxyProvider
        
        proxy = ProxyConfig(
            host="proxy.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            provider=ProxyProvider.DATACENTER
        )
        
        initial_score = proxy.health_score
        proxy.update_health_score(True)
        assert proxy.health_score >= initial_score
        assert proxy.total_requests == 1
        assert proxy.failed_requests == 0
        
        proxy.update_health_score(False)
        assert proxy.total_requests == 2
        assert proxy.failed_requests == 1
        
        print("✅ Health score update works")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update health score: {e}")
        return False

def test_service_imports():
    """Test importing service modules"""
    try:
        # Test importing service classes (may fail due to missing dependencies)
        from services.extraction.extraction_orchestrator import ExtractionOrchestrator
        from services.proxy_management.vpn_manager import VPNManager
        from services.proxy_management.proxy_rotator import ProxyRotator
        
        print("✅ Service modules imported successfully")
        return True
        
    except ImportError as e:
        print(f"⚠️  Service imports failed (expected due to missing dependencies): {e}")
        return False

def test_project_structure():
    """Test project structure"""
    try:
        required_dirs = [
            "services/extraction",
            "services/proxy_management",
            "common/models",
            "tests/unit",
            "docker",
            "scripts"
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                print(f"❌ Missing directory: {dir_path}")
                return False
        
        required_files = [
            "requirements.txt",
            "pyproject.toml",
            "docker-compose.yml",
            "README.md",
            "pytest.ini"
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ Missing file: {file_path}")
                return False
        
        print("✅ Project structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Failed to check project structure: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🔍 Validating implementation...")
    print()
    
    tests = [
        test_project_structure,
        test_model_imports,
        test_basic_model_creation,
        test_proxy_url_generation,
        test_health_score_update,
        test_service_imports,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed or had warnings")
        return 1

if __name__ == "__main__":
    sys.exit(main())