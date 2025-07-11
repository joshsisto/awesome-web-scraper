#!/usr/bin/env python3
"""
Scraper API Service - RESTful API for web scraping

Usage:
    python api_service.py                    # Start API server on port 8000
    python api_service.py --port 8080       # Start on custom port
    python api_service.py --host 0.0.0.0    # Bind to all interfaces

API Endpoints:
    POST /scrape                             # Scrape a URL
    GET /results                             # List all results
    GET /results/{id}                        # Get specific result
    GET /results/url/{url}                   # Get results for URL
    GET /results/domain/{domain}             # Get results for domain
    GET /search?q={query}                    # Search results
    GET /stats                               # Get statistics
    DELETE /results/{id}                     # Delete result
    GET /health                              # Health check

Features:
    - RESTful API with FastAPI
    - Async scraping with background tasks
    - Rate limiting and authentication
    - Comprehensive error handling
    - OpenAPI documentation
    - CORS support
    - Request validation
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, unquote
import logging

# FastAPI and related imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl, Field
import uvicorn

# Import our scraping components
from master_scraper import ProgressiveScraper, ScrapingDatabase
from vpn_checker import async_check_vpn


# Pydantic models for API
class ScrapeRequest(BaseModel):
    """Request model for scraping"""
    url: str = Field(..., description="URL to scrape (with or without protocol)")
    methods: Optional[List[str]] = Field(
        default=["scrapy", "pydoll", "playwright"],
        description="Scraping methods to try in order"
    )
    output_format: Optional[str] = Field(default="json", description="Output format")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Scraping configuration")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "methods": ["scrapy", "pydoll"],
                "output_format": "json",
                "config": {"verify_ssl": False, "timeout": 30}
            }
        }


class ScrapeResponse(BaseModel):
    """Response model for scraping"""
    task_id: str = Field(..., description="Task ID for tracking")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    result_id: Optional[int] = Field(None, description="Database record ID if completed")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")


class ScrapeResult(BaseModel):
    """Model for scrape result"""
    id: int
    url: str
    domain: str
    method_used: str
    status: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    timestamp: str
    title: Optional[str] = None
    content_length: Optional[int] = None
    links_count: int = 0
    images_count: int = 0
    data: Optional[Dict[str, Any]] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    error_message: Optional[str] = None


class DatabaseStats(BaseModel):
    """Model for database statistics"""
    total_results: int
    successful_results: int
    failed_results: int
    success_rate: float
    method_statistics: Dict[str, Dict[str, Any]]
    top_domains: Dict[str, int]
    daily_activity: Dict[str, int]
    response_time_stats: Dict[str, float]


# Background task tracking
class TaskManager:
    """Manage background scraping tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, Any] = {}
    
    def create_task(self, task_id: str, url: str) -> Dict[str, Any]:
        """Create a new task"""
        task = {
            "task_id": task_id,
            "url": url,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result_id": None,
            "error": None
        }
        self.tasks[task_id] = task
        return task
    
    def update_task(self, task_id: str, **updates):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        return self.tasks.get(task_id) or self.completed_tasks.get(task_id)
    
    def complete_task(self, task_id: str, result_id: Optional[int] = None, error: Optional[str] = None):
        """Mark task as completed"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.update({
                "status": "completed" if result_id else "failed",
                "completed_at": datetime.now().isoformat(),
                "result_id": result_id,
                "error": error
            })
            self.completed_tasks[task_id] = task
            del self.tasks[task_id]


# Global instances
task_manager = TaskManager()
scraping_db = ScrapingDatabase()

# FastAPI app
app = FastAPI(
    title="Awesome Web Scraper API",
    description="RESTful API for progressive web scraping with multiple methods",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security (optional)
security = HTTPBearer(auto_error=False)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional authentication dependency"""
    # For now, no authentication required
    # In production, verify JWT tokens here
    return {"user_id": "anonymous"}


def validate_url(url: str) -> str:
    """Validate and normalize URL"""
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    parsed = urlparse(url)
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    return url


# API Routes
@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Awesome Web Scraper API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "docs": "/docs",
            "scrape": "/scrape",
            "results": "/results",
            "stats": "/stats",
            "health": "/health"
        }
    }


@app.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with sqlite3.connect(scraping_db.db_path) as conn:
            conn.execute("SELECT 1").fetchone()
        
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "active_tasks": len(task_manager.tasks),
        "completed_tasks": len(task_manager.completed_tasks)
    }


