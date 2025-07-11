#!/usr/bin/env python3
"""
Data Retriever - Access and analyze scraped data from the database

Usage:
    python data_retriever.py --list                    # List all scraped URLs
    python data_retriever.py --url joshsisto.com       # Get data for specific URL
    python data_retriever.py --domain example.com      # Get all data for domain
    python data_retriever.py --recent 24               # Get data from last 24 hours
    python data_retriever.py --export csv              # Export all data to CSV
    python data_retriever.py --stats                   # Show database statistics
    python data_retriever.py --search "keyword"        # Search in scraped content

Features:
    - Query scraped data by URL, domain, or time
    - Export to multiple formats (JSON, CSV, Excel)
    - Statistics and analytics
    - Full-text search capabilities
    - Data visualization
    - Clean and filter results
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import csv
from urllib.parse import urlparse
import re


class DataRetriever:
    """Database interface for retrieving scraped data"""
    
    def __init__(self, db_path: str = "scraped_data.db"):
        self.db_path = db_path
        if not Path(db_path).exists():
            print(f"❌ Database not found: {db_path}")
            print("💡 Run master_scraper.py first to create data")
            sys.exit(1)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def list_all_urls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all scraped URLs"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, url, domain, method_used, status, timestamp, title
                FROM scrape_results
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_by_url(self, url: str) -> List[Dict[str, Any]]:
        """Get all results for a specific URL"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM scrape_results
                WHERE url = ? OR url LIKE ?
                ORDER BY timestamp DESC
            """, (url, f"%{url}%"))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for result in results:
                for field in ['data_json', 'links_json', 'images_json']:
                    if result.get(field):
                        try:
                            result[field.replace('_json', '')] = json.loads(result[field])
                        except json.JSONDecodeError:
                            pass
            
            return results
    
    def get_by_domain(self, domain: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all results for a specific domain"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM scrape_results
                WHERE domain = ? OR domain LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (domain, f"%{domain}%", limit))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for result in results:
                for field in ['data_json', 'links_json', 'images_json']:
                    if result.get(field):
                        try:
                            result[field.replace('_json', '')] = json.loads(result[field])
                        except json.JSONDecodeError:
                            pass
            
            return results
    
    def get_recent(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent scraping results"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM scrape_results
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_str,))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for result in results:
                for field in ['data_json', 'links_json', 'images_json']:
                    if result.get(field):
                        try:
                            result[field.replace('_json', '')] = json.loads(result[field])
                        except json.JSONDecodeError:
                            pass
            
            return results
    
    def search_content(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for content in scraped data"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM scrape_results
                WHERE title LIKE ? 
                   OR data_json LIKE ?
                   OR url LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", limit))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Parse JSON fields and highlight matches
            for result in results:
                for field in ['data_json', 'links_json', 'images_json']:
                    if result.get(field):
                        try:
                            result[field.replace('_json', '')] = json.loads(result[field])
                        except json.JSONDecodeError:
                            pass
                
                # Add search relevance score
                score = 0
                if search_term.lower() in (result.get('title') or '').lower():
                    score += 10
                if search_term.lower() in (result.get('url') or '').lower():
                    score += 5
                if search_term.lower() in (result.get('data_json') or '').lower():
                    score += 1
                
                result['relevance_score'] = score
            
            # Sort by relevance
            results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
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
            
            return {
                'total_results': total_results,
                'successful_results': successful_results,
                'failed_results': failed_results,
                'success_rate': round((successful_results / total_results * 100) if total_results > 0 else 0, 2),
                'method_statistics': method_stats,
                'top_domains': top_domains,
                'daily_activity': daily_stats,
                'response_time_stats': {
                    'average': round(time_stats[0] or 0, 3),
                    'minimum': round(time_stats[1] or 0, 3),
                    'maximum': round(time_stats[2] or 0, 3)
                }
            }
    
    def export_to_csv(self, filename: str, data: List[Dict[str, Any]] = None):
        """Export data to CSV file"""
        if data is None:
            data = self.list_all_urls(limit=10000)  # Export all data
        
        if not data:
            print("❌ No data to export")
            return
        
        # Flatten nested JSON fields
        flattened_data = []
        for item in data:
            flat_item = {}
            for key, value in item.items():
                if key.endswith('_json') and isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict):
                            for sub_key, sub_value in parsed.items():
                                flat_item[f"{key.replace('_json', '')}_{sub_key}"] = str(sub_value)
                        else:
                            flat_item[key.replace('_json', '')] = str(parsed)
                    except json.JSONDecodeError:
                        flat_item[key] = str(value)
                elif isinstance(value, (dict, list)):
                    flat_item[key] = json.dumps(value)
                else:
                    flat_item[key] = value
            
            flattened_data.append(flat_item)
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if flattened_data:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)
        
        print(f"💾 Exported {len(flattened_data)} records to {filename}")
    
    def export_to_json(self, filename: str, data: List[Dict[str, Any]] = None):
        """Export data to JSON file"""
        if data is None:
            data = self.list_all_urls(limit=10000)  # Export all data
        
        # Parse JSON fields
        for item in data:
            for field in ['data_json', 'links_json', 'images_json']:
                if item.get(field) and isinstance(item[field], str):
                    try:
                        item[field.replace('_json', '')] = json.loads(item[field])
                        del item[field]  # Remove the JSON string version
                    except json.JSONDecodeError:
                        pass
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"💾 Exported {len(data)} records to {filename}")
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Remove data older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_time.isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM scrape_results
                WHERE timestamp < ?
            """, (cutoff_str,))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        return deleted_count


