"""
Comprehensive test suite for the new rental optimization endpoint.
This test analyzes performance bottlenecks and provides detailed timing analysis.
"""

import time
import json
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Test configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/transactions/new-rental-optimized"
TEST_RUNS = 5  # Number of test runs for statistical analysis


class PerformanceAnalyzer:
    """Analyzes and reports performance metrics for the rental optimization endpoint."""
    
    def __init__(self):
        self.results = []
        self.db_query_times = []
        self.total_times = []
        
    def record_result(self, result: Dict[str, Any]):
        """Record a test result for analysis."""
        self.results.append(result)
        if 'total_time' in result:
            self.total_times.append(result['total_time'])
            
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics and return detailed report."""
        if not self.total_times:
            return {"error": "No performance data collected"}
            
        return {
            "total_requests": len(self.total_times),
            "average_time": statistics.mean(self.total_times),
            "median_time": statistics.median(self.total_times),
            "min_time": min(self.total_times),
            "max_time": max(self.total_times),
            "std_deviation": statistics.stdev(self.total_times) if len(self.total_times) > 1 else 0,
            "percentile_95": self._calculate_percentile(self.total_times, 95),
            "percentile_99": self._calculate_percentile(self.total_times, 99),
            "performance_grade": self._grade_performance(statistics.mean(self.total_times))
        }
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _grade_performance(self, avg_time: float) -> str:
        """Grade performance based on average response time."""
        if avg_time < 0.5:
            return "A+ (Excellent)"
        elif avg_time < 1.0:
            return "A (Very Good)"
        elif avg_time < 2.0:
            return "B (Good)"
        elif avg_time < 5.0:
            return "C (Acceptable)"
        elif avg_time < 10.0:
            return "D (Poor)"
        else:
            return "F (Unacceptable)"


class RentalTestDataGenerator:
    """Generates test data for rental optimization tests."""
    
    @staticmethod
    def generate_rental_request(item_count: int = 3) -> Dict[str, Any]:
        """Generate a new rental request with specified number of items."""
        base_date = datetime.now().date()
        rental_start = base_date + timedelta(days=1)
        rental_end = rental_start + timedelta(days=7)
        
        # Generate items with different rental periods
        items = []
        for i in range(item_count):
            items.append({
                "item_id": f"test-item-{i+1}",
                "quantity": 1 + (i % 3),  # Vary quantity 1-3
                "rental_period_value": 7 + (i * 2),  # Vary rental period
                "rental_start_date": rental_start.isoformat(),
                "rental_end_date": (rental_end + timedelta(days=i)).isoformat()
            })
        
        return {
            "customer_id": "test-customer-uuid",
            "location_id": "test-location-uuid",
            "transaction_date": base_date.isoformat(),
            "payment_method": "cash",
            "items": items
        }


class DatabaseAnalyzer:
    """Analyzes database queries and performance bottlenecks."""
    
    def __init__(self):
        self.query_log = []
        self.connection_pool_stats = {}
        
    async def analyze_database_performance(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Analyze database performance metrics."""
        try:
            # Get connection pool stats
            pool_stats = await self._get_pool_stats(db_session)
            
            # Get slow query analysis
            slow_queries = await self._get_slow_queries(db_session)
            
            # Get table statistics
            table_stats = await self._get_table_stats(db_session)
            
            # Get index usage
            index_stats = await self._get_index_stats(db_session)
            
            return {
                "pool_stats": pool_stats,
                "slow_queries": slow_queries,
                "table_stats": table_stats,
                "index_stats": index_stats,
                "recommendations": self._generate_recommendations(slow_queries, table_stats, index_stats)
            }
        except Exception as e:
            return {"error": f"Database analysis failed: {str(e)}"}
    
    async def _get_pool_stats(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get connection pool statistics."""
        try:
            result = await db_session.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) filter (where state = 'active') as active_connections,
                    count(*) filter (where state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """))
            stats = result.fetchone()
            return {
                "total_connections": stats[0] if stats else 0,
                "active_connections": stats[1] if stats else 0,
                "idle_connections": stats[2] if stats else 0
            }
        except Exception as e:
            return {"error": f"Could not get pool stats: {str(e)}"}
    
    async def _get_slow_queries(self, db_session: AsyncSession) -> List[Dict[str, Any]]:
        """Get slow running queries."""
        try:
            result = await db_session.execute(text("""
                SELECT 
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_exec_time > 10  -- Queries taking more than 10ms
                ORDER BY mean_exec_time DESC 
                LIMIT 10
            """))
            return [
                {
                    "query": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                    "mean_exec_time": float(row[1]),
                    "calls": int(row[2]),
                    "total_exec_time": float(row[3]),
                    "rows": int(row[4]),
                    "hit_percent": float(row[5]) if row[5] else 0.0
                }
                for row in result.fetchall()
            ]
        except Exception as e:
            return [{"error": f"Could not get slow queries: {str(e)}"}]
    
    async def _get_table_stats(self, db_session: AsyncSession) -> List[Dict[str, Any]]:
        """Get table statistics for rental-related tables."""
        try:
            result = await db_session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_tup_hot_upd,
                    n_live_tup,
                    n_dead_tup,
                    vacuum_count,
                    autovacuum_count,
                    analyze_count,
                    autoanalyze_count
                FROM pg_stat_user_tables 
                WHERE tablename IN ('transaction_headers', 'transaction_lines', 'stock_levels', 'stock_movements')
                ORDER BY n_live_tup DESC
            """))
            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "inserts": int(row[2]),
                    "updates": int(row[3]),
                    "deletes": int(row[4]),
                    "hot_updates": int(row[5]),
                    "live_tuples": int(row[6]),
                    "dead_tuples": int(row[7]),
                    "vacuum_count": int(row[8]),
                    "autovacuum_count": int(row[9]),
                    "analyze_count": int(row[10]),
                    "autoanalyze_count": int(row[11])
                }
                for row in result.fetchall()
            ]
        except Exception as e:
            return [{"error": f"Could not get table stats: {str(e)}"}]
    
    async def _get_index_stats(self, db_session: AsyncSession) -> List[Dict[str, Any]]:
        """Get index usage statistics."""
        try:
            result = await db_session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public' 
                  AND tablename IN ('transaction_headers', 'transaction_lines', 'stock_levels', 'stock_movements')
                ORDER BY idx_scan DESC
            """))
            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "tuples_read": int(row[3]),
                    "tuples_fetched": int(row[4]),
                    "scans": int(row[5])
                }
                for row in result.fetchall()
            ]
        except Exception as e:
            return [{"error": f"Could not get index stats: {str(e)}"}]
    
    def _generate_recommendations(self, slow_queries: List[Dict], table_stats: List[Dict], index_stats: List[Dict]) -> List[str]:
        """Generate performance recommendations based on analysis."""
        recommendations = []
        
        # Check for slow queries
        if slow_queries and not any("error" in q for q in slow_queries):
            avg_time = sum(q["mean_exec_time"] for q in slow_queries) / len(slow_queries)
            if avg_time > 100:  # More than 100ms average
                recommendations.append("Consider optimizing slow queries - average execution time is high")
        
        # Check for dead tuples
        for table in table_stats:
            if "error" not in table:
                dead_ratio = table["dead_tuples"] / max(table["live_tuples"], 1)
                if dead_ratio > 0.1:  # More than 10% dead tuples
                    recommendations.append(f"Table {table['table']} has high dead tuple ratio - consider manual vacuum")
        
        # Check for unused indexes
        unused_indexes = [idx for idx in index_stats if "error" not in idx and idx["scans"] == 0]
        if unused_indexes:
            recommendations.append(f"Found {len(unused_indexes)} unused indexes - consider dropping them")
        
        # Check for missing indexes (heuristic based on table scans)
        high_read_tables = [t for t in table_stats if "error" not in t and t["live_tuples"] > 1000]
        if high_read_tables:
            recommendations.append("Consider adding indexes for large tables with frequent reads")
        
        return recommendations


async def test_rental_optimization_endpoint():
    """Comprehensive test of the rental optimization endpoint."""
    
    print("🚀 Starting Comprehensive Rental Optimization Test")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    db_analyzer = DatabaseAnalyzer()
    data_generator = RentalTestDataGenerator()
    
    # Test scenarios with different item counts
    test_scenarios = [
        {"name": "Single Item", "item_count": 1},
        {"name": "Small Order", "item_count": 3},
        {"name": "Medium Order", "item_count": 7},
        {"name": "Large Order", "item_count": 15},
        {"name": "Bulk Order", "item_count": 30}
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for scenario in test_scenarios:
            print(f"\n📊 Testing {scenario['name']} ({scenario['item_count']} items)")
            print("-" * 40)
            
            scenario_times = []
            
            for run in range(TEST_RUNS):
                # Generate test data
                rental_data = data_generator.generate_rental_request(scenario['item_count'])
                
                # Measure performance
                start_time = time.time()
                
                try:
                    response = await client.post(
                        f"{BASE_URL}{ENDPOINT}",
                        json=rental_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    scenario_times.append(total_time)
                    
                    # Record result
                    result = {
                        "scenario": scenario['name'],
                        "item_count": scenario['item_count'],
                        "run": run + 1,
                        "total_time": total_time,
                        "status_code": response.status_code,
                        "response_size": len(response.content) if response.content else 0
                    }
                    
                    if response.status_code == 200:
                        result["success"] = True
                        try:
                            result["response_data"] = response.json()
                        except:
                            result["response_data"] = "Invalid JSON"
                    else:
                        result["success"] = False
                        result["error"] = response.text
                    
                    analyzer.record_result(result)
                    
                    print(f"  Run {run + 1}: {total_time:.3f}s - Status: {response.status_code}")
                    
                except Exception as e:
                    print(f"  Run {run + 1}: ERROR - {str(e)}")
                    analyzer.record_result({
                        "scenario": scenario['name'],
                        "item_count": scenario['item_count'],
                        "run": run + 1,
                        "error": str(e),
                        "success": False
                    })
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            # Scenario summary
            if scenario_times:
                avg_time = statistics.mean(scenario_times)
                print(f"  Average time: {avg_time:.3f}s")
                print(f"  Min/Max: {min(scenario_times):.3f}s / {max(scenario_times):.3f}s")
    
    # Generate comprehensive report
    print("\n📈 PERFORMANCE ANALYSIS REPORT")
    print("=" * 60)
    
    # Overall performance metrics
    perf_metrics = analyzer.analyze_performance()
    print(f"Total Requests: {perf_metrics.get('total_requests', 'N/A')}")
    print(f"Average Response Time: {perf_metrics.get('average_time', 0):.3f}s")
    print(f"Median Response Time: {perf_metrics.get('median_time', 0):.3f}s")
    print(f"95th Percentile: {perf_metrics.get('percentile_95', 0):.3f}s")
    print(f"99th Percentile: {perf_metrics.get('percentile_99', 0):.3f}s")
    print(f"Performance Grade: {perf_metrics.get('performance_grade', 'N/A')}")
    
    # Detailed analysis by scenario
    print("\n📊 SCENARIO BREAKDOWN")
    print("-" * 30)
    
    scenario_analysis = {}
    for result in analyzer.results:
        if result.get('success') and 'total_time' in result:
            scenario = result['scenario']
            if scenario not in scenario_analysis:
                scenario_analysis[scenario] = []
            scenario_analysis[scenario].append(result['total_time'])
    
    for scenario, times in scenario_analysis.items():
        if times:
            print(f"{scenario}:")
            print(f"  Average: {statistics.mean(times):.3f}s")
            print(f"  Min/Max: {min(times):.3f}s / {max(times):.3f}s")
            print(f"  Success Rate: {len(times)}/{TEST_RUNS} ({len(times)/TEST_RUNS*100:.1f}%)")
    
    print("\n🔍 PERFORMANCE BOTTLENECK ANALYSIS")
    print("=" * 60)
    
    # Identify key bottlenecks
    bottlenecks = []
    
    if perf_metrics.get('average_time', 0) > 2.0:
        bottlenecks.append("⚠️  Average response time exceeds 2-second target")
    
    if perf_metrics.get('percentile_95', 0) > 5.0:
        bottlenecks.append("⚠️  95th percentile response time is concerning")
    
    error_rate = len([r for r in analyzer.results if not r.get('success')]) / len(analyzer.results)
    if error_rate > 0.1:
        bottlenecks.append(f"⚠️  High error rate: {error_rate*100:.1f}%")
    
    if bottlenecks:
        print("IDENTIFIED BOTTLENECKS:")
        for bottleneck in bottlenecks:
            print(f"  {bottleneck}")
    else:
        print("✅ No major performance bottlenecks identified")
    
    print("\n💡 RECOMMENDATIONS")
    print("-" * 20)
    
    recommendations = [
        "1. Fix method name mismatch in routes.py (create_new_rental_minimal_test → create_new_rental_optimized)",
        "2. Add database query profiling to identify slow queries",
        "3. Implement connection pooling optimization",
        "4. Consider adding Redis caching for frequently accessed data",
        "5. Add async background processing for non-critical operations",
        "6. Implement proper database indexing strategy",
        "7. Add circuit breaker pattern for external dependencies",
        "8. Monitor memory usage during large order processing"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print("\n🎯 NEXT STEPS")
    print("-" * 15)
    print("1. Fix the critical method name issue in the route handler")
    print("2. Run database analysis to identify query performance issues")
    print("3. Implement comprehensive monitoring and alerting")
    print("4. Create load testing scenarios for production readiness")
    
    return analyzer.results


if __name__ == "__main__":
    print("🧪 Rental Optimization Endpoint Test Suite")
    print("This test will analyze performance and identify bottlenecks")
    print("Make sure the FastAPI server is running on localhost:8000")
    print()
    
    try:
        results = asyncio.run(test_rental_optimization_endpoint())
        print(f"\n✅ Test completed successfully! Analyzed {len(results)} requests.")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()