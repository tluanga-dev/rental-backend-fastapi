#!/usr/bin/env python3
"""
Comprehensive Performance Analysis for Rental Optimization Endpoint
This test deeply analyzes why the new rental creation takes a long time.
"""

import asyncio
import time
import json
import statistics
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import httpx
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/transactions/new-rental-optimized"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/fastapi_db")


class PerformanceProfiler:
    """Detailed performance profiler for analyzing execution times."""
    
    def __init__(self):
        self.timings = {}
        self.start_times = {}
        
    def start_timer(self, name: str):
        """Start timing a specific operation."""
        self.start_times[name] = time.perf_counter()
        
    def end_timer(self, name: str) -> float:
        """End timing and record the duration."""
        if name not in self.start_times:
            return 0.0
        duration = time.perf_counter() - self.start_times[name]
        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(duration)
        return duration
    
    def get_report(self) -> Dict[str, Any]:
        """Generate performance report with statistics."""
        report = {}
        for name, times in self.timings.items():
            if times:
                report[name] = {
                    "count": len(times),
                    "total": sum(times),
                    "average": statistics.mean(times),
                    "min": min(times),
                    "max": max(times),
                    "median": statistics.median(times),
                    "std_dev": statistics.stdev(times) if len(times) > 1 else 0
                }
        return report


class DatabaseProfiler:
    """Profile database operations and queries."""
    
    def __init__(self):
        self.query_log = []
        self.connection_times = []
        
    async def profile_database_connection(self):
        """Test database connection performance."""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text
            
            engine = create_async_engine(DATABASE_URL)
            
            # Test connection time
            start = time.perf_counter()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            connection_time = time.perf_counter() - start
            self.connection_times.append(connection_time)
            
            # Get database statistics
            async with engine.begin() as conn:
                # Check for slow queries
                result = await conn.execute(text("""
                    SELECT query, calls, mean_exec_time, total_exec_time
                    FROM pg_stat_statements 
                    WHERE query LIKE '%transaction%' OR query LIKE '%rental%'
                    ORDER BY mean_exec_time DESC
                    LIMIT 10
                """))
                slow_queries = result.fetchall()
                
            await engine.dispose()
            
            return {
                "connection_time": connection_time,
                "slow_queries": [
                    {
                        "query": row[0][:100],
                        "calls": row[1],
                        "mean_time": row[2],
                        "total_time": row[3]
                    } for row in slow_queries
                ] if slow_queries else []
            }
        except Exception as e:
            return {"error": str(e)}


