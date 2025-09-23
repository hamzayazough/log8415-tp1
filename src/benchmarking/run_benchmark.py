import asyncio
import aiohttp
import json
import time
import statistics
from datetime import datetime

class BenchmarkRunner:
    def __init__(self):
        """Initialize benchmark runner"""
        self.results = {}
        print("Benchmark Runner initialized")

    async def load_endpoints(self):
        """Load endpoints from deployment files"""
        endpoints = {'cluster1_direct': [], 'cluster2_direct': [], 'alb_cluster1': None, 'alb_cluster2': None}
        
        try:
            with open('deployment_info.json', 'r') as f:
                deployment = json.load(f)
            endpoints['cluster1_direct'] = deployment.get('endpoints', {}).get('cluster1', [])
            endpoints['cluster2_direct'] = deployment.get('endpoints', {}).get('cluster2', [])
        except FileNotFoundError:
            print("deployment_info.json not found")
        
        try:
            with open('alb_info.json', 'r') as f:
                alb_info = json.load(f)
            endpoints['alb_cluster1'] = alb_info.get('endpoints', {}).get('cluster1', '')
            endpoints['alb_cluster2'] = alb_info.get('endpoints', {}).get('cluster2', '')
        except FileNotFoundError:
            print("alb_info.json not found")
        
        return endpoints

    async def benchmark_endpoint(self, session, endpoint, num_requests=100, name="Endpoint"):
        """Benchmark a single endpoint"""
        print(f"Benchmarking {name}: {endpoint}")
        print(f"  Sending {num_requests} requests...")
        
        semaphore = asyncio.Semaphore(10)
        
        async def make_request():
            async with semaphore:
                start_time = time.time()
                try:
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        await response.text()
                        response_time = (time.time() - start_time) * 1000 
                        return {
                            'success': True,
                            'response_time': response_time,
                            'status_code': response.status
                        }
                except Exception as e:
                    return {
                        'success': False,
                        'response_time': 0,
                        'error': str(e)
                    }
        
        overall_start = time.time()
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        overall_time = time.time() - overall_start
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        response_times = [r['response_time'] for r in successful]
        
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            throughput = len(successful) / overall_time
        else:
            avg_time = min_time = max_time = throughput = 0
        
        result = {
            'endpoint': endpoint,
            'total_requests': num_requests,
            'successful_requests': len(successful),
            'failed_requests': len(failed),
            'success_rate': len(successful) / num_requests * 100,
            'avg_response_time': avg_time,
            'min_response_time': min_time,
            'max_response_time': max_time,
            'throughput': throughput,
            'total_time': overall_time
        }
        
        print(f"  Success rate: {result['success_rate']:.1f}%")
        print(f"  Avg response time: {avg_time:.2f}ms")
        print(f"  Throughput: {throughput:.2f} req/s")
        
        return result

    async def run_benchmarks(self, endpoints):
        print("\nStarting Performance Benchmarks")
        print("=" * 50)
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            if endpoints['alb_cluster1']:
                print(f"\nTesting ALB Cluster1 (/cluster1):")
                result = await self.benchmark_endpoint(
                    session, endpoints['alb_cluster1'], 1000, "ALB Cluster1"
                )
                self.results['alb_cluster1'] = result
            
            if endpoints['alb_cluster2']:
                print(f"\nTesting ALB Cluster2 (/cluster2):")
                result = await self.benchmark_endpoint(
                    session, endpoints['alb_cluster2'], 1000, "ALB Cluster2"
                )
                self.results['alb_cluster2'] = result
            
            if endpoints['cluster1_direct']:
                print(f"\nTesting Direct Cluster1 Instances:")
                direct_results = []
                for i, endpoint in enumerate(endpoints['cluster1_direct'][:2]):
                    result = await self.benchmark_endpoint(
                        session, endpoint, 100, f"Cluster1 Instance {i+1}"
                    )
                    direct_results.append(result)
                self.results['direct_cluster1'] = direct_results
            
            if endpoints['cluster2_direct']:
                print(f"\nTesting Direct Cluster2 Instances:")
                direct_results = []
                for i, endpoint in enumerate(endpoints['cluster2_direct'][:2]):
                    result = await self.benchmark_endpoint(
                        session, endpoint, 100, f"Cluster2 Instance {i+1}"
                    )
                    direct_results.append(result)
                self.results['direct_cluster2'] = direct_results

    def analyze_results(self):
        """Analyze and compare results"""
        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {},
            'detailed_results': self.results
        }
        
        summary = {}
        
        if 'alb_cluster1' in self.results:
            summary['alb_cluster1_avg_response_time'] = self.results['alb_cluster1']['avg_response_time']
            summary['alb_cluster1_throughput'] = self.results['alb_cluster1']['throughput']
        
        if 'alb_cluster2' in self.results:
            summary['alb_cluster2_avg_response_time'] = self.results['alb_cluster2']['avg_response_time']
            summary['alb_cluster2_throughput'] = self.results['alb_cluster2']['throughput']
        
        if 'direct_cluster1' in self.results:
            direct1_times = [r['avg_response_time'] for r in self.results['direct_cluster1']]
            summary['direct_cluster1_avg_response_time'] = statistics.mean(direct1_times) if direct1_times else 0
        
        if 'direct_cluster2' in self.results:
            direct2_times = [r['avg_response_time'] for r in self.results['direct_cluster2']]
            summary['direct_cluster2_avg_response_time'] = statistics.mean(direct2_times) if direct2_times else 0
        
        if 'alb_cluster1_avg_response_time' in summary and 'alb_cluster2_avg_response_time' in summary:
            if summary['alb_cluster1_avg_response_time'] < summary['alb_cluster2_avg_response_time']:
                summary['faster_cluster'] = 'Cluster1 (t2.large) is faster'
            else:
                summary['faster_cluster'] = 'Cluster2 (t2.micro) is faster'
        
        analysis['summary'] = summary
        return analysis

    def save_results(self, analysis):
        with open('benchmark_results.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        
        csv_data = []
        
        if 'alb_cluster1' in self.results:
            csv_data.append([
                'ALB Cluster1',
                self.results['alb_cluster1']['endpoint'],
                self.results['alb_cluster1']['total_requests'],
                f"{self.results['alb_cluster1']['success_rate']:.1f}%",
                f"{self.results['alb_cluster1']['avg_response_time']:.2f}",
                f"{self.results['alb_cluster1']['throughput']:.2f}"
            ])
        
        if 'alb_cluster2' in self.results:
            csv_data.append([
                'ALB Cluster2',
                self.results['alb_cluster2']['endpoint'],
                self.results['alb_cluster2']['total_requests'],
                f"{self.results['alb_cluster2']['success_rate']:.1f}%",
                f"{self.results['alb_cluster2']['avg_response_time']:.2f}",
                f"{self.results['alb_cluster2']['throughput']:.2f}"
            ])
        
        if 'direct_cluster1' in self.results:
            for i, result in enumerate(self.results['direct_cluster1']):
                csv_data.append([
                    f'Direct Cluster1-{i+1}',
                    result['endpoint'],
                    result['total_requests'],
                    f"{result['success_rate']:.1f}%",
                    f"{result['avg_response_time']:.2f}",
                    f"{result['throughput']:.2f}"
                ])
        
        if 'direct_cluster2' in self.results:
            for i, result in enumerate(self.results['direct_cluster2']):
                csv_data.append([
                    f'Direct Cluster2-{i+1}',
                    result['endpoint'],
                    result['total_requests'],
                    f"{result['success_rate']:.1f}%",
                    f"{result['avg_response_time']:.2f}",
                    f"{result['throughput']:.2f}"
                ])
        
        with open('benchmark_results.csv', 'w') as f:
            f.write('Type,Endpoint,Requests,Success Rate,Avg Response Time (ms),Throughput (req/s)\n')
            for row in csv_data:
                f.write(','.join(map(str, row)) + '\n')
        
        print("Results saved to benchmark_results.json and benchmark_results.csv")

    def print_summary(self, analysis):
        print("\n" + "="*60)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*60)
        
        if 'summary' in analysis:
            summary = analysis['summary']
            print(f"\nCLUSTER PERFORMANCE COMPARISON:")
            
            if 'alb_cluster1_avg_response_time' in summary:
                print(f"  • ALB Cluster1 (t2.large) avg response: {summary['alb_cluster1_avg_response_time']:.2f}ms")
                print(f"  • ALB Cluster1 throughput: {summary['alb_cluster1_throughput']:.2f} req/s")
            
            if 'alb_cluster2_avg_response_time' in summary:
                print(f"  • ALB Cluster2 (t2.micro) avg response: {summary['alb_cluster2_avg_response_time']:.2f}ms")
                print(f"  • ALB Cluster2 throughput: {summary['alb_cluster2_throughput']:.2f} req/s")
            
            if 'direct_cluster1_avg_response_time' in summary:
                print(f"  • Direct Cluster1 avg response: {summary['direct_cluster1_avg_response_time']:.2f}ms")
            
            if 'direct_cluster2_avg_response_time' in summary:
                print(f"  • Direct Cluster2 avg response: {summary['direct_cluster2_avg_response_time']:.2f}ms")
            
            if 'faster_cluster' in summary:
                print(f"\nPERFORMANCE WINNER: {summary['faster_cluster']}")
        
        print("\n" + "="*60)

async def main():
    try:
        print("Starting Simplified Benchmark for LOG8415E Assignment")
        
        runner = BenchmarkRunner()
        
        endpoints = await runner.load_endpoints()
        
        if not any(endpoints.values()):
            print("No endpoints found. Run setup_aws.py and create_alb.py first.")
            return
        
        await runner.run_benchmarks(endpoints)
        
        analysis = runner.analyze_results()
        runner.save_results(analysis)
        runner.print_summary(analysis)
        
        print("\nBenchmarking completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())