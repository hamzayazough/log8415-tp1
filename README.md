# LOG8415E Cloud Computing Assignment - Simplified FastAPI Deployment on AWS EC2

## 📋 Overview

This project implements a simplified cloud computing assignment that deploys FastAPI applications across multiple EC2 instances with load balancing and performance monitoring using AWS CloudWatch.

### Assignment Components

- **AWS Infrastructure**: 8 EC2 instances (t2.micro)
- **Application Load Balancer (ALB)**: Basic HTTP routing
- **CloudWatch Monitoring**: AWS native metrics collection
- **FastAPI Applications**: Auto-deployed on all instances
- **Performance Benchmarking**: Essential testing functionality

## Quick Start Guide

### Prerequisites

1. **AWS Academy Lab Access** with valid credentials
2. **Python 3.11+** installed
3. **Git** for cloning the repository

### Step 1: Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd log8415-tp1

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Single-Command Deployment (Recommended)

For complete automated deployment, use one of these single-command runners:

**Windows PowerShell:**

```powershell
.\run_all.ps1
```

**Linux/Mac Bash:**

```bash
./run_all.sh
```

These scripts will automatically:

1. Deploy 8 EC2 instances (4×t2.large + 4×t2.micro)
2. Create ALB with cluster routing
3. Run performance benchmarks
4. Collect CloudWatch metrics
5. Generate all result files

**Skip to Step 7 if using single-command deployment.**

### Step 3: Manual Deployment (Alternative)

```bash
# Deploy 8 EC2 instances with FastAPI applications
python src/aws_automation/setup_aws.py
```

**Expected output:**

- 4×t2.large + 4×t2.micro instances
- Security group with HTTP access on port 8000
- FastAPI apps auto-installing on all instances

### Step 4: Create Application Load Balancer

```bash
# Create ALB with basic routing
python src/load_balancer/create_alb.py
```

**Expected output:**

- AWS Application Load Balancer
- Target group with all instances
- HTTP listener on port 80

### Step 5: Run Performance Benchmarks

```bash
# Simplified benchmarking
python src/benchmarking/run_benchmark.py
```

**Tests performed:**

- ALB endpoint (1000 requests)
- Direct instance endpoints (100 requests each, sample of 3)

### Step 6: Monitor with CloudWatch

```bash
# Collect CloudWatch metrics
python src/monitoring/cloudwatch_metrics.py
```

**Metrics collected:**

- EC2 CPU utilization
- Network in/out
- ALB request count and response times

### Step 7: Cleanup Resources

```bash
# Delete all AWS resources to avoid charges
python src/aws_automation/teardown_aws.py
```

## 🔧 Project Structure

```
├── src/
│   ├── aws_automation/
│   │   ├── setup_aws.py          # Deploy EC2 infrastructure (< 200 lines)
│   │   └── teardown_aws.py       # Cleanup AWS resources
│   ├── load_balancer/
│   │   └── create_alb.py         # Simple ALB setup (< 200 lines)
│   ├── benchmarking/
│   │   └── run_benchmark.py      # Basic performance testing (< 200 lines)
│   └── monitoring/
│       └── cloudwatch_metrics.py # CloudWatch metrics collection (< 200 lines)
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

## 📊 Key Features

### Simplified Architecture

- **Minimal EC2 Deployment**: Essential instance setup only
- **Basic ALB**: Standard load balancer without complex routing
- **CloudWatch Integration**: Native AWS monitoring instead of custom solutions
- **Streamlined Benchmarking**: Core performance testing functionality

### CloudWatch Monitoring

Instead of a custom load balancer, this implementation uses AWS CloudWatch to:

- Monitor EC2 instance performance (CPU, network)
- Track ALB metrics (request count, response times)
- Analyze healthy host counts
- Provide native AWS monitoring capabilities

### File Size Optimization

All core files are under 200 lines of code:

- `setup_aws.py`: ~165 lines
- `create_alb.py`: ~145 lines
- `run_benchmark.py`: ~185 lines
- `cloudwatch_metrics.py`: ~195 lines

## 🚀 Usage Examples

### Basic Testing Workflow

```bash
# 1. Deploy infrastructure
python src/aws_automation/setup_aws.py

# 2. Create load balancer
python src/load_balancer/create_alb.py

# 3. Run benchmarks
python src/benchmarking/run_benchmark.py

# 4. Monitor with CloudWatch
python src/monitoring/cloudwatch_metrics.py

# 5. Cleanup
python src/aws_automation/teardown_aws.py
```

### Output Files

- `deployment_info.json`: Instance details and endpoints
- `alb_info.json`: Load balancer configuration
- `benchmark_results.json`: Performance test results
- `benchmark_results.csv`: Summary in CSV format
- `cloudwatch_metrics.json`: AWS monitoring data

## 📈 Monitoring and Analysis

The CloudWatch monitoring script provides:

- Real-time performance metrics
- Instance-level CPU and network usage
- ALB request patterns and response times
- Automated analysis and reporting

This approach leverages AWS native monitoring capabilities for production-ready observability.

## 🔧 Requirements

### Python Dependencies

```
boto3>=1.26.0
aiohttp>=3.8.0
```

### AWS Permissions Required

- EC2: Create/manage instances, security groups
- ELB: Create/manage load balancers and target groups
- CloudWatch: Read metrics data
- VPC: Access default VPC and subnets
