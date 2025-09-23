#!/usr/bin/env python3
"""
Comprehensive Benchmarking Script for LOG8415E Assignment

This script sends 1000 concurrent requests to test:
- Direct instance endpoints
- Application Load Balancer endpoints
- Custom load balancer performance
- Collects detailed performance metrics and generates reports
"""

import asyncio
import aiohttp
import time
import json
import statistics
import csv
from datetime import datetime
from typing import List, Dict, Optional
import os
import sys

# Add custom load balancer to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'load_balancer'))
from custom_lb import CustomLoadBalancer

class BenchmarkRunner:
    def __init__(self):
        """Initialize benchmark runner"""
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'direct_instances': {},
            'alb_endpoints': {},
            'custom_lb': {},
            'summary': {}
        }
        
        print("Benchmark Runner initialized")

    async def load_deployment_info(self):
        """Load deployment and ALB information"""
        deployment_info = None
        alb_info = None
        
        # Load deployment info
        try:
            with open('deployment_info.json', 'r') as f:
                deployment_info = json.load(f)
            print("Loaded deployment_info.json")
        except FileNotFoundError:
            print("  deployment_info.json not found")
        
        # Load ALB info
        try:
            with open('alb_info.json', 'r') as f:
                alb_info = json.load(f)
            print("Loaded alb_info.json")
        except FileNotFoundError:
            print("  alb_info.json not found")
        
        return deployment_info, alb_info

    async def benchmark_endpoint(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        num_requests: int = 1000,
        concurrent_requests: int = 50,
        test_name: str = "Benchmark"
    ) -> Dict:
        """Benchmark a specific endpoint with concurrent requests"""
        
        print(f"{test_name}: {endpoint}")
        print(f"   Sending {num_requests} requests with {concurrent_requests} concurrent connections...")
        
        # Semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request():
            async with semaphore:
                start_time = time.time()
                try:
                    async with session.get(
                        endpoint,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # Convert to ms
                        
                        response_data = await response.json()
                        
                        return {
                            'success': True,
                            'response_time': response_time,
                            'status_code': response.status,
                            'timestamp': end_time,
                            'instance_id': response_data.get('instance_id', 'unknown'),
                            'cluster': response_data.get('cluster', 'unknown')
                        }
                        
                except Exception as e:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    return {
                        'success': False,
                        'response_time': response_time,
                        'status_code': 0,
                        'timestamp': end_time,
                        'error': str(e),
                        'instance_id': 'unknown',
                        'cluster': 'unknown'
                    }
        
        # Execute requests
        overall_start = time.time()
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        overall_end = time.time()
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        response_times = [r['response_time'] for r in successful_requests]
        
        total_time = overall_end - overall_start
        throughput = len(successful_requests) / total_time if total_time > 0 else 0
        
        # Calculate percentiles
        percentiles = {}
        if response_times:
            response_times.sort()
            percentiles = {
                'p50': statistics.median(response_times),
                'p90': response_times[int(0.9 * len(response_times))] if len(response_times) > 10 else response_times[-1],
                'p95': response_times[int(0.95 * len(response_times))] if len(response_times) > 20 else response_times[-1],
                'p99': response_times[int(0.99 * len(response_times))] if len(response_times) > 100 else response_times[-1]
            }
        
        # Instance distribution
        instance_distribution = {}
        for result in successful_requests:
            instance_id = result['instance_id']
            if instance_id not in instance_distribution:
                instance_distribution[instance_id] = 0
            instance_distribution[instance_id] += 1
        
        benchmark_result = {
            'endpoint': endpoint,
            'test_name': test_name,
            'total_requests': num_requests,
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / num_requests * 100,
            'total_time': total_time,
            'throughput': throughput,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'std_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            'percentiles': percentiles,
            'instance_distribution': instance_distribution,
            'detailed_results': results
        }
        
        print(f"   Completed: {len(successful_requests)}/{num_requests} successful")
        print(f"   Avg response time: {benchmark_result['avg_response_time']:.2f}ms")
        print(f"   Throughput: {throughput:.2f} req/s")
        
        return benchmark_result

    async def benchmark_direct_instances(self, session: aiohttp.ClientSession, deployment_info: Dict):
        """Benchmark direct instance endpoints"""
        print("\nBENCHMARKING DIRECT INSTANCE ENDPOINTS")
        print("="*60)
        
        direct_results = {}
        
        for endpoint in deployment_info.get('endpoints', []):
            try:
                result = await self.benchmark_endpoint(
                    session=session,
                    endpoint=endpoint,
                    num_requests=100,  # Fewer requests per instance
                    concurrent_requests=10,
                    test_name="Direct Instance"
                )
                direct_results[endpoint] = result
                
            except Exception as e:
                print(f"❌ Error benchmarking {endpoint}: {e}")
                direct_results[endpoint] = {
                    'error': str(e),
                    'endpoint': endpoint
                }
        
        self.results['direct_instances'] = direct_results
        return direct_results

    async def benchmark_alb_endpoints(self, session: aiohttp.ClientSession, alb_info: Dict):
        """Benchmark ALB endpoints"""
        print("\nBENCHMARKING APPLICATION LOAD BALANCER ENDPOINTS")
        print("="*60)
        
        alb_results = {}
        
        endpoints_to_test = [
            ('Root endpoint', alb_info['endpoints']['root']),
            ('Cluster1 endpoint', alb_info['endpoints']['cluster1']),
            ('Cluster2 endpoint', alb_info['endpoints']['cluster2'])
        ]
        
        for test_name, endpoint in endpoints_to_test:
            try:
                result = await self.benchmark_endpoint(
                    session=session,
                    endpoint=endpoint,
                    num_requests=1000,
                    concurrent_requests=50,
                    test_name=f"ALB {test_name}"
                )
                alb_results[test_name] = result
                
            except Exception as e:
                print(f"❌ Error benchmarking ALB {test_name}: {e}")
                alb_results[test_name] = {
                    'error': str(e),
                    'endpoint': endpoint
                }
        
        self.results['alb_endpoints'] = alb_results
        return alb_results

    async def benchmark_custom_load_balancer(self, session: aiohttp.ClientSession, deployment_info: Dict):
        """Benchmark custom load balancer"""
        print("\n BENCHMARKING CUSTOM LOAD BALANCER")
        print("="*60)
        
        try:
            instances = deployment_info.get('endpoints', [])
            if not instances:
                print("❌ No instances found for custom load balancer test")
                return {}
            
            # Initialize custom load balancer
            custom_lb = CustomLoadBalancer(instances)
            
            # Benchmark the custom load balancer
            print("Testing custom load balancer with intelligent routing...")
            
            start_time = time.time()
            
            # First, collect performance data
            await custom_lb.benchmark_instances(num_requests=50, concurrent_requests=10)
            
            # Then do the main benchmark
            num_requests = 500
            concurrent_requests = 25
            
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            async def make_lb_request():
                async with semaphore:
                    return await custom_lb.send_request(session, "/")
            
            print(f"Sending {num_requests} requests through custom load balancer...")
            
            tasks = [make_lb_request() for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze results
            successful_requests = [r for r in results if r['success']]
            failed_requests = [r for r in results if not r['success']]
            
            response_times = [r['response_time'] for r in successful_requests]
            
            throughput = len(successful_requests) / total_time if total_time > 0 else 0
            
            # Instance distribution
            instance_distribution = {}
            for result in successful_requests:
                instance = result.get('instance', 'unknown')
                if instance not in instance_distribution:
                    instance_distribution[instance] = 0
                instance_distribution[instance] += 1
            
            # Calculate percentiles
            percentiles = {}
            if response_times:
                response_times.sort()
                percentiles = {
                    'p50': statistics.median(response_times),
                    'p90': response_times[int(0.9 * len(response_times))] if len(response_times) > 10 else response_times[-1],
                    'p95': response_times[int(0.95 * len(response_times))] if len(response_times) > 20 else response_times[-1],
                    'p99': response_times[int(0.99 * len(response_times))] if len(response_times) > 100 else response_times[-1]
                }
            
            custom_lb_result = {
                'test_name': 'Custom Load Balancer',
                'total_requests': num_requests,
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'success_rate': len(successful_requests) / num_requests * 100,
                'total_time': total_time,
                'throughput': throughput,
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'std_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0,
                'percentiles': percentiles,
                'instance_distribution': instance_distribution,
                'load_balancer_stats': custom_lb.get_performance_stats(),
                'detailed_results': results
            }
            
            print(f"   Completed: {len(successful_requests)}/{num_requests} successful")
            print(f"   Avg response time: {custom_lb_result['avg_response_time']:.2f}ms")
            print(f"   Throughput: {throughput:.2f} req/s")
            
            # Print load balancer performance summary
            custom_lb.print_performance_summary()
            
            self.results['custom_lb'] = custom_lb_result
            return custom_lb_result
            
        except Exception as e:
            print(f"❌ Error benchmarking custom load balancer: {e}")
            return {'error': str(e)}

    def save_results_to_csv(self, filename: str = 'benchmark_results.csv'):
        """Save benchmark results to CSV format"""
        csv_data = []
        
        # Direct instances
        for endpoint, result in self.results.get('direct_instances', {}).items():
            if 'error' not in result:
                csv_data.append({
                    'test_type': 'Direct Instance',
                    'endpoint': endpoint,
                    'total_requests': result['total_requests'],
                    'successful_requests': result['successful_requests'],
                    'success_rate': result['success_rate'],
                    'avg_response_time': result['avg_response_time'],
                    'throughput': result['throughput'],
                    'p50_response_time': result['percentiles'].get('p50', 0),
                    'p95_response_time': result['percentiles'].get('p95', 0),
                    'p99_response_time': result['percentiles'].get('p99', 0)
                })
        
        # ALB endpoints
        for test_name, result in self.results.get('alb_endpoints', {}).items():
            if 'error' not in result:
                csv_data.append({
                    'test_type': f'ALB {test_name}',
                    'endpoint': result['endpoint'],
                    'total_requests': result['total_requests'],
                    'successful_requests': result['successful_requests'],
                    'success_rate': result['success_rate'],
                    'avg_response_time': result['avg_response_time'],
                    'throughput': result['throughput'],
                    'p50_response_time': result['percentiles'].get('p50', 0),
                    'p95_response_time': result['percentiles'].get('p95', 0),
                    'p99_response_time': result['percentiles'].get('p99', 0)
                })
        
        # Custom load balancer
        if 'custom_lb' in self.results and 'error' not in self.results['custom_lb']:
            result = self.results['custom_lb']
            csv_data.append({
                'test_type': 'Custom Load Balancer',
                'endpoint': 'Custom LB',
                'total_requests': result['total_requests'],
                'successful_requests': result['successful_requests'],
                'success_rate': result['success_rate'],
                'avg_response_time': result['avg_response_time'],
                'throughput': result['throughput'],
                'p50_response_time': result['percentiles'].get('p50', 0),
                'p95_response_time': result['percentiles'].get('p95', 0),
                'p99_response_time': result['percentiles'].get('p99', 0)
            })
        
        # Write CSV
        if csv_data:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            print(f"CSV results saved to: {filename}")

    def save_results_to_json(self, filename: str = 'benchmark_results.json'):
        """Save detailed benchmark results to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Detailed results saved to: {filename}")

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*80)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*80)
        
        print(f"\nPERFORMANCE COMPARISON:")
        
        # Collect summary data
        summary_data = []
        
        # ALB endpoints
        for test_name, result in self.results.get('alb_endpoints', {}).items():
            if 'error' not in result:
                summary_data.append({
                    'name': f'ALB {test_name}',
                    'avg_response_time': result['avg_response_time'],
                    'throughput': result['throughput'],
                    'success_rate': result['success_rate']
                })
        
        # Custom load balancer
        if 'custom_lb' in self.results and 'error' not in self.results['custom_lb']:
            result = self.results['custom_lb']
            summary_data.append({
                'name': 'Custom Load Balancer',
                'avg_response_time': result['avg_response_time'],
                'throughput': result['throughput'],
                'success_rate': result['success_rate']
            })
        
        # Sort by average response time
        summary_data.sort(key=lambda x: x['avg_response_time'])
        
        for i, data in enumerate(summary_data, 1):
            print(f"\n   {i}. {data['name']}")
            print(f"      Avg Response Time: {data['avg_response_time']:.2f}ms")
            print(f"      Throughput: {data['throughput']:.2f} req/s")
            print(f"      Success Rate: {data['success_rate']:.1f}%")
        
        # Find best performer
        if summary_data:
            best = summary_data[0]
            print(f"\nBEST PERFORMING CONFIGURATION:")
            print(f"   • {best['name']}")
            print(f"   • Average Response Time: {best['avg_response_time']:.2f}ms")
            print(f"   • Throughput: {best['throughput']:.2f} req/s")
        
        print("\n" + "="*80)
        print("Files generated:")
        print("   • benchmark_results.json (detailed results)")
        print("   • benchmark_results.csv (summary for spreadsheet)")
        print("   • custom_lb_stats.json (load balancer performance)")
        print("="*80)

async def main():
    """Main benchmarking function"""
    try:
        print("Starting Comprehensive Benchmark for LOG8415E Assignment")
        print("="*70)
        
        # Initialize benchmark runner
        runner = BenchmarkRunner()
        
        # Load deployment information
        deployment_info, alb_info = await runner.load_deployment_info()
        
        if not deployment_info and not alb_info:
            print("❌ No deployment information found.")
            print("   Please run setup_aws.py and create_alb.py first.")
            return
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=100)
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        ) as session:
            
            # Benchmark direct instances
            if deployment_info:
                await runner.benchmark_direct_instances(session, deployment_info)
            
            # Benchmark ALB endpoints
            if alb_info:
                await runner.benchmark_alb_endpoints(session, alb_info)
            
            # Benchmark custom load balancer
            if deployment_info:
                await runner.benchmark_custom_load_balancer(session, deployment_info)
        
        # Save results
        runner.save_results_to_json()
        runner.save_results_to_csv()
        
        # Print summary
        runner.print_summary()
        
    except KeyboardInterrupt:
        print("\n  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())