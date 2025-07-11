#!/usr/bin/env python3
"""
VPN Checker - Ensures scraper only runs when connected to VPN

This module checks the current public IP address and prevents the scraper
from running if it matches the home IP address (23.115.156.177).

Features:
    - Multiple IP detection services for reliability
    - Fast fail-safe approach
    - Clear error messages
    - Timeout handling
    - Retry logic with different services
"""

import asyncio
import httpx
import sys
from typing import Optional, List
import logging
from datetime import datetime


class VPNChecker:
    """Check if VPN is active by verifying public IP"""
    
    # Josh's home IP that should NEVER be used for scraping
    BLOCKED_HOME_IP = "23.115.156.177"
    
    # Multiple IP detection services for reliability
    IP_SERVICES = [
        "https://httpbin.org/ip",
        "https://ipinfo.io/ip", 
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ifconfig.me/ip"
    ]
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for VPN checker"""
        logger = logging.getLogger('vpn_checker')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - VPN_CHECK - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def get_current_ip(self) -> Optional[str]:
        """Get current public IP address using multiple services"""
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            
            for service_url in self.IP_SERVICES:
                try:
                    self.logger.debug(f"Checking IP via {service_url}")
                    response = await client.get(service_url)
                    
                    if response.status_code == 200:
                        # Parse IP from different response formats
                        ip = self._extract_ip_from_response(response.text, service_url)
                        if ip:
                            self.logger.debug(f"Got IP {ip} from {service_url}")
                            return ip
                    
                except Exception as e:
                    self.logger.debug(f"Failed to get IP from {service_url}: {e}")
                    continue
            
            return None
    
    def _extract_ip_from_response(self, response_text: str, service_url: str) -> Optional[str]:
        """Extract IP address from different service response formats"""
        
        response_text = response_text.strip()
        
        if "httpbin.org" in service_url:
            # httpbin.org returns JSON: {"origin": "1.2.3.4"}
            try:
                import json
                data = json.loads(response_text)
                return data.get("origin", "").split(",")[0].strip()
            except json.JSONDecodeError:
                return None
        
        else:
            # Most services return plain text IP
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if self._is_valid_ip(line):
                    return line
            
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Basic IP address validation"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                if not (0 <= int(part) <= 255):
                    return False
            
            return True
        except (ValueError, AttributeError):
            return False
    
    async def check_vpn_status(self) -> tuple[bool, str, Optional[str]]:
        """
        Check if VPN is active
        
        Returns:
            tuple: (is_vpn_active, message, current_ip)
        """
        
        self.logger.info("🔍 Checking VPN status...")
        
        try:
            current_ip = await self.get_current_ip()
            
            if not current_ip:
                return False, "❌ Could not determine current IP address", None
            
            self.logger.info(f"📍 Current public IP: {current_ip}")
            
            if current_ip == self.BLOCKED_HOME_IP:
                return False, f"🚨 BLOCKED: Running from home IP ({current_ip}). VPN required!", current_ip
            
            return True, f"✅ VPN active. Current IP: {current_ip}", current_ip
            
        except Exception as e:
            self.logger.error(f"VPN check failed: {e}")
            return False, f"❌ VPN check failed: {e}", None
    
    def enforce_vpn_requirement(self) -> Optional[str]:
        """
        Synchronous wrapper that enforces VPN requirement
        Exits the program if VPN is not active
        
        Returns:
            str: Current IP if VPN is active, otherwise exits
        """
        
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create new loop in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.check_vpn_status())
                    is_vpn_active, message, current_ip = future.result(timeout=30)
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                is_vpn_active, message, current_ip = asyncio.run(self.check_vpn_status())
            
            print(message)
            
            if not is_vpn_active:
                print("\n🛑 SCRAPING BLOCKED FOR SECURITY")
                print("=" * 50)
                print("For security reasons, scraping is not allowed from your home IP.")
                print("Please connect to VPN before running the scraper.")
                print("\nHome IP (BLOCKED): 23.115.156.177")
                if current_ip:
                    print(f"Current IP: {current_ip}")
                print("\n💡 Solutions:")
                print("  1. Connect to VPN")
                print("  2. Use a proxy service")
                print("  3. Run from a different network")
                print("  4. Use --skip-vpn-check for testing (NOT RECOMMENDED)")
                print("=" * 50)
                sys.exit(1)
            
            return current_ip
            
        except KeyboardInterrupt:
            print("\n🛑 VPN check interrupted")
            sys.exit(1)
        except Exception as e:
            print(f"🚨 VPN check failed: {e}")
            print("🛑 Blocking scraping for security")
            sys.exit(1)


# Convenience functions for easy integration
async def async_check_vpn() -> tuple[bool, str, Optional[str]]:
    """Async VPN check function"""
    checker = VPNChecker()
    return await checker.check_vpn_status()


def require_vpn() -> str:
    """
    Require VPN to be active, exit if not
    
    Returns:
        str: Current IP address if VPN is active
    """
    checker = VPNChecker()
    return checker.enforce_vpn_requirement()


def check_vpn_quietly() -> Optional[str]:
    """
    Check VPN status without exiting
    
    Returns:
        str: Current IP if VPN active, None if not
    """
    try:
        checker = VPNChecker()
        is_vpn_active, message, current_ip = asyncio.run(checker.check_vpn_status())
        return current_ip if is_vpn_active else None
    except Exception:
        return None


# CLI interface for standalone usage
def main():
    """CLI interface for VPN checker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check VPN status for scraping")
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Quiet mode - no output, exit code only')
    parser.add_argument('--timeout', '-t', type=float, default=10.0,
                       help='Timeout for IP checks (default: 10s)')
    
    args = parser.parse_args()
    
    if args.quiet:
        # Quiet mode - just exit codes
        try:
            checker = VPNChecker(timeout=args.timeout)
            is_vpn_active, _, _ = asyncio.run(checker.check_vpn_status())
            sys.exit(0 if is_vpn_active else 1)
        except Exception:
            sys.exit(1)
    else:
        # Verbose mode
        print("🔒 VPN Status Checker")
        print("=" * 30)
        print(f"🏠 Home IP (BLOCKED): {VPNChecker.BLOCKED_HOME_IP}")
        print(f"⏱️  Timeout: {args.timeout}s")
        print()
        
        try:
            checker = VPNChecker(timeout=args.timeout)
            is_vpn_active, message, current_ip = asyncio.run(checker.check_vpn_status())
            
            print(message)
            
            if is_vpn_active:
                print("🎉 Scraping is ALLOWED")
                sys.exit(0)
            else:
                print("🚫 Scraping is BLOCKED")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Check interrupted")
            sys.exit(1)
        except Exception as e:
            print(f"💥 Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()