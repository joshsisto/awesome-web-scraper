#!/usr/bin/env python3
"""
Practical Examples for the Awesome Web Scraper
Real-world scraping scenarios with working code

Note: These examples use httpx for demonstration since the full framework
requires additional dependencies. The patterns shown here work the same
with the full orchestrator.
"""

import asyncio
import json
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import httpx
from urllib.parse import urljoin, urlparse


class PracticalExamples:
    def __init__(self):
        self.session = None
        self.results_dir = Path("example_results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            verify=False  # For demo purposes
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def save_json(self, data: Any, filename: str):
        """Save data to JSON file"""
        filepath = self.results_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Saved: {filepath}")
    
    def save_csv(self, data: List[Dict], filename: str):
        """Save data to CSV file"""
        if not data:
            return
        
        filepath = self.results_dir / filename
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"💾 Saved: {filepath}")


# Example 1: News Article Scraper
class NewsArticleScraper(PracticalExamples):
    async def scrape_news_site(self, base_url: str = "https://httpbin.org"):
        """
        Example: Scrape news articles
        In real use, replace with actual news site
        """
        print("📰 Example 1: News Article Scraping")
        print("=" * 50)
        
        # For demo, we'll simulate scraping news structure
        article_urls = [
            f"{base_url}/html",  # Simulates article page
            f"{base_url}/json",  # Simulates API endpoint
        ]
        
        articles = []
        
        for url in article_urls:
            try:
                print(f"\n📡 Scraping: {url}")
                response = await self.session.get(url)
                
                if response.status_code == 200:
                    # Simulate article extraction
                    article = {
                        "url": url,
                        "title": self._extract_title(response.text),
                        "content": self._extract_content(response.text),
                        "word_count": len(response.text.split()),
                        "scraped_at": datetime.now().isoformat(),
                        "response_time": response.elapsed.total_seconds()
                    }
                    articles.append(article)
                    
                    print(f"✅ Title: {article['title']}")
                    print(f"📊 Words: {article['word_count']}")
                
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
        
        # Save results
        self.save_json(articles, "news_articles.json")
        self.save_csv(articles, "news_articles.csv")
        
        print(f"\n📋 Summary: Scraped {len(articles)} articles")
        return articles
    
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML"""
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        return match.group(1).strip() if match else "No title"
    
    def _extract_content(self, html: str) -> str:
        """Extract main content from HTML"""
        # Remove scripts and styles
        content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract paragraphs
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
        clean_paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs]
        
        return " ".join(clean_paragraphs)


# Example 2: E-commerce Product Monitor
class ProductMonitor(PracticalExamples):
    async def monitor_product_prices(self):
        """
        Example: Monitor product prices
        Demonstrates tracking changes over time
        """
        print("🛒 Example 2: Product Price Monitoring")
        print("=" * 50)
        
        # Simulate product URLs (in real use, these would be actual product pages)
        products = [
            {
                "name": "Example Product 1",
                "url": "https://httpbin.org/json",
                "target_price": 100.00
            },
            {
                "name": "Example Product 2", 
                "url": "https://httpbin.org/get",
                "target_price": 50.00
            }
        ]
        
        monitoring_results = []
        
        for product in products:
            try:
                print(f"\n🔍 Monitoring: {product['name']}")
                response = await self.session.get(product['url'])
                
                if response.status_code == 200:
                    # Simulate price extraction
                    current_price = self._simulate_price_extraction()
                    
                    result = {
                        "product_name": product['name'],
                        "url": product['url'],
                        "current_price": current_price,
                        "target_price": product['target_price'],
                        "price_difference": current_price - product['target_price'],
                        "is_deal": current_price <= product['target_price'],
                        "timestamp": datetime.now().isoformat(),
                        "status": "available" if response.status_code == 200 else "unavailable"
                    }
                    
                    monitoring_results.append(result)
                    
                    # Alert logic
                    if result['is_deal']:
                        print(f"🎯 DEAL ALERT! {product['name']} is ${current_price} (target: ${product['target_price']})")
                    else:
                        print(f"💰 Price: ${current_price} (${result['price_difference']:.2f} above target)")
                        
            except Exception as e:
                print(f"❌ Error monitoring {product['name']}: {e}")
        
        # Save monitoring results
        self.save_json(monitoring_results, "price_monitoring.json")
        
        # Create alert summary
        deals = [r for r in monitoring_results if r['is_deal']]
        if deals:
            print(f"\n🎉 Found {len(deals)} deals!")
            for deal in deals:
                print(f"  - {deal['product_name']}: ${deal['current_price']}")
        
        return monitoring_results
    
    def _simulate_price_extraction(self) -> float:
        """Simulate price extraction (in real use, parse actual price from HTML)"""
        import random
        return round(random.uniform(45.00, 120.00), 2)


# Example 3: Social Media Content Aggregator
class SocialMediaAggregator(PracticalExamples):
    async def aggregate_social_content(self):
        """
        Example: Aggregate content from multiple social platforms
        Demonstrates handling different data formats
        """
        print("📱 Example 3: Social Media Content Aggregation")
        print("=" * 50)
        
        # Simulate different social media APIs
        platforms = [
            {"name": "Platform A", "url": "https://httpbin.org/json", "type": "json"},
            {"name": "Platform B", "url": "https://httpbin.org/html", "type": "html"},
            {"name": "Platform C", "url": "https://httpbin.org/xml", "type": "xml"}
        ]
        
        aggregated_content = []
        
        for platform in platforms:
            try:
                print(f"\n📡 Fetching from {platform['name']}")
                response = await self.session.get(platform['url'])
                
                if response.status_code == 200:
                    # Extract content based on platform type
                    content = await self._extract_social_content(
                        response.text, 
                        platform['type']
                    )
                    
                    for item in content:
                        item.update({
                            "platform": platform['name'],
                            "scraped_at": datetime.now().isoformat(),
                            "engagement_score": self._calculate_engagement_score(item)
                        })
                        aggregated_content.append(item)
                    
                    print(f"✅ Extracted {len(content)} posts from {platform['name']}")
                    
            except Exception as e:
                print(f"❌ Error fetching from {platform['name']}: {e}")
        
        # Sort by engagement score
        aggregated_content.sort(key=lambda x: x['engagement_score'], reverse=True)
        
        # Save results
        self.save_json(aggregated_content, "social_content.json")
        
        # Create trending topics report
        trending = self._analyze_trending_topics(aggregated_content)
        self.save_json(trending, "trending_topics.json")
        
        print(f"\n📊 Aggregated {len(aggregated_content)} posts across {len(platforms)} platforms")
        print(f"🔥 Found {len(trending)} trending topics")
        
        return aggregated_content
    
    async def _extract_social_content(self, content: str, content_type: str) -> List[Dict]:
        """Extract content based on format type"""
        posts = []
        
        if content_type == "json":
            try:
                data = json.loads(content)
                # Simulate extracting posts from JSON
                posts.append({
                    "post_id": "json_post_1",
                    "text": "This is a simulated social media post from JSON API",
                    "likes": 42,
                    "shares": 7,
                    "comments": 3
                })
            except json.JSONDecodeError:
                pass
                
        elif content_type == "html":
            # Simulate extracting from HTML
            posts.append({
                "post_id": "html_post_1", 
                "text": "This is a simulated post extracted from HTML",
                "likes": 28,
                "shares": 5,
                "comments": 12
            })
            
        elif content_type == "xml":
            # Simulate extracting from XML
            posts.append({
                "post_id": "xml_post_1",
                "text": "This is a simulated post from XML feed",
                "likes": 15,
                "shares": 2,
                "comments": 8
            })
        
        return posts
    
    def _calculate_engagement_score(self, post: Dict) -> float:
        """Calculate engagement score for ranking"""
        likes = post.get('likes', 0)
        shares = post.get('shares', 0) 
        comments = post.get('comments', 0)
        
        # Weighted engagement score
        return (likes * 1) + (shares * 3) + (comments * 2)
    
    def _analyze_trending_topics(self, posts: List[Dict]) -> List[Dict]:
        """Analyze trending topics from posts"""
        # Simulate topic extraction (in real use, use NLP)
        common_words = ['example', 'demo', 'test', 'social', 'media', 'content']
        
        trending = []
        for word in common_words:
            mentions = sum(1 for post in posts if word.lower() in post.get('text', '').lower())
            if mentions > 0:
                trending.append({
                    "topic": word,
                    "mentions": mentions,
                    "trend_score": mentions * 10
                })
        
        return sorted(trending, key=lambda x: x['trend_score'], reverse=True)


# Example 4: Research Data Collector
class ResearchDataCollector(PracticalExamples):
    async def collect_research_data(self):
        """
        Example: Collect data for research purposes
        Demonstrates systematic data collection and analysis
        """
        print("🔬 Example 4: Research Data Collection")
        print("=" * 50)
        
        # Simulate research data sources
        data_sources = [
            {"name": "Academic Source 1", "url": "https://httpbin.org/json"},
            {"name": "Government Data", "url": "https://httpbin.org/xml"}, 
            {"name": "Statistics Portal", "url": "https://httpbin.org/html"}
        ]
        
        research_data = []
        
        for source in data_sources:
            try:
                print(f"\n📊 Collecting from {source['name']}")
                response = await self.session.get(source['url'])
                
                if response.status_code == 200:
                    # Simulate data extraction
                    data_points = self._extract_research_data(response.text, source['name'])
                    research_data.extend(data_points)
                    
                    print(f"✅ Collected {len(data_points)} data points")
                    
            except Exception as e:
                print(f"❌ Error collecting from {source['name']}: {e}")
        
        # Analyze collected data
        analysis = self._analyze_research_data(research_data)
        
        # Save raw data and analysis
        self.save_json(research_data, "research_raw_data.json")
        self.save_json(analysis, "research_analysis.json")
        self.save_csv(research_data, "research_data.csv")
        
        print(f"\n📈 Research Summary:")
        print(f"  - Total data points: {len(research_data)}")
        print(f"  - Data sources: {len(data_sources)}")
        print(f"  - Analysis metrics: {len(analysis)}")
        
        return research_data, analysis
    
    def _extract_research_data(self, content: str, source_name: str) -> List[Dict]:
        """Extract research data points"""
        import random
        
        # Simulate extracting numerical data
        data_points = []
        for i in range(random.randint(5, 15)):
            data_points.append({
                "source": source_name,
                "metric": f"metric_{i+1}",
                "value": round(random.uniform(10, 100), 2),
                "unit": "percentage",
                "category": random.choice(["category_a", "category_b", "category_c"]),
                "collected_at": datetime.now().isoformat()
            })
        
        return data_points
    
    def _analyze_research_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform analysis on collected data"""
        if not data:
            return {}
        
        # Basic statistical analysis
        values = [d['value'] for d in data]
        
        analysis = {
            "total_records": len(data),
            "statistics": {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values)
            },
            "category_breakdown": {},
            "source_breakdown": {}
        }
        
        # Category analysis
        categories = {}
        for item in data:
            cat = item['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item['value'])
        
        for cat, vals in categories.items():
            analysis["category_breakdown"][cat] = {
                "count": len(vals),
                "average": sum(vals) / len(vals)
            }
        
        # Source analysis  
        sources = {}
        for item in data:
            src = item['source']
            if src not in sources:
                sources[src] = 0
            sources[src] += 1
        
        analysis["source_breakdown"] = sources
        
        return analysis


# Example 5: Website Health Monitor
class WebsiteHealthMonitor(PracticalExamples):
    async def monitor_website_health(self):
        """
        Example: Monitor website health and performance
        Demonstrates monitoring multiple metrics
        """
        print("🏥 Example 5: Website Health Monitoring")
        print("=" * 50)
        
        # Websites to monitor
        websites = [
            "https://httpbin.org/get",
            "https://httpbin.org/delay/2",
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404"  # This will demonstrate error handling
        ]
        
        health_reports = []
        
        for website in websites:
            try:
                print(f"\n🔍 Checking {website}")
                
                start_time = datetime.now()
                response = await self.session.get(website)
                end_time = datetime.now()
                
                response_time = (end_time - start_time).total_seconds()
                
                # Analyze response
                health_report = {
                    "url": website,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "timestamp": start_time.isoformat(),
                    "content_length": len(response.text),
                    "health_score": self._calculate_health_score(response.status_code, response_time),
                    "issues": self._identify_issues(response.status_code, response_time),
                    "recommendations": self._generate_recommendations(response.status_code, response_time)
                }
                
                health_reports.append(health_report)
                
                # Display status
                status_emoji = "✅" if response.status_code == 200 else "❌"
                print(f"{status_emoji} Status: {response.status_code} | Time: {response_time:.2f}s | Score: {health_report['health_score']}/100")
                
                if health_report['issues']:
                    print(f"⚠️  Issues: {', '.join(health_report['issues'])}")
                    
            except Exception as e:
                print(f"❌ Error checking {website}: {e}")
                health_reports.append({
                    "url": website,
                    "status_code": None,
                    "response_time": None,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "health_score": 0,
                    "issues": ["Connection failed"],
                    "recommendations": ["Check network connectivity", "Verify URL is correct"]
                })
        
        # Generate summary report
        summary = self._generate_health_summary(health_reports)
        
        # Save reports
        self.save_json(health_reports, "website_health_reports.json")
        self.save_json(summary, "health_summary.json")
        
        print(f"\n📊 Health Monitoring Summary:")
        print(f"  - Websites checked: {len(websites)}")
        print(f"  - Healthy sites: {summary['healthy_count']}")
        print(f"  - Issues detected: {summary['issues_count']}")
        print(f"  - Average response time: {summary['avg_response_time']:.2f}s")
        
        return health_reports, summary
    
    def _calculate_health_score(self, status_code: int, response_time: float) -> int:
        """Calculate health score (0-100)"""
        score = 100
        
        # Penalize based on status code
        if status_code != 200:
            score -= 50
        
        # Penalize based on response time
        if response_time > 3.0:
            score -= 30
        elif response_time > 1.0:
            score -= 15
        elif response_time > 0.5:
            score -= 5
        
        return max(0, score)
    
    def _identify_issues(self, status_code: int, response_time: float) -> List[str]:
        """Identify potential issues"""
        issues = []
        
        if status_code != 200:
            issues.append(f"HTTP {status_code} error")
        
        if response_time > 3.0:
            issues.append("Very slow response time")
        elif response_time > 1.0:
            issues.append("Slow response time")
        
        return issues
    
    def _generate_recommendations(self, status_code: int, response_time: float) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if status_code != 200:
            recommendations.append("Check server configuration and error logs")
        
        if response_time > 1.0:
            recommendations.append("Optimize server performance")
            recommendations.append("Consider CDN implementation")
            recommendations.append("Review database query performance")
        
        return recommendations
    
    def _generate_health_summary(self, reports: List[Dict]) -> Dict[str, Any]:
        """Generate overall health summary"""
        healthy_count = sum(1 for r in reports if r.get('health_score', 0) > 80)
        issues_count = sum(len(r.get('issues', [])) for r in reports)
        
        response_times = [r['response_time'] for r in reports if r.get('response_time')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_sites": len(reports),
            "healthy_count": healthy_count,
            "issues_count": issues_count,
            "avg_response_time": avg_response_time,
            "health_percentage": (healthy_count / len(reports)) * 100 if reports else 0,
            "generated_at": datetime.now().isoformat()
        }


# Main demonstration function
async def run_all_examples():
    """Run all practical examples"""
    
    print("🚀 Awesome Web Scraper - Practical Examples")
    print("=" * 60)
    print("These examples demonstrate real-world scraping scenarios")
    print("Replace URLs with actual targets for production use\n")
    
    results = {}
    
    # Example 1: News Articles
    async with NewsArticleScraper() as news_scraper:
        results['news'] = await news_scraper.scrape_news_site()
    
    print("\n" + "="*60)
    
    # Example 2: Product Monitoring  
    async with ProductMonitor() as product_monitor:
        results['products'] = await product_monitor.monitor_product_prices()
    
    print("\n" + "="*60)
    
    # Example 3: Social Media
    async with SocialMediaAggregator() as social_aggregator:
        results['social'] = await social_aggregator.aggregate_social_content()
    
    print("\n" + "="*60)
    
    # Example 4: Research Data
    async with ResearchDataCollector() as research_collector:
        results['research'] = await research_collector.collect_research_data()
    
    print("\n" + "="*60)
    
    # Example 5: Website Health
    async with WebsiteHealthMonitor() as health_monitor:
        results['health'] = await health_monitor.monitor_website_health()
    
    print("\n" + "="*60)
    print("🎉 All examples completed!")
    print("📂 Check the 'example_results' directory for output files")
    print("\n💡 Tip: Modify these examples to work with your target websites")
    print("🔧 Use the full orchestrator for production scraping")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_examples())