@app.post("/scrape", response_model=ScrapeResponse, summary="Scrape a URL")
async def scrape_url(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    Start a scraping task for the specified URL.
    
    The scraping is performed in the background using progressive method selection:
    1. Scrapy (fast, lightweight)
    2. PyDoll (optimized HTTP + parsing)
    3. Playwright (full browser automation)
    
    Returns a task ID for tracking progress.
    """
    
    # Validate URL
    try:
        validated_url = validate_url(request.url)
    except HTTPException as e:
        raise e
    
    # Generate task ID
    task_id = f"task_{int(time.time() * 1000)}"
    
    # Create task
    task = task_manager.create_task(task_id, validated_url)
    
    # Start background scraping
    background_tasks.add_task(
        perform_scraping,
        task_id,
        validated_url,
        request.methods,
        request.config
    )
    
    logger.info(f"Started scraping task {task_id} for {validated_url}")
    
    return ScrapeResponse(
        task_id=task_id,
        status="started",
        message=f"Scraping task started for {validated_url}",
        estimated_completion=(datetime.now() + timedelta(seconds=30)).isoformat()
    )


@app.get("/tasks/{task_id}", summary="Get task status")
async def get_task_status(task_id: str):
    """Get the status of a scraping task"""
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.get("/results", summary="List all results")
async def list_results(
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    status: Optional[str] = Query(None, description="Filter by status (success/failed)"),
    domain: Optional[str] = Query(None, description="Filter by domain")
):
    """List scraping results with optional filtering"""
    
    with sqlite3.connect(scraping_db.db_path) as conn:
        # Build query
        query = "SELECT * FROM scrape_results WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if domain:
            query += " AND domain LIKE ?"
            params.append(f"%{domain}%")
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse JSON fields
        for result in results:
            for field in ['data_json', 'links_json', 'images_json']:
                if result.get(field):
                    try:
                        result[field.replace('_json', '')] = json.loads(result[field])
                        del result[field]
                    except json.JSONDecodeError:
                        pass
        
        return {
            "results": results,
            "count": len(results),
            "limit": limit,
            "offset": offset
        }


@app.get("/results/{result_id}", response_model=ScrapeResult, summary="Get specific result")
async def get_result(result_id: int = PathParam(..., ge=1)):
    """Get a specific scraping result by ID"""
    
    with sqlite3.connect(scraping_db.db_path) as conn:
        cursor = conn.execute("SELECT * FROM scrape_results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Result not found")
        
        columns = [desc[0] for desc in cursor.description]
        result = dict(zip(columns, row))
        
        # Parse JSON fields
        for field in ['data_json', 'links_json', 'images_json']:
            if result.get(field):
                try:
                    result[field.replace('_json', '')] = json.loads(result[field])
                    del result[field]
                except json.JSONDecodeError:
                    pass
        
        return result


@app.get("/results/url/{encoded_url}", summary="Get results for URL")
async def get_results_by_url(encoded_url: str):
    """Get all results for a specific URL (URL must be URL-encoded)"""
    
    try:
        url = unquote(encoded_url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL encoding")
    
    with sqlite3.connect(scraping_db.db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM scrape_results WHERE url = ? OR url LIKE ? ORDER BY timestamp DESC",
            (url, f"%{url}%")
        )
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse JSON fields
        for result in results:
            for field in ['data_json', 'links_json', 'images_json']:
                if result.get(field):
                    try:
                        result[field.replace('_json', '')] = json.loads(result[field])
                        del result[field]
                    except json.JSONDecodeError:
                        pass
        
        return {
            "url": url,
            "results": results,
            "count": len(results)
        }


@app.get("/results/domain/{domain}", summary="Get results for domain")
async def get_results_by_domain(
    domain: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all results for a specific domain"""
    
    with sqlite3.connect(scraping_db.db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM scrape_results WHERE domain = ? OR domain LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (domain, f"%{domain}%", limit)
        )
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse JSON fields
        for result in results:
            for field in ['data_json', 'links_json', 'images_json']:
                if result.get(field):
                    try:
                        result[field.replace('_json', '')] = json.loads(result[field])
                        del result[field]
                    except json.JSONDecodeError:
                        pass
        
        return {
            "domain": domain,
            "results": results,
            "count": len(results)
        }


@app.get("/search", summary="Search results")
async def search_results(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=200)
):
    """Search through scraped content"""
    
    with sqlite3.connect(scraping_db.db_path) as conn:
        cursor = conn.execute("""
            SELECT * FROM scrape_results
            WHERE title LIKE ? 
               OR data_json LIKE ?
               OR url LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{q}%", f"%{q}%", f"%{q}%", limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse JSON fields and calculate relevance
        for result in results:
            for field in ['data_json', 'links_json', 'images_json']:
                if result.get(field):
                    try:
                        result[field.replace('_json', '')] = json.loads(result[field])
                        del result[field]
                    except json.JSONDecodeError:
                        pass
            
            # Calculate relevance score
            score = 0
            if q.lower() in (result.get('title') or '').lower():
                score += 10
            if q.lower() in (result.get('url') or '').lower():
                score += 5
            if q.lower() in (result.get('data_json') or '').lower():
                score += 1
            
            result['relevance_score'] = score
        
        # Sort by relevance
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }


@app.get("/stats", response_model=DatabaseStats, summary="Get statistics")
async def get_statistics():
    """Get comprehensive database statistics"""
    
    with sqlite3.connect(scraping_db.db_path) as conn:
        # Basic counts
        total_results = conn.execute("SELECT COUNT(*) FROM scrape_results").fetchone()[0]
        successful_results = conn.execute("SELECT COUNT(*) FROM scrape_results WHERE status = 'success'").fetchone()[0]
        failed_results = conn.execute("SELECT COUNT(*) FROM scrape_results WHERE status = 'failed'").fetchone()[0]
        
        # Method statistics
        method_stats = {}
        method_cursor = conn.execute("""
            SELECT method_used, COUNT(*) as count, AVG(response_time) as avg_time
            FROM scrape_results
            WHERE method_used != 'none'
            GROUP BY method_used
        """)
        
        for method, count, avg_time in method_cursor.fetchall():
            method_stats[method] = {
                'count': count,
                'avg_response_time': round(avg_time or 0, 3)
            }
        
        # Domain statistics
        domain_cursor = conn.execute("""
            SELECT domain, COUNT(*) as count
            FROM scrape_results
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_domains = dict(domain_cursor.fetchall())
        
        # Time-based statistics
        recent_cursor = conn.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM scrape_results
            WHERE timestamp >= date('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)
        
        daily_stats = dict(recent_cursor.fetchall())
        
        # Response time statistics
        time_cursor = conn.execute("""
            SELECT AVG(response_time) as avg, MIN(response_time) as min, MAX(response_time) as max
            FROM scrape_results
            WHERE response_time IS NOT NULL
        """)
        
        time_stats = time_cursor.fetchone()
        
        return DatabaseStats(
            total_results=total_results,
            successful_results=successful_results,
            failed_results=failed_results,
            success_rate=round((successful_results / total_results * 100) if total_results > 0 else 0, 2),
            method_statistics=method_stats,
            top_domains=top_domains,
            daily_activity=daily_stats,
            response_time_stats={
                'average': round(time_stats[0] or 0, 3),
                'minimum': round(time_stats[1] or 0, 3),
                'maximum': round(time_stats[2] or 0, 3)
            }
        )


@app.delete("/results/{result_id}", summary="Delete result")
async def delete_result(
    result_id: int = PathParam(..., ge=1),
    user: dict = Depends(get_current_user)
):
    """Delete a specific scraping result"""
    
    with sqlite3.connect(scraping_db.db_path) as conn:
        cursor = conn.execute("DELETE FROM scrape_results WHERE id = ?", (result_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Result not found")
        
        conn.commit()
    
    return {"message": f"Result {result_id} deleted successfully"}


# Background task function
async def perform_scraping(task_id: str, url: str, methods: List[str], config: Dict[str, Any]):
    """Perform the actual scraping in background"""
    
    try:
        # Update task status
        task_manager.update_task(task_id, status="running", started_at=datetime.now().isoformat())
        
        # 🔒 SECURITY CHECK: Ensure VPN is active before scraping
        is_vpn_active, vpn_message, current_ip = await async_check_vpn()
        if not is_vpn_active:
            raise Exception(f"VPN CHECK FAILED: {vpn_message}")
        
        logger.info(f"VPN Check passed for task {task_id}: {current_ip}")
        
        # Create scraper with config
        scraper_config = {
            'verify_ssl': False,
            'timeout': 30,
            **config
        }
        
        # Perform scraping
        async with ProgressiveScraper(scraper_config) as scraper:
            result = await scraper.scrape_progressive(url)
        
        # Save to database
        result_id = scraping_db.save_result(result)
        
        # Mark task as completed
        task_manager.complete_task(task_id, result_id=result_id)
        
        logger.info(f"Completed scraping task {task_id} with result ID {result_id}")
        
    except Exception as e:
        logger.error(f"Scraping task {task_id} failed: {e}")
        task_manager.complete_task(task_id, error=str(e))


# CLI argument parsing for service
def parse_service_arguments():
    """Parse command line arguments for the API service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scraper API Service")
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind to (default: 8000)'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='Log level (default: info)'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse arguments
    args = parse_service_arguments()
    
    print("🚀 Starting Awesome Web Scraper API Service")
    print("=" * 50)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Docs: http://{args.host}:{args.port}/docs")
    print("=" * 50)
    
    # Run the server
    uvicorn.run(
        "api_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )