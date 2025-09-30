# LOG8415E TP1

## Overview

This project implements a simplified cloud computing assignment that deploys FastAPI applications across multiple EC2 instances with load balancing and performance monitoring using AWS CloudWatch.

### Assignment Components

- **AWS Infrastructure**: 8 EC2 instances (4×t2.large + 4×t2.micro)
- **Application Load Balancer (ALB)**: Path-based routing (/cluster1, /cluster2)
- **CloudWatch Monitoring**: AWS native metrics collection
- **FastAPI Applications**: Auto-deployed on all instances
- **Performance Benchmarking**: Comprehensive testing functionality

## Quick Start

### Step 1: Configure AWS Credentials

```bash
aws configure
```

Enter your AWS credentials when prompted:

- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1`
- Default output format: `json`

```bash
aws configure set aws_session_token <your token here>
```

### Step 2: Run Complete Deployment

**Windows:**

```powershell
.\run_all.ps1
```

**Linux/Mac:**

```bash
./run_all.sh
```

The script will automatically:

1. Deploy 8 EC2 instances (4×t2.large + 4×t2.micro)
2. Create ALB with cluster routing
3. Wait for FastAPI apps to start
4. Run performance benchmarks
5. Collect CloudWatch metrics

## What Gets Deployed

- **Cluster1**: 4×t2.large instances accessible via `/cluster1`
- **Cluster2**: 4×t2.micro instances accessible via `/cluster2`
- **Load Balancer**: AWS ALB with path-based routing
- **Security Group**: HTTP access on port 8000
- **FastAPI Apps**: Auto-deployed with cluster identification

## Generated Files

After completion, you'll have:

- `deployment_info.json` - Instance details and endpoints
- `alb_info.json` - Load balancer configuration
- `benchmark_results.csv` - Performance test results
- `cloudwatch_metrics.json` - AWS monitoring data

## Cleanup

When finished testing:

```bash
python src/aws_automation/teardown_aws.py
```

## Manual Setup

If you prefer manual steps:

1. Create virtual environment: `python -m venv .venv`
2. Activate: `.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (Linux/Mac)
3. Install dependencies: `pip install -r requirements.txt`
4. Run individual scripts in order:
   - `python src/aws_automation/setup_aws.py`
   - `python src/load_balancer/create_alb.py`
   - `python src/benchmarking/run_benchmark.py`
   - `python src/monitoring/cloudwatch_metrics.py`
