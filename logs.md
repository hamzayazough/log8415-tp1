(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> python src/aws_automation/setup_aws.py
Starting AWS Infrastructure Setup for LOG8415E Assignment
============================================================
AWS Infrastructure Manager initialized for region: us-east-1
Skipping key pair creation (AWS Academy restriction)
Instances will be launched without key pairs (no SSH access)
Using Amazon Linux 2 AMI: ami-0c02fb55956c7d316 (AWS Academy standard)
Using default VPC: vpc-03445e1d10490cf52
Creating security group: LOG8415E-TP1-SG
Security group created: sg-0acd5ba3537dc7df0
Launching 4 t2.large instances for cluster1
Cluster1 instances launched: ['i-0e79beb093ae8025e', 'i-06b8350b5f45784c2', 'i-00ddf704ed784153e', 'i-03e42c37913c38023']
Launching 5 t2.micro instances for cluster2
Cluster2 instances launched: ['i-05297451dcf7708b4', 'i-0c41577a11634d5ea', 'i-04eab2ac04a37e5cd', 'i-0d028b2e0fdf9b5cd', 'i-04c6d3d742da55c00']
Waiting for 9 instances to be running...
All instances are now running!
Deployment information saved to: deployment_info.json

================================================================================
DEPLOYMENT COMPLETED SUCCESSFULLY!
================================================================================

DEPLOYMENT SUMMARY:
• Total Instances: 9
• Cluster1 (t2.large): 4 instances
• Cluster2 (t2.micro): 5 instances
• Region: us-east-1

CLUSTER1 ENDPOINTS (4 instances):

1.  http://ec2-98-89-18-212.compute-1.amazonaws.com:8000
    Instance ID: i-0e79beb093ae8025e
    Public IP: 98.89.18.212
2.  http://ec2-34-229-138-220.compute-1.amazonaws.com:8000
    Instance ID: i-03e42c37913c38023
    Public IP: 34.229.138.220
3.  http://ec2-54-81-100-91.compute-1.amazonaws.com:8000
    Instance ID: i-00ddf704ed784153e
    Public IP: 54.81.100.91
4.  http://ec2-50-19-40-223.compute-1.amazonaws.com:8000
    Instance ID: i-06b8350b5f45784c2
    Public IP: 50.19.40.223

CLUSTER2 ENDPOINTS (5 instances):

1.  http://ec2-34-229-156-148.compute-1.amazonaws.com:8000
    Instance ID: i-0d028b2e0fdf9b5cd
    Public IP: 34.229.156.148
2.  http://ec2-3-85-126-17.compute-1.amazonaws.com:8000
    Instance ID: i-04c6d3d742da55c00
    Public IP: 3.85.126.17
3.  http://ec2-54-198-238-242.compute-1.amazonaws.com:8000
    Instance ID: i-0c41577a11634d5ea
    Public IP: 54.198.238.242
4.  http://ec2-54-147-11-18.compute-1.amazonaws.com:8000
    Instance ID: i-05297451dcf7708b4
    Public IP: 54.147.11.18
5.  http://ec2-18-215-154-58.compute-1.amazonaws.com:8000
    Instance ID: i-04eab2ac04a37e5cd
    Public IP: 18.215.154.58

================================================================================
(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1>

(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> Test-NetConnection ec2-98-89-18-212.compute-1.amazonaws.com -Port 8000

ComputerName : ec2-98-89-18-212.compute-1.amazonaws.com
RemoteAddress : 98.89.18.212
RemotePort : 8000
InterfaceAlias : Wi-Fi
SourceAddress : 192.168.0.14
TcpTestSucceeded : True

(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> Invoke-RestMethod -Uri "http://ec2-98-89-18-212.compute-1.amazonaws.com:8000/"

message instance_id cluster timestamp

---

Instance i-0e79beb093ae8025e is responding now! i-0e79beb093ae8025e cluster1 2025-09-22T22:49:03.993829

(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> Invoke-RestMethod -Uri "http://ec2-98-89-18-212.compute-1.amazonaws.com:8000/health"

status instance_id

---

healthy i-0e79beb093ae8025e

(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1>

(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> python src/load_balancer/custom_lb.py
Custom Load Balancer for LOG8415E Assignment
============================================================
Loaded 9 instances from deployment_info.json
Starting Custom Load Balancer Demo
==================================================
Custom Load Balancer initialized with 9 instances
Benchmarking 9 instances with 30 requests...
Health check: 9/9 instances healthy
Benchmark completed:
• Total requests: 30
• Successful: 30
• Failed: 0
• Total time: 0.31s
• Throughput: 96.42 req/s

================================================================================
CUSTOM LOAD BALANCER PERFORMANCE SUMMARY
================================================================================

HEALTH STATUS:
• Total instances: 9
• Healthy instances: 9
• Health ratio: 9/9

INSTANCE PERFORMANCE:

1.  http://ec2-50-19-40-223.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 30
    Errors: 0
    Avg Response Time: 49.97ms
    Min/Max: 27.40ms / 133.13ms

2.  http://ec2-98-89-18-212.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 138.63ms
    Min/Max: 138.63ms / 138.63ms

3.  http://ec2-34-229-156-148.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 172.66ms
    Min/Max: 172.66ms / 172.66ms

4.  http://ec2-34-229-138-220.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 175.94ms
    Min/Max: 175.94ms / 175.94ms

5.  http://ec2-54-81-100-91.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 176.40ms
    Min/Max: 176.40ms / 176.40ms

6.  http://ec2-54-198-238-242.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 180.25ms
    Min/Max: 180.25ms / 180.25ms

7.  http://ec2-54-147-11-18.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 180.58ms
    Min/Max: 180.58ms / 180.58ms

8.  http://ec2-3-85-126-17.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 181.10ms
    Min/Max: 181.10ms / 181.10ms

9.  http://ec2-18-215-154-58.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 0
    Errors: 0
    Avg Response Time: 181.10ms
    Min/Max: 181.10ms / 181.10ms

BEST PERFORMING INSTANCE:
• http://ec2-50-19-40-223.compute-1.amazonaws.com:8000
• Average Response Time: 49.97ms

================================================================================

Performance statistics saved to: custom_lb_stats.json

CUSTOM LOAD BALANCER FEATURES DEMONSTRATED:
Health monitoring of all instances
Response time measurement and tracking
Intelligent routing to fastest instance
Error counting and handling
Performance analytics and reporting

This load balancer routes requests to the instance with
the lowest average response time, ensuring optimal performance!
(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1>

(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> python src/benchmarking/run_benchmark.py
Starting Comprehensive Benchmark for LOG8415E Assignment
======================================================================
Benchmark Runner initialized
Loaded deployment_info.json
Loaded alb_info.json

# BENCHMARKING DIRECT INSTANCE ENDPOINTS

Direct Instance: http://ec2-34-229-156-148.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 103.74ms
Throughput: 92.49 req/s
Direct Instance: http://ec2-3-85-126-17.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 94.48ms
Throughput: 101.28 req/s
Direct Instance: http://ec2-54-198-238-242.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 97.49ms
Throughput: 97.71 req/s
Direct Instance: http://ec2-54-147-11-18.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 96.84ms
Throughput: 98.41 req/s
Direct Instance: http://ec2-18-215-154-58.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 103.63ms
Throughput: 91.82 req/s
Direct Instance: http://ec2-98-89-18-212.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 93.36ms
Throughput: 101.74 req/s
Direct Instance: http://ec2-34-229-138-220.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 82.74ms
Throughput: 116.05 req/s
Direct Instance: http://ec2-54-81-100-91.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 94.29ms
Throughput: 100.80 req/s
Direct Instance: http://ec2-50-19-40-223.compute-1.amazonaws.com:8000
Sending 100 requests with 10 concurrent connections...
Completed: 100/100 successful
Avg response time: 85.53ms
Throughput: 111.91 req/s

# BENCHMARKING APPLICATION LOAD BALANCER ENDPOINTS

ALB Root endpoint: http://LOG8415E-TP1-ALB-1019344157.us-east-1.elb.amazonaws.com
Sending 1000 requests with 50 concurrent connections...
Completed: 1000/1000 successful
Avg response time: 118.68ms
Throughput: 385.29 req/s
ALB Cluster1 endpoint: http://LOG8415E-TP1-ALB-1019344157.us-east-1.elb.amazonaws.com/cluster1
Sending 1000 requests with 50 concurrent connections...
Completed: 1000/1000 successful
Avg response time: 109.77ms
Throughput: 424.06 req/s
ALB Cluster2 endpoint: http://LOG8415E-TP1-ALB-1019344157.us-east-1.elb.amazonaws.com/cluster2
Sending 1000 requests with 50 concurrent connections...
Completed: 1000/1000 successful
Avg response time: 95.42ms
Throughput: 495.20 req/s

# BENCHMARKING CUSTOM LOAD BALANCER

Custom Load Balancer initialized with 9 instances
Testing custom load balancer with intelligent routing...
Benchmarking 9 instances with 50 requests...
Health check: 9/9 instances healthy
Benchmark completed:
• Total requests: 50
• Successful: 50
• Failed: 0
• Total time: 0.51s
• Throughput: 97.85 req/s
Sending 500 requests through custom load balancer...
Completed: 500/500 successful
Avg response time: 170.36ms
Throughput: 119.69 req/s

================================================================================
CUSTOM LOAD BALANCER PERFORMANCE SUMMARY
================================================================================

HEALTH STATUS:
• Total instances: 9
• Healthy instances: 9
• Health ratio: 9/9

INSTANCE PERFORMANCE:

1.  http://ec2-34-229-138-220.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 18
    Errors: 0
    Avg Response Time: 90.65ms
    Min/Max: 52.73ms / 162.06ms

2.  http://ec2-54-81-100-91.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 55
    Errors: 0
    Avg Response Time: 166.01ms
    Min/Max: 43.75ms / 357.54ms

3.  http://ec2-18-215-154-58.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 68
    Errors: 0
    Avg Response Time: 171.53ms
    Min/Max: 71.90ms / 364.48ms

4.  http://ec2-34-229-156-148.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 52
    Errors: 0
    Avg Response Time: 179.11ms
    Min/Max: 47.88ms / 339.63ms

5.  http://ec2-98-89-18-212.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 73
    Errors: 0
    Avg Response Time: 179.21ms
    Min/Max: 82.41ms / 286.36ms

6.  http://ec2-54-147-11-18.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 61
    Errors: 0
    Avg Response Time: 189.93ms
    Min/Max: 64.72ms / 358.33ms

7.  http://ec2-3-85-126-17.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 63
    Errors: 0
    Avg Response Time: 190.69ms
    Min/Max: 74.86ms / 378.18ms

8.  http://ec2-50-19-40-223.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 86
    Errors: 0
    Avg Response Time: 203.12ms
    Min/Max: 124.80ms / 355.37ms

9.  http://ec2-54-198-238-242.compute-1.amazonaws.com:8000
    Status: HEALTHY
    Requests: 74
    Errors: 0
    Avg Response Time: 235.32ms
    Min/Max: 123.77ms / 382.94ms

BEST PERFORMING INSTANCE:
• http://ec2-34-229-138-220.compute-1.amazonaws.com:8000
• Average Response Time: 90.65ms

================================================================================
Detailed results saved to: benchmark_results.json
CSV results saved to: benchmark_results.csv

================================================================================
BENCHMARK RESULTS SUMMARY
================================================================================

PERFORMANCE COMPARISON:

1.  ALB Cluster2 endpoint
    Avg Response Time: 95.42ms
    Throughput: 495.20 req/s
    Success Rate: 100.0%

2.  ALB Cluster1 endpoint
    Avg Response Time: 109.77ms
    Throughput: 424.06 req/s
    Success Rate: 100.0%

3.  ALB Root endpoint
    Avg Response Time: 118.68ms
    Throughput: 385.29 req/s
    Success Rate: 100.0%

4.  Custom Load Balancer
    Avg Response Time: 170.36ms
    Throughput: 119.69 req/s
    Success Rate: 100.0%

BEST PERFORMING CONFIGURATION:
• ALB Cluster2 endpoint
• Average Response Time: 95.42ms
• Throughput: 495.20 req/s

================================================================================
Files generated:
• benchmark_results.json (detailed results)
• benchmark_results.csv (summary for spreadsheet)
• custom_lb_stats.json (load balancer performance)
================================================================================
(venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1>
