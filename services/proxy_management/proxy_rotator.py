import asyncio
import random
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
import json
import structlog
from common.models.proxy_config import ProxyConfig, ProxyStatus, ProxyType, ProxyProvider
from .vpn_manager import VPNManager

logger = structlog.get_logger()


class RotationStrategy(str, Enum):
    """Proxy rotation strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_USED = "least_used"
    HEALTH_BASED = "health_based"
    RANDOM = "random"
    STICKY_SESSION = "sticky_session"
    GEOGRAPHIC = "geographic"


@dataclass
class ProxyPool:
    """Proxy pool configuration"""
    name: str
    proxies: List[ProxyConfig]
    strategy: RotationStrategy
    health_check_interval: int = 300  # 5 minutes
    max_concurrent_per_proxy: int = 5
    session_timeout: int = 1800  # 30 minutes


class ProxyRotator:
    """Advanced proxy rotation and management system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.pools: Dict[str, ProxyPool] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.proxy_stats: Dict[str, Dict[str, Any]] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        self.logger = logger.bind(service="proxy_rotator")
        self.vpn_manager: Optional[VPNManager] = None
        
    async def initialize(self):
        """Initialize proxy rotator"""
        try:
            self.redis = redis.from_url(self.redis_url)
            await self.redis.ping()
            
            # Initialize VPN manager
            self.vpn_manager = VPNManager()
            await self.vpn_manager.initialize()
            
            # Load proxy pools from Redis
            await self._load_proxy_pools()
            
            # Start health check task
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.logger.info("Proxy rotator initialized", pools=len(self.pools))
            
        except Exception as e:
            self.logger.error("Failed to initialize proxy rotator", error=str(e))
            raise
    
    async def close(self):
        """Close proxy rotator"""
        try:
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            if self.vpn_manager:
                await self.vpn_manager.disconnect()
            
            if self.redis:
                await self.redis.close()
            
            self.logger.info("Proxy rotator closed")
            
        except Exception as e:
            self.logger.error("Failed to close proxy rotator", error=str(e))
    
    async def add_proxy_pool(self, pool: ProxyPool):
        """Add a proxy pool"""
        self.pools[pool.name] = pool
        await self._save_proxy_pool(pool)
        self.logger.info("Proxy pool added", pool_name=pool.name, proxy_count=len(pool.proxies))
    
    async def remove_proxy_pool(self, pool_name: str):
        """Remove a proxy pool"""
        if pool_name in self.pools:
            del self.pools[pool_name]
            await self.redis.delete(f"proxy_pool:{pool_name}")
            self.logger.info("Proxy pool removed", pool_name=pool_name)
    
    async def get_proxy(
        self, 
        pool_name: str = "default", 
        session_id: Optional[str] = None,
        country: Optional[str] = None,
        sticky_duration: Optional[int] = None
    ) -> Optional[ProxyConfig]:
        """Get a proxy from the specified pool"""
        
        if pool_name not in self.pools:
            self.logger.error("Proxy pool not found", pool_name=pool_name)
            return None
        
        pool = self.pools[pool_name]
        
        # Check for sticky session
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if time.time() - session["created_at"] < session.get("duration", pool.session_timeout):
                proxy_id = session["proxy_id"]
                proxy = next((p for p in pool.proxies if self._get_proxy_id(p) == proxy_id), None)
                if proxy and proxy.status == ProxyStatus.ACTIVE:
                    return proxy
        
        # Filter proxies by country if specified
        available_proxies = [p for p in pool.proxies if p.status == ProxyStatus.ACTIVE]
        if country:
            available_proxies = [p for p in available_proxies if p.country and p.country.lower() == country.lower()]
        
        if not available_proxies:
            self.logger.warning("No available proxies in pool", pool_name=pool_name, country=country)
            return None
        
        # Select proxy based on strategy
        proxy = await self._select_proxy(available_proxies, pool.strategy)
        
        if proxy:
            # Create or update session
            if session_id:
                self.active_sessions[session_id] = {
                    "proxy_id": self._get_proxy_id(proxy),
                    "created_at": time.time(),
                    "duration": sticky_duration or pool.session_timeout,
                    "requests": 0
                }
            
            # Update proxy stats
            await self._update_proxy_stats(proxy, "selected")
            
            self.logger.info(
                "Proxy selected",
                pool_name=pool_name,
                proxy_host=proxy.host,
                proxy_country=proxy.country,
                session_id=session_id
            )
        
        return proxy
    
    async def _select_proxy(self, proxies: List[ProxyConfig], strategy: RotationStrategy) -> Optional[ProxyConfig]:
        """Select proxy based on rotation strategy"""
        
        if strategy == RotationStrategy.RANDOM:
            return random.choice(proxies)
        
        elif strategy == RotationStrategy.ROUND_ROBIN:
            # Simple round-robin based on usage count
            proxy_usage = {}
            for proxy in proxies:
                proxy_id = self._get_proxy_id(proxy)
                stats = await self._get_proxy_stats(proxy_id)
                proxy_usage[proxy_id] = stats.get("total_requests", 0)
            
            # Select proxy with least usage
            min_usage = min(proxy_usage.values())
            candidates = [p for p in proxies if proxy_usage[self._get_proxy_id(p)] == min_usage]
            return random.choice(candidates)
        
        elif strategy == RotationStrategy.LEAST_USED:
            # Select proxy with least current usage
            proxy_usage = {}
            for proxy in proxies:
                proxy_id = self._get_proxy_id(proxy)
                stats = await self._get_proxy_stats(proxy_id)
                proxy_usage[proxy_id] = stats.get("current_requests", 0)
            
            min_usage = min(proxy_usage.values())
            candidates = [p for p in proxies if proxy_usage[self._get_proxy_id(p)] == min_usage]
            return random.choice(candidates)
        
        elif strategy == RotationStrategy.HEALTH_BASED:
            # Select proxy with best health score
            best_proxy = None
            best_score = -1
            
            for proxy in proxies:
                score = proxy.health_score * 0.7 + proxy.success_rate * 0.3
                if score > best_score:
                    best_score = score
                    best_proxy = proxy
            
            return best_proxy
        
        elif strategy == RotationStrategy.GEOGRAPHIC:
            # Prefer proxies from diverse locations
            country_counts = {}
            for proxy in proxies:
                country = proxy.country or "unknown"
                country_counts[country] = country_counts.get(country, 0) + 1
            
            # Select from least used country
            min_count = min(country_counts.values())
            preferred_countries = [country for country, count in country_counts.items() if count == min_count]
            preferred_country = random.choice(preferred_countries)
            
            candidates = [p for p in proxies if (p.country or "unknown") == preferred_country]
            return random.choice(candidates)
        
        return random.choice(proxies)
    
    async def release_proxy(self, proxy: ProxyConfig, session_id: Optional[str] = None):
        """Release a proxy back to the pool"""
        try:
            # Update proxy stats
            await self._update_proxy_stats(proxy, "released")
            
            # Remove from active sessions if session-based
            if session_id and session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            self.logger.info("Proxy released", proxy_host=proxy.host, session_id=session_id)
            
        except Exception as e:
            self.logger.error("Failed to release proxy", error=str(e))
    
    async def report_proxy_result(self, proxy: ProxyConfig, success: bool, response_time: Optional[float] = None):
        """Report proxy usage result"""
        try:
            # Update proxy health
            proxy.update_health_score(success)
            
            # Update proxy stats
            await self._update_proxy_stats(proxy, "request_completed", {
                "success": success,
                "response_time": response_time
            })
            
            # Update proxy status based on health
            if proxy.health_score < 0.3:
                proxy.status = ProxyStatus.BLOCKED
                self.logger.warning("Proxy marked as blocked", proxy_host=proxy.host, health_score=proxy.health_score)
            elif proxy.health_score < 0.5:
                proxy.status = ProxyStatus.RATE_LIMITED
                self.logger.warning("Proxy marked as rate limited", proxy_host=proxy.host, health_score=proxy.health_score)
            else:
                proxy.status = ProxyStatus.ACTIVE
            
            # Save updated proxy
            await self._save_proxy_config(proxy)
            
        except Exception as e:
            self.logger.error("Failed to report proxy result", error=str(e))
    
    async def rotate_vpn_if_needed(self, failure_threshold: int = 3) -> bool:
        """Rotate VPN connection if too many proxy failures"""
        try:
            if not self.vpn_manager:
                return False
            
            # Check recent failures across all proxies
            recent_failures = 0
            current_time = time.time()
            
            for proxy_id, stats in self.proxy_stats.items():
                recent_failures += stats.get("recent_failures", 0)
            
            if recent_failures >= failure_threshold:
                self.logger.info("High failure rate detected, rotating VPN", failures=recent_failures)
                
                # Rotate VPN connection
                success = await self.vpn_manager.rotate_server()
                
                if success:
                    # Reset proxy failure counts
                    for stats in self.proxy_stats.values():
                        stats["recent_failures"] = 0
                    
                    # Update proxy configs with new VPN proxy
                    vpn_proxy = self.vpn_manager.get_proxy_config()
                    if vpn_proxy:
                        await self._add_vpn_proxy_to_pools(vpn_proxy)
                    
                    return True
                
            return False
            
        except Exception as e:
            self.logger.error("Failed to rotate VPN", error=str(e))
            return False
    
    async def _add_vpn_proxy_to_pools(self, vpn_proxy: ProxyConfig):
        """Add VPN proxy to all pools"""
        for pool in self.pools.values():
            # Remove existing VPN proxies
            pool.proxies = [p for p in pool.proxies if p.provider != ProxyProvider.PRIVATE_INTERNET_ACCESS]
            
            # Add new VPN proxy
            pool.proxies.append(vpn_proxy)
            
            await self._save_proxy_pool(pool)
    
    async def _health_check_loop(self):
        """Periodic health check for all proxies"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                for pool in self.pools.values():
                    await self._health_check_pool(pool)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _health_check_pool(self, pool: ProxyPool):
        """Health check for a proxy pool"""
        try:
            for proxy in pool.proxies:
                if proxy.status == ProxyStatus.FAILED:
                    continue
                
                # Simple health check - could be expanded
                if proxy.health_score < 0.2:
                    proxy.status = ProxyStatus.BLOCKED
                elif proxy.health_score < 0.4:
                    proxy.status = ProxyStatus.RATE_LIMITED
                else:
                    proxy.status = ProxyStatus.ACTIVE
                
                await self._save_proxy_config(proxy)
            
            self.logger.info("Health check completed", pool_name=pool.name)
            
        except Exception as e:
            self.logger.error("Pool health check failed", pool_name=pool.name, error=str(e))
    
    async def _load_proxy_pools(self):
        """Load proxy pools from Redis"""
        try:
            keys = await self.redis.keys("proxy_pool:*")
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    pool_data = json.loads(data)
                    proxies = [ProxyConfig(**proxy_data) for proxy_data in pool_data["proxies"]]
                    
                    pool = ProxyPool(
                        name=pool_data["name"],
                        proxies=proxies,
                        strategy=RotationStrategy(pool_data["strategy"]),
                        health_check_interval=pool_data.get("health_check_interval", 300),
                        max_concurrent_per_proxy=pool_data.get("max_concurrent_per_proxy", 5),
                        session_timeout=pool_data.get("session_timeout", 1800)
                    )
                    
                    self.pools[pool.name] = pool
        
        except Exception as e:
            self.logger.error("Failed to load proxy pools", error=str(e))
    
    async def _save_proxy_pool(self, pool: ProxyPool):
        """Save proxy pool to Redis"""
        try:
            pool_data = {
                "name": pool.name,
                "proxies": [proxy.dict() for proxy in pool.proxies],
                "strategy": pool.strategy.value,
                "health_check_interval": pool.health_check_interval,
                "max_concurrent_per_proxy": pool.max_concurrent_per_proxy,
                "session_timeout": pool.session_timeout
            }
            
            await self.redis.set(f"proxy_pool:{pool.name}", json.dumps(pool_data))
            
        except Exception as e:
            self.logger.error("Failed to save proxy pool", pool_name=pool.name, error=str(e))
    
    async def _save_proxy_config(self, proxy: ProxyConfig):
        """Save proxy configuration to Redis"""
        try:
            proxy_id = self._get_proxy_id(proxy)
            await self.redis.set(f"proxy_config:{proxy_id}", json.dumps(proxy.dict()))
            
        except Exception as e:
            self.logger.error("Failed to save proxy config", error=str(e))
    
    async def _get_proxy_stats(self, proxy_id: str) -> Dict[str, Any]:
        """Get proxy statistics"""
        try:
            data = await self.redis.get(f"proxy_stats:{proxy_id}")
            if data:
                return json.loads(data)
            return {}
        except Exception as e:
            self.logger.error("Failed to get proxy stats", proxy_id=proxy_id, error=str(e))
            return {}
    
    async def _update_proxy_stats(self, proxy: ProxyConfig, event: str, data: Dict[str, Any] = None):
        """Update proxy statistics"""
        try:
            proxy_id = self._get_proxy_id(proxy)
            stats = await self._get_proxy_stats(proxy_id)
            
            if event == "selected":
                stats["total_requests"] = stats.get("total_requests", 0) + 1
                stats["current_requests"] = stats.get("current_requests", 0) + 1
                stats["last_used"] = time.time()
            
            elif event == "released":
                stats["current_requests"] = max(0, stats.get("current_requests", 0) - 1)
            
            elif event == "request_completed":
                if data:
                    stats["completed_requests"] = stats.get("completed_requests", 0) + 1
                    
                    if data.get("success"):
                        stats["successful_requests"] = stats.get("successful_requests", 0) + 1
                        stats["recent_failures"] = max(0, stats.get("recent_failures", 0) - 1)
                    else:
                        stats["failed_requests"] = stats.get("failed_requests", 0) + 1
                        stats["recent_failures"] = stats.get("recent_failures", 0) + 1
                    
                    if data.get("response_time"):
                        response_times = stats.get("response_times", [])
                        response_times.append(data["response_time"])
                        if len(response_times) > 100:  # Keep only last 100
                            response_times = response_times[-100:]
                        stats["response_times"] = response_times
                        stats["avg_response_time"] = sum(response_times) / len(response_times)
            
            await self.redis.set(f"proxy_stats:{proxy_id}", json.dumps(stats))
            
        except Exception as e:
            self.logger.error("Failed to update proxy stats", error=str(e))
    
    def _get_proxy_id(self, proxy: ProxyConfig) -> str:
        """Get unique proxy identifier"""
        return f"{proxy.host}:{proxy.port}:{proxy.proxy_type.value}"
    
    def get_pool_status(self, pool_name: str) -> Dict[str, Any]:
        """Get proxy pool status"""
        if pool_name not in self.pools:
            return {"error": "Pool not found"}
        
        pool = self.pools[pool_name]
        status = {
            "name": pool.name,
            "strategy": pool.strategy.value,
            "total_proxies": len(pool.proxies),
            "active_proxies": len([p for p in pool.proxies if p.status == ProxyStatus.ACTIVE]),
            "blocked_proxies": len([p for p in pool.proxies if p.status == ProxyStatus.BLOCKED]),
            "failed_proxies": len([p for p in pool.proxies if p.status == ProxyStatus.FAILED]),
            "active_sessions": len(self.active_sessions)
        }
        
        return status
    
    def get_all_pools_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all proxy pools"""
        return {
            pool_name: self.get_pool_status(pool_name)
            for pool_name in self.pools.keys()
        }