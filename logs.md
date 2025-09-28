(.venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> python src/aws_automation/setup_aws.py

> > Starting AWS Infrastructure Setup
> > AWS setup initialized for LOG8415E-TP1
> > Launching 4 t2.large instances for cluster1...
> > Launching 4 t2.micro instances for cluster2...
> > Launching 4 t2.micro instances for cluster2...
> > com:8000
> > Cluster1-2: http://ec2-54-167-3-53.compute-1.amazonaws.com:8000
> > Cluster1-3: http://ec2-3-84-135-171.compute-1.amazonaws.com:8000
> > Cluster1-4: http://ec2-34-229-163-18.compute-1.amazonaws.com:8000
> > Cluster2-1: http://ec2-54-87-18-111.compute-1.amazonaws.com:8000
> > Cluster2-2: http://ec2-3-91-7-194.compute-1.amazonaws.com:8000
> > Cluster2-3: http://ec2-34-228-41-191.compute-1.amazonaws.com:8000
> > Cluster2-4: http://ec2-54-91-116-67.compute-1.amazonaws.com:8000

Deployment completed successfully!
(.venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> python src/load_balancer/create_alb.py
Starting ALB Setup
ALB Manager initialized for LOG8415E-TP1
Found Cluster1: 4 instances, Cluster2: 4 instances
Created cluster1 target group: arn:aws:elasticloadbalancing:us-east-1:654654213826:targetgroup/LOG8415E-TP1-Cluster1-TG/2a6da61a9e6a516f
Created cluster2 target group: arn:aws:elasticloadbalancing:us-east-1:654654213826:targetgroup/LOG8415E-TP1-Cluster2-TG/3df3bdfac25d4200
Registered 4 cluster1 targets
Registered 4 cluster2 targets
Created ALB: LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com
Created listener: arn:aws:elasticloadbalancing:us-east-1:654654213826:listener/app/LOG8415E-TP1-ALB/2307e16f7803ed1b/e4158a37f093be25
Created rule for /cluster1 -> cluster1 target group
Created rule for /cluster2 -> cluster2 target group
Waiting for ALB to be active...
ALB is active!
ALB endpoints:
Root: http://LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com
Cluster1: http://LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com/cluster1
Cluster2: http://LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com/cluster2
ALB info saved to alb_info.json

ALB setup completed successfully!
Test endpoints:
http://LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com/cluster1
http://LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com/cluster2
(.venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> python src/benchmarking/run_benchmark.py

Starting Simplified Benchmark for LOG8415E Assignment
Benchmark Runner initialized

# Starting Performance Benchmarks

Testing ALB Cluster1 (/cluster1):
Benchmarking ALB Cluster1: http://LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com/cluster1  
 Sending 1000 requests...
Success rate: 100.0%
Avg response time: 36.93ms
Throughput: 267.36 req/s

Testing ALB Cluster2 (/cluster2):
Benchmarking ALB Cluster2: http://LOG8415E-TP1-ALB-943597734.us-east-1.elb.amazonaws.com/cluster2  
 Sending 1000 requests...
Success rate: 100.0%
Avg response time: 35.11ms
Throughput: 280.06 req/s

Testing Direct Cluster1 Instances:
Benchmarking Cluster1 Instance 1: http://ec2-3-87-90-123.compute-1.amazonaws.com:8000
Sending 100 requests...
Success rate: 100.0%
Avg response time: 98.01ms
Throughput: 97.92 req/s
Benchmarking Cluster1 Instance 2: http://ec2-54-167-3-53.compute-1.amazonaws.com:8000
Sending 100 requests...
Success rate: 100.0%
Avg response time: 108.96ms
Throughput: 88.07 req/s

Testing Direct Cluster2 Instances:
Benchmarking Cluster2 Instance 1: http://ec2-54-87-18-111.compute-1.amazonaws.com:8000
Sending 100 requests...
Success rate: 100.0%
Avg response time: 105.42ms
Throughput: 90.78 req/s
Benchmarking Cluster2 Instance 2: http://ec2-3-91-7-194.compute-1.amazonaws.com:8000
Sending 100 requests...
Success rate: 100.0%
Avg response time: 121.13ms
Throughput: 78.94 req/s
Results saved to benchmark_results.json and benchmark_results.csv

============================================================
BENCHMARK RESULTS SUMMARY
============================================================

CLUSTER PERFORMANCE COMPARISON:
• ALB Cluster1 (t2.large) avg response: 36.93ms
• ALB Cluster1 throughput: 267.36 req/s
• ALB Cluster2 (t2.micro) avg response: 35.11ms
• ALB Cluster2 throughput: 280.06 req/s
• Direct Cluster1 avg response: 103.49ms
• Direct Cluster2 avg response: 113.28ms

PERFORMANCE WINNER: Cluster2 (t2.micro) is faster

============================================================

Benchmarking completed successfully!

(.venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1> python src/monitoring/cloudwatch_metrics.py
Starting CloudWatch Metrics Collection
CloudWatch Monitor initialized for LOG8415E-TP1
Found 8 instances to monitor
Collecting CloudWatch metrics...
Getting metrics for instance i-077630f9c3c8864b6
Getting metrics for instance i-04aea465704fc49b5
Getting metrics for instance i-0637d6c3bd3d86bbd
Getting metrics for instance i-03f10b03c9ddac40b
Getting metrics for instance i-0699881aac29b1386
Getting metrics for instance i-004462457b5c4b495
Getting metrics for instance i-028b9c6e352f7aa53
Getting metrics for instance i-0158e6e1ce118191e
CloudWatch metrics saved to cloudwatch_metrics.json

============================================================
CLOUDWATCH METRICS SUMMARY
============================================================

OVERALL PERFORMANCE:
• Total instances monitored: 5
• Average CPU utilization: 3.64%
• Total ALB requests: 0
• Average response time: 0.000s

INSTANCE DETAILS:
i-077630f9c3c8864b6:
CPU: 0.00%
Network In: 360.0 bytes
Network Out: 360.0 bytes
i-04aea465704fc49b5:
CPU: 4.85%
Network In: 360.0 bytes
Network Out: 360.0 bytes
i-0637d6c3bd3d86bbd:
CPU: 3.12%
Network In: 360.0 bytes
Network Out: 360.0 bytes
i-03f10b03c9ddac40b:
CPU: 4.45%
Network In: 270.0 bytes
Network Out: 360.0 bytes
i-0699881aac29b1386:
CPU: 0.00%
Network In: 360.0 bytes
Network Out: 360.0 bytes
i-004462457b5c4b495:
CPU: 2.80%
Network In: 360.0 bytes
Network Out: 360.0 bytes
i-028b9c6e352f7aa53:
CPU: 0.00%
Network In: 782.0 bytes
Network Out: 959.0 bytes
i-0158e6e1ce118191e:
CPU: 2.99%
Network In: 360.0 bytes
Network Out: 360.0 bytes

============================================================

CloudWatch monitoring completed!
(.venv) PS C:\Users\hamza\Documents\ecole\log8415\log8415-tp1>