class DataFormatter:
    """Format data for display"""
    
    @staticmethod
    def format_url_list(data: List[Dict[str, Any]]) -> str:
        """Format URL list for display"""
        if not data:
            return "No data found."
        
        output = []
        output.append("📋 Scraped URLs")
        output.append("=" * 80)
        output.append(f"{'ID':<5} {'Status':<8} {'Method':<10} {'URL':<40} {'Title':<20}")
        output.append("-" * 80)
        
        for item in data:
            status_emoji = "✅" if item['status'] == 'success' else "❌"
            title = (item.get('title') or 'No title')[:18] + "..." if len(item.get('title') or '') > 18 else (item.get('title') or 'No title')
            url = item['url'][:38] + "..." if len(item['url']) > 38 else item['url']
            
            output.append(f"{item['id']:<5} {status_emoji:<8} {item['method_used']:<10} {url:<40} {title:<20}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_detailed_result(data: Dict[str, Any]) -> str:
        """Format detailed result for display"""
        output = []
        output.append(f"🔍 Detailed Result for {data['url']}")
        output.append("=" * 80)
        
        # Basic info
        status_emoji = "✅" if data['status'] == 'success' else "❌"
        method_emoji = {"scrapy": "🕷️", "pydoll": "⚡", "playwright": "🎭"}.get(data['method_used'], "🔧")
        
        output.append(f"{status_emoji} Status: {data['status'].upper()}")
        output.append(f"{method_emoji} Method: {data['method_used'].upper()}")
        output.append(f"🌐 HTTP Status: {data.get('status_code', 'N/A')}")
        output.append(f"⏱️  Response Time: {data.get('response_time', 0):.3f}s")
        output.append(f"🕒 Timestamp: {data['timestamp']}")
        
        if data.get('title'):
            output.append(f"📄 Title: {data['title']}")
        
        if data.get('content_length'):
            output.append(f"📏 Content Length: {data['content_length']:,} characters")
        
        if data.get('links_count') is not None:
            output.append(f"🔗 Links Found: {data['links_count']}")
        
        if data.get('images_count') is not None:
            output.append(f"🖼️  Images Found: {data['images_count']}")
        
        # Extracted data
        if data.get('data'):
            output.append("\n📊 Extracted Data:")
            output.append("-" * 40)
            extracted_data = data['data']
            
            for key, value in extracted_data.items():
                if isinstance(value, list):
                    output.append(f"  {key}: {len(value)} items")
                    if value and len(value) <= 5:
                        for item in value:
                            output.append(f"    - {str(item)[:60]}...")
                elif isinstance(value, str) and len(value) > 100:
                    output.append(f"  {key}: {value[:100]}...")
                else:
                    output.append(f"  {key}: {value}")
        
        # Links (sample)
        if data.get('links') and len(data['links']) > 0:
            output.append(f"\n🔗 Sample Links (showing first 5 of {len(data['links'])}):")
            output.append("-" * 40)
            for link in data['links'][:5]:
                output.append(f"  - {link}")
        
        # Images (sample)
        if data.get('images') and len(data['images']) > 0:
            output.append(f"\n🖼️  Sample Images (showing first 5 of {len(data['images'])}):")
            output.append("-" * 40)
            for img in data['images'][:5]:
                output.append(f"  - {img}")
        
        if data.get('error_message'):
            output.append(f"\n❌ Error: {data['error_message']}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_statistics(stats: Dict[str, Any]) -> str:
        """Format statistics for display"""
        output = []
        output.append("📊 Database Statistics")
        output.append("=" * 60)
        
        # Overview
        output.append(f"📈 Total Results: {stats['total_results']}")
        output.append(f"✅ Successful: {stats['successful_results']}")
        output.append(f"❌ Failed: {stats['failed_results']}")
        output.append(f"📊 Success Rate: {stats['success_rate']}%")
        
        # Method statistics
        if stats['method_statistics']:
            output.append("\n🔧 Method Performance:")
            output.append("-" * 30)
            for method, data in stats['method_statistics'].items():
                emoji = {"scrapy": "🕷️", "pydoll": "⚡", "playwright": "🎭"}.get(method, "🔧")
                output.append(f"  {emoji} {method.capitalize()}: {data['count']} uses, {data['avg_response_time']}s avg")
        
        # Response time stats
        time_stats = stats['response_time_stats']
        output.append(f"\n⏱️  Response Times:")
        output.append("-" * 20)
        output.append(f"  Average: {time_stats['average']}s")
        output.append(f"  Fastest: {time_stats['minimum']}s")
        output.append(f"  Slowest: {time_stats['maximum']}s")
        
        # Top domains
        if stats['top_domains']:
            output.append("\n🌐 Top Domains:")
            output.append("-" * 20)
            for domain, count in list(stats['top_domains'].items())[:5]:
                output.append(f"  {domain}: {count} results")
        
        # Daily activity
        if stats['daily_activity']:
            output.append("\n📅 Recent Activity:")
            output.append("-" * 20)
            for date, count in list(stats['daily_activity'].items())[:7]:
                output.append(f"  {date}: {count} scrapes")
        
        return "\n".join(output)
    
    @staticmethod
    def format_search_results(results: List[Dict[str, Any]], search_term: str) -> str:
        """Format search results for display"""
        if not results:
            return f"❌ No results found for '{search_term}'"
        
        output = []
        output.append(f"🔍 Search Results for '{search_term}'")
        output.append("=" * 60)
        output.append(f"Found {len(results)} matching results\n")
        
        for i, result in enumerate(results[:10], 1):
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            relevance = result.get('relevance_score', 0)
            
            output.append(f"{i}. {status_emoji} {result['url']}")
            output.append(f"   📊 Relevance: {relevance} | Method: {result['method_used']} | {result['timestamp']}")
            
            if result.get('title'):
                # Highlight search term in title
                highlighted_title = result['title'].replace(
                    search_term, f"**{search_term}**"
                )
                output.append(f"   📄 {highlighted_title}")
            
            output.append("")
        
        if len(results) > 10:
            output.append(f"... and {len(results) - 10} more results")
        
        return "\n".join(output)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Data Retriever - Access and analyze scraped data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python data_retriever.py --list
    python data_retriever.py --url joshsisto.com
    python data_retriever.py --domain example.com --export json
    python data_retriever.py --recent 48 --format table
    python data_retriever.py --search "contact" --limit 20
    python data_retriever.py --stats
    python data_retriever.py --cleanup 30
        """
    )
    
    # Query options (mutually exclusive)
    query_group = parser.add_mutually_exclusive_group(required=True)
    
    query_group.add_argument(
        '--list',
        action='store_true',
        help='List all scraped URLs'
    )
    
    query_group.add_argument(
        '--url',
        type=str,
        help='Get data for specific URL'
    )
    
    query_group.add_argument(
        '--domain',
        type=str,
        help='Get all data for specific domain'
    )
    
    query_group.add_argument(
        '--recent',
        type=int,
        metavar='HOURS',
        help='Get data from last N hours'
    )
    
    query_group.add_argument(
        '--search',
        type=str,
        help='Search for keyword in scraped content'
    )
    
    query_group.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    
    query_group.add_argument(
        '--cleanup',
        type=int,
        metavar='DAYS',
        help='Remove data older than N days'
    )
    
    # Output options
    parser.add_argument(
        '--format',
        choices=['table', 'json', 'summary'],
        default='summary',
        help='Output format (default: summary)'
    )
    
    parser.add_argument(
        '--export',
        choices=['csv', 'json'],
        help='Export results to file format'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output filename (auto-generated if not provided)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Limit number of results (default: 50)'
    )
    
    parser.add_argument(
        '--db',
        type=str,
        default='scraped_data.db',
        help='Database file path (default: scraped_data.db)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    print("📊 Data Retriever")
    print("=" * 40)
    
    # Initialize data retriever
    retriever = DataRetriever(args.db)
    formatter = DataFormatter()
    
    try:
        # Execute query based on arguments
        if args.list:
            data = retriever.list_all_urls(limit=args.limit)
            if args.format == 'json':
                output = json.dumps(data, indent=2, default=str)
            else:
                output = formatter.format_url_list(data)
            
        elif args.url:
            data = retriever.get_by_url(args.url)
            if not data:
                print(f"❌ No data found for URL: {args.url}")
                return
            
            if args.format == 'json':
                output = json.dumps(data, indent=2, default=str)
            else:
                # Show most recent result in detail
                output = formatter.format_detailed_result(data[0])
                if len(data) > 1:
                    output += f"\n\n📝 Note: Found {len(data)} total results for this URL"
            
        elif args.domain:
            data = retriever.get_by_domain(args.domain, limit=args.limit)
            if not data:
                print(f"❌ No data found for domain: {args.domain}")
                return
            
            if args.format == 'json':
                output = json.dumps(data, indent=2, default=str)
            else:
                output = formatter.format_url_list(data)
            
        elif args.recent:
            data = retriever.get_recent(hours=args.recent)
            if not data:
                print(f"❌ No data found from last {args.recent} hours")
                return
            
            if args.format == 'json':
                output = json.dumps(data, indent=2, default=str)
            else:
                output = formatter.format_url_list(data)
            
        elif args.search:
            data = retriever.search_content(args.search, limit=args.limit)
            if not data:
                print(f"❌ No results found for search term: {args.search}")
                return
            
            if args.format == 'json':
                output = json.dumps(data, indent=2, default=str)
            else:
                output = formatter.format_search_results(data, args.search)
            
        elif args.stats:
            stats = retriever.get_statistics()
            output = formatter.format_statistics(stats)
            data = [stats]  # For export purposes
            
        elif args.cleanup:
            deleted_count = retriever.cleanup_old_data(days=args.cleanup)
            print(f"🗑️  Cleaned up {deleted_count} records older than {args.cleanup} days")
            return
        
        # Display output
        print(output)
        
        # Export if requested
        if args.export and 'data' in locals():
            if args.output:
                filename = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"scraped_data_export_{timestamp}.{args.export}"
            
            if args.export == 'csv':
                retriever.export_to_csv(filename, data)
            elif args.export == 'json':
                retriever.export_to_json(filename, data)
    
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()