class RentalEndpointAnalyzer:
    """Comprehensive analyzer for the rental optimization endpoint."""
    
    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.db_profiler = DatabaseProfiler()
        self.test_results = []
        
    def generate_test_data(self, num_items: int = 1) -> Dict[str, Any]:
        """Generate test rental request data."""
        base_date = datetime.now().date()
        items = []
        
        for i in range(num_items):
            items.append({
                "item_id": f"550e8400-e29b-41d4-a716-44665544000{i+1}",
                "quantity": 1,
                "rental_period_value": 7,
                "rental_start_date": (base_date + timedelta(days=1)).isoformat(),
                "rental_end_date": (base_date + timedelta(days=8)).isoformat(),
                "tax_rate": "10.00",
                "discount_amount": "0.00",
                "notes": f"Test item {i+1}"
            })
        
        return {
            "customer_id": "550e8400-e29b-41d4-a716-446655440001",
            "location_id": "550e8400-e29b-41d4-a716-446655440002",
            "transaction_date": base_date.isoformat(),
            "payment_method": "cash",
            "deposit_amount": "100.00",
            "delivery_required": False,
            "pickup_required": False,
            "notes": "Performance test rental",
            "items": items
        }
    
    async def analyze_endpoint_internals(self):
        """Analyze the internal implementation of the endpoint."""
        print("\n🔬 ANALYZING ENDPOINT IMPLEMENTATION")
        print("=" * 50)
        
        # Read and analyze the service implementation
        with open('app/modules/transactions/service.py', 'r') as f:
            service_content = f.read()
        
        # Count database operations
        import re
        
        # Find all database query patterns
        query_patterns = {
            "select": len(re.findall(r'select\(|\.execute\(.*SELECT', service_content, re.IGNORECASE)),
            "insert": len(re.findall(r'\.add\(|\.add_all\(|INSERT', service_content, re.IGNORECASE)),
            "update": len(re.findall(r'UPDATE|\.merge\(', service_content, re.IGNORECASE)),
            "flush": len(re.findall(r'\.flush\(', service_content)),
            "commit": len(re.findall(r'\.commit\(', service_content)),
            "begin": len(re.findall(r'\.begin\(', service_content))
        }
        
        print("📊 Database Operation Counts in Service:")
        for op, count in query_patterns.items():
            print(f"  - {op.upper()}: {count}")
        
        # Analyze the optimized method
        optimized_method_start = service_content.find("async def create_new_rental_optimized")
        if optimized_method_start != -1:
            method_lines = service_content[optimized_method_start:].split('\n')[:150]
            
            print("\n📋 Key Operations in create_new_rental_optimized:")
            operations = []
            for i, line in enumerate(method_lines):
                if any(keyword in line for keyword in ['await', 'select(', '.execute(', '.add(', '.add_all(', 'flush(', 'begin(']):
                    operations.append((i, line.strip()))
            
            for line_num, operation in operations[:10]:  # Show first 10 operations
                print(f"  Line +{line_num}: {operation[:80]}...")
        
        return query_patterns
    
    async def test_endpoint_performance(self, num_runs: int = 5, item_counts: List[int] = None):
        """Test endpoint performance with various scenarios."""
        if item_counts is None:
            item_counts = [1, 5, 10, 20]
        
        print("\n🚀 TESTING ENDPOINT PERFORMANCE")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for item_count in item_counts:
                print(f"\n📦 Testing with {item_count} items")
                print("-" * 40)
                
                scenario_results = []
                
                for run in range(num_runs):
                    test_data = self.generate_test_data(item_count)
                    
                    # Profile the entire request
                    self.profiler.start_timer(f"request_{item_count}_items")
                    
                    try:
                        # Measure request phases
                        self.profiler.start_timer("serialization")
                        json_data = json.dumps(test_data)
                        serialization_time = self.profiler.end_timer("serialization")
                        
                        self.profiler.start_timer("network_request")
                        start_time = time.perf_counter()
                        
                        response = await client.post(
                            f"{BASE_URL}{ENDPOINT}",
                            content=json_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        network_time = self.profiler.end_timer("network_request")
                        total_time = self.profiler.end_timer(f"request_{item_count}_items")
                        
                        # Analyze response
                        result = {
                            "run": run + 1,
                            "item_count": item_count,
                            "status_code": response.status_code,
                            "total_time": total_time,
                            "network_time": network_time,
                            "serialization_time": serialization_time,
                            "server_time": total_time - serialization_time,
                            "response_size": len(response.content)
                        }
                        
                        if response.status_code == 200 or response.status_code == 201:
                            result["success"] = True
                            result["response_data"] = response.json()
                        else:
                            result["success"] = False
                            result["error"] = response.text
                            
                        scenario_results.append(result)
                        
                        print(f"  Run {run + 1}: {total_time:.3f}s (Status: {response.status_code})")
                        
                    except httpx.TimeoutException:
                        print(f"  Run {run + 1}: TIMEOUT after 60s")
                        scenario_results.append({
                            "run": run + 1,
                            "item_count": item_count,
                            "success": False,
                            "error": "Request timeout after 60 seconds",
                            "total_time": 60.0
                        })
                    except Exception as e:
                        print(f"  Run {run + 1}: ERROR - {str(e)}")
                        scenario_results.append({
                            "run": run + 1,
                            "item_count": item_count,
                            "success": False,
                            "error": str(e),
                            "total_time": 0
                        })
                    
                    await asyncio.sleep(0.5)  # Delay between requests
                
                # Analyze scenario results
                successful_runs = [r for r in scenario_results if r.get("success")]
                if successful_runs:
                    avg_time = statistics.mean([r["total_time"] for r in successful_runs])
                    print(f"\n  ✅ Success Rate: {len(successful_runs)}/{num_runs}")
                    print(f"  ⏱️  Average Time: {avg_time:.3f}s")
                    print(f"  📊 Time per Item: {avg_time/item_count:.3f}s")
                else:
                    print(f"\n  ❌ All runs failed for {item_count} items")
                
                self.test_results.extend(scenario_results)
    
    async def analyze_bottlenecks(self):
        """Analyze performance bottlenecks."""
        print("\n🔍 BOTTLENECK ANALYSIS")
        print("=" * 50)
        
        # Get performance report
        perf_report = self.profiler.get_report()
        
        print("\n📊 Performance Breakdown:")
        for operation, stats in perf_report.items():
            print(f"\n{operation}:")
            print(f"  Count: {stats['count']}")
            print(f"  Total: {stats['total']:.3f}s")
            print(f"  Average: {stats['average']:.3f}s")
            print(f"  Min/Max: {stats['min']:.3f}s / {stats['max']:.3f}s")
        
        # Analyze scaling behavior
        print("\n📈 Scaling Analysis:")
        item_results = {}
        for result in self.test_results:
            if result.get("success"):
                item_count = result["item_count"]
                if item_count not in item_results:
                    item_results[item_count] = []
                item_results[item_count].append(result["total_time"])
        
        if len(item_results) > 1:
            sorted_counts = sorted(item_results.keys())
            print("Item Count | Avg Time | Time/Item | Scaling Factor")
            print("-" * 50)
            
            base_time = None
            for count in sorted_counts:
                avg_time = statistics.mean(item_results[count])
                time_per_item = avg_time / count
                
                if base_time is None:
                    base_time = avg_time
                    scaling_factor = 1.0
                else:
                    scaling_factor = avg_time / base_time
                
                print(f"{count:10} | {avg_time:8.3f}s | {time_per_item:9.3f}s | {scaling_factor:6.2f}x")
        
        # Identify specific bottlenecks
        print("\n⚠️  IDENTIFIED BOTTLENECKS:")
        bottlenecks = []
        
        # Check for linear scaling (bad)
        if len(item_results) > 1:
            counts = sorted(item_results.keys())
            times = [statistics.mean(item_results[c]) for c in counts]
            
            # Simple linear regression to check scaling
            if len(counts) > 2:
                # Calculate slope
                n = len(counts)
                sum_x = sum(counts)
                sum_y = sum(times)
                sum_xy = sum(c * t for c, t in zip(counts, times))
                sum_x2 = sum(c * c for c in counts)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                
                if slope > 0.5:  # More than 0.5 seconds per item
                    bottlenecks.append(f"Linear scaling detected: {slope:.3f}s per item - indicates N+1 query problem")
        
        # Check for slow operations
        for operation, stats in perf_report.items():
            if stats["average"] > 1.0:
                bottlenecks.append(f"{operation}: Average {stats['average']:.3f}s is too slow")
        
        # Check success rate
        total_runs = len(self.test_results)
        failed_runs = len([r for r in self.test_results if not r.get("success")])
        if failed_runs > 0:
            failure_rate = (failed_runs / total_runs) * 100
            bottlenecks.append(f"High failure rate: {failure_rate:.1f}% ({failed_runs}/{total_runs} runs failed)")
        
        if bottlenecks:
            for i, bottleneck in enumerate(bottlenecks, 1):
                print(f"  {i}. {bottleneck}")
        else:
            print("  ✅ No major bottlenecks identified")
        
        return bottlenecks
    
    def generate_detailed_report(self):
        """Generate comprehensive performance report."""
        print("\n📑 DETAILED PERFORMANCE REPORT")
        print("=" * 50)
        
        # Summary statistics
        successful_results = [r for r in self.test_results if r.get("success")]
        failed_results = [r for r in self.test_results if not r.get("success")]
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Total Runs: {len(self.test_results)}")
        print(f"  Successful: {len(successful_results)}")
        print(f"  Failed: {len(failed_results)}")
        
        if successful_results:
            all_times = [r["total_time"] for r in successful_results]
            print(f"\n⏱️  Response Time Statistics:")
            print(f"  Average: {statistics.mean(all_times):.3f}s")
            print(f"  Median: {statistics.median(all_times):.3f}s")
            print(f"  Min: {min(all_times):.3f}s")
            print(f"  Max: {max(all_times):.3f}s")
            print(f"  Std Dev: {statistics.stdev(all_times):.3f}s" if len(all_times) > 1 else "  Std Dev: N/A")
        
        # Error analysis
        if failed_results:
            print(f"\n❌ Error Analysis:")
            error_types = {}
            for result in failed_results:
                error = result.get("error", "Unknown error")
                error_type = error.split(":")[0] if ":" in error else error
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {error_type}: {count} occurrences")
        
        # Performance recommendations
        print(f"\n💡 PERFORMANCE RECOMMENDATIONS:")
        recommendations = [
            "1. Implement connection pooling with optimal pool size",
            "2. Add database indexes on frequently queried columns (item_id, location_id)",
            "3. Use bulk operations for stock level updates",
            "4. Cache frequently accessed data (items, locations)",
            "5. Implement async background processing for non-critical operations",
            "6. Use database transactions more efficiently",
            "7. Consider pagination for large item sets",
            "8. Add request/response compression",
            "9. Implement circuit breaker pattern for resilience",
            "10. Add comprehensive monitoring and alerting"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
        
        return {
            "total_runs": len(self.test_results),
            "successful_runs": len(successful_results),
            "failed_runs": len(failed_results),
            "average_response_time": statistics.mean([r["total_time"] for r in successful_results]) if successful_results else None,
            "recommendations": recommendations
        }


async def main():
    """Main test runner."""
    print("🧪 COMPREHENSIVE RENTAL ENDPOINT PERFORMANCE ANALYSIS")
    print("=" * 60)
    print("Target: http://localhost:8000/api/transactions/new-rental-optimized")
    print("This test will deeply analyze performance issues")
    print()
    
    analyzer = RentalEndpointAnalyzer()
    
    try:
        # Step 1: Analyze implementation
        await analyzer.analyze_endpoint_internals()
        
        # Step 2: Test performance with various scenarios
        await analyzer.test_endpoint_performance(
            num_runs=3,
            item_counts=[1, 5, 10, 15, 20]
        )
        
        # Step 3: Analyze bottlenecks
        bottlenecks = await analyzer.analyze_bottlenecks()
        
        # Step 4: Generate detailed report
        report = analyzer.generate_detailed_report()
        
        print("\n✅ ANALYSIS COMPLETE!")
        
        # Save results to file
        with open('rental_performance_analysis.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "test_results": analyzer.test_results,
                "performance_profile": analyzer.profiler.get_report(),
                "bottlenecks": bottlenecks,
                "summary": report
            }, f, indent=2, default=str)
        
        print("\n📄 Results saved to: rental_performance_analysis.json")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    # Check if server is running
    try:
        import requests
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️  Server returned unexpected status:", response.status_code)
    except:
        print("❌ Server is not running! Please start it with: uvicorn app.main:app --reload")
        print("   Make sure all dependencies are installed from requirements.txt")
        sys.exit(1)
    
    asyncio.run(main())