#!/usr/bin/env python3
"""
Custom Client Load Balancer for LOG8415E Assignment

This implements a client-side load balancer that:
- Monitors response times from all instances
- Routes new requests to the most responsive instance
- Provides performance analytics and reporting
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Optional
import os

class CustomLoadBalancer:
    def __init__(self, instances: List[str]):
        """
        Initialize custom load balancer
        
        Args:
            instances: List of instance endpoints (e.g., ['http://dns1:8000', 'http://dns2:8000'])
        """
        self.instances = instances
        self.response_times = {instance: [] for instance in instances}
        self.error_counts = {instance: 0 for instance in instances}
        self.request_counts = {instance: 0 for instance in instances}
        self.last_health_check = {instance: 0 for instance in instances}
        self.healthy_instances = set(instances)
        
        print(f"Custom Load Balancer initialized with {len(instances)} instances")

    async def health_check(self, session: aiohttp.ClientSession, instance: str) -> bool:
        """Check if an instance is healthy"""
        try:
            start_time = time.time()
            
            async with session.get(
                f"{instance}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                if response.status == 200:
                    # Update response time for this instance
                    self.response_times[instance].append(response_time)
                    
                    # Keep only last 10 response times for average calculation
                    if len(self.response_times[instance]) > 10:
                        self.response_times[instance] = self.response_times[instance][-10:]
                    
                    self.last_health_check[instance] = time.time()
                    return True
                else:
                    return False
                    
        except Exception as e:
            self.error_counts[instance] += 1
            return False

    async def perform_health_checks(self, session: aiohttp.ClientSession):
        """Perform health checks on all instances"""
        health_tasks = [
            self.health_check(session, instance) 
            for instance in self.instances
        ]
        
        results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Update healthy instances set
        self.healthy_instances.clear()
        for instance, is_healthy in zip(self.instances, results):
            if is_healthy is True:
                self.healthy_instances.add(instance)
        
        print(f"Health check: {len(self.healthy_instances)}/{len(self.instances)} instances healthy")

    def get_best_instance(self) -> Optional[str]:
        """Get the instance with the best (lowest average) response time"""
        if not self.healthy_instances:
            print("  No healthy instances available!")
            return None
        
        best_instance = None
        best_avg_time = float('inf')
        
        for instance in self.healthy_instances:
            if self.response_times[instance]:
                avg_time = statistics.mean(self.response_times[instance])
                if avg_time < best_avg_time:
                    best_avg_time = avg_time
                    best_instance = instance
        
        # If no response time data, choose first healthy instance
        if best_instance is None and self.healthy_instances:
            best_instance = list(self.healthy_instances)[0]
        
        return best_instance

    async def send_request(self, session: aiohttp.ClientSession, path: str = "/") -> Dict:
        """Send a request to the best available instance"""
        best_instance = self.get_best_instance()
        
        if not best_instance:
            return {
                'success': False,
                'error': 'No healthy instances available',
                'instance': None,
                'response_time': 0,
                'status_code': 0
            }
        
        try:
            start_time = time.time()
            
            async with session.get(
                f"{best_instance}{path}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                # Update metrics
                self.request_counts[best_instance] += 1
                self.response_times[best_instance].append(response_time)
                
                # Keep response time history manageable
                if len(self.response_times[best_instance]) > 50:
                    self.response_times[best_instance] = self.response_times[best_instance][-50:]
                
                response_data = await response.json()
                
                return {
                    'success': True,
                    'instance': best_instance,
                    'response_time': response_time,
                    'status_code': response.status,
                    'data': response_data
                }
                
        except Exception as e:
            self.error_counts[best_instance] += 1
            return {
                'success': False,
                'error': str(e),
                'instance': best_instance,
                'response_time': 0,
                'status_code': 0
            }

    async def benchmark_instances(self, num_requests: int = 100, concurrent_requests: int = 10):
        """Benchmark all instances to collect initial performance data"""
        print(f"Benchmarking {len(self.instances)} instances with {num_requests} requests...")
        
        async with aiohttp.ClientSession() as session:
            # First, do health checks
            await self.perform_health_checks(session)
            
            # Send requests to gather performance data
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def bounded_request():
                async with semaphore:
                    return await self.send_request(session, "/")
            
            # Create tasks for concurrent requests
            tasks = [bounded_request() for _ in range(num_requests)]
            
            # Execute requests
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Analyze results
            successful_requests = [r for r in results if r['success']]
            failed_requests = [r for r in results if not r['success']]
            
            total_time = end_time - start_time
            throughput = len(successful_requests) / total_time if total_time > 0 else 0
            
            print(f"Benchmark completed:")
            print(f"   • Total requests: {num_requests}")
            print(f"   • Successful: {len(successful_requests)}")
            print(f"   • Failed: {len(failed_requests)}")
            print(f"   • Total time: {total_time:.2f}s")
            print(f"   • Throughput: {throughput:.2f} req/s")
            
            return {
                'total_requests': num_requests,
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'total_time': total_time,
                'throughput': throughput,
                'results': results
            }

    def get_performance_stats(self) -> Dict:
        """Get current performance statistics"""
        stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_instances': len(self.instances),
            'healthy_instances': len(self.healthy_instances),
            'instance_stats': {}
        }
        
        for instance in self.instances:
            response_times = self.response_times[instance]
            
            instance_stats = {
                'endpoint': instance,
                'is_healthy': instance in self.healthy_instances,
                'request_count': self.request_counts[instance],
                'error_count': self.error_counts[instance],
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'last_health_check': self.last_health_check[instance]
            }
            
            stats['instance_stats'][instance] = instance_stats
        
        return stats

    def print_performance_summary(self):
        """Print a summary of performance statistics"""
        stats = self.get_performance_stats()
        
        print("\n" + "="*80)
        print("CUSTOM LOAD BALANCER PERFORMANCE SUMMARY")
        print("="*80)
        
        print(f"\nHEALTH STATUS:")
        print(f"   • Total instances: {stats['total_instances']}")
        print(f"   • Healthy instances: {stats['healthy_instances']}")
        print(f"   • Health ratio: {stats['healthy_instances']}/{stats['total_instances']}")
        
        print(f"\nINSTANCE PERFORMANCE:")
        
        # Sort instances by average response time
        sorted_instances = sorted(
            stats['instance_stats'].items(),
            key=lambda x: x[1]['avg_response_time'] if x[1]['avg_response_time'] > 0 else float('inf')
        )
        
        for i, (instance, instance_stats) in enumerate(sorted_instances, 1):
            status = "HEALTHY" if instance_stats['is_healthy'] else "🔴 UNHEALTHY"
            print(f"\n   {i}. {instance}")
            print(f"      Status: {status}")
            print(f"      Requests: {instance_stats['request_count']}")
            print(f"      Errors: {instance_stats['error_count']}")
            print(f"      Avg Response Time: {instance_stats['avg_response_time']:.2f}ms")
            print(f"      Min/Max: {instance_stats['min_response_time']:.2f}ms / {instance_stats['max_response_time']:.2f}ms")
        
        # Find best performing instance
        best_instance = None
        best_time = float('inf')
        
        for instance, instance_stats in stats['instance_stats'].items():
            if (instance_stats['is_healthy'] and 
                instance_stats['avg_response_time'] > 0 and
                instance_stats['avg_response_time'] < best_time):
                best_time = instance_stats['avg_response_time']
                best_instance = instance
        
        if best_instance:
            print(f"\nBEST PERFORMING INSTANCE:")
            print(f"   • {best_instance}")
            print(f"   • Average Response Time: {best_time:.2f}ms")
        
        print("\n" + "="*80)

async def load_instances_from_deployment():
    """Load instance endpoints from deployment_info.json"""
    try:
        with open('deployment_info.json', 'r') as f:
            deployment_info = json.load(f)
        
        instances = []
        for endpoint in deployment_info.get('endpoints', []):
            instances.append(endpoint)
        
        if not instances:
            print("❌ No instances found in deployment_info.json")
            return None
        
        print(f"Loaded {len(instances)} instances from deployment_info.json")
        return instances
        
    except FileNotFoundError:
        print("❌ deployment_info.json not found. Please run setup_aws.py first.")
        return None
    except Exception as e:
        print(f"❌ Error loading deployment info: {e}")
        return None

async def demo_load_balancer(instances: List[str], num_requests: int = 50):
    """Demonstrate the custom load balancer functionality"""
    print("Starting Custom Load Balancer Demo")
    print("="*50)
    
    # Initialize load balancer
    lb = CustomLoadBalancer(instances)
    
    # Benchmark instances to collect initial data
    benchmark_results = await lb.benchmark_instances(num_requests=num_requests, concurrent_requests=5)
    
    # Print performance summary
    lb.print_performance_summary()
    
    # Save performance stats
    stats = lb.get_performance_stats()
    
    # Add benchmark results to stats
    stats['benchmark_results'] = benchmark_results
    
    output_file = 'custom_lb_stats.json'
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nPerformance statistics saved to: {output_file}")
    
    return lb, stats

async def main():
    """Main function to demonstrate custom load balancer"""
    try:
        print("Custom Load Balancer for LOG8415E Assignment")
        print("="*60)
        
        # Load instances from deployment
        instances = await load_instances_from_deployment()
        
        if not instances:
            # Fallback to manual configuration
            print("  Using manual configuration for demo")
            instances = [
                "http://example1.amazonaws.com:8000",
                "http://example2.amazonaws.com:8000",
                "http://example3.amazonaws.com:8000"
            ]
        
        # Run load balancer demo
        lb, stats = await demo_load_balancer(instances, num_requests=30)
        
        print(f"\nCUSTOM LOAD BALANCER FEATURES DEMONSTRATED:")
        print(f"   Health monitoring of all instances")
        print(f"   Response time measurement and tracking")
        print(f"   Intelligent routing to fastest instance")
        print(f"   Error counting and handling")
        print(f"   Performance analytics and reporting")
        
        print(f"\nThis load balancer routes requests to the instance with")
        print(f"   the lowest average response time, ensuring optimal performance!")
        
    except KeyboardInterrupt:
        print("\n  Load balancer demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Load balancer demo failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())