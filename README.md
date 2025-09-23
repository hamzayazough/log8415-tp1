# LOG8415E Cloud Computing Assignment - FastAPI Deployment on AWS EC2

## 📋 Overview

This project implements a complete cloud computing assignment that deploys FastAPI applications across multiple EC2 instances with load balancing and performance benchmarking.

### Assignment Components

- **AWS Infrastructure**: 9 EC2 instances (4×t2.large + 5×t2.micro)
- **Application Load Balancer (ALB)**: Path-based routing with target groups
- **Custom Load Balancer**: Response-time based intelligent routing
- **FastAPI Applications**: Auto-deployed on all instances
- **Performance Benchmarking**: Comprehensive testing with 1000+ requests

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

### Step 2: Configure AWS Credentials

Update your AWS credentials in `.env` file:

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here
AWS_DEFAULT_REGION=us-east-1
```

**Or configure via AWS CLI:**

```bash
aws configure set aws_access_key_id YOUR_ACCESS_KEY
aws configure set aws_secret_access_key YOUR_SECRET_KEY
aws configure set aws_session_token YOUR_SESSION_TOKEN
```

### Step 3: Deploy Infrastructure

```bash
# Deploy 8 EC2 instances with FastAPI applications
python src/aws_automation/setup_aws.py
```

**Expected output:**

- 4×t2.large instances (cluster1)
- 4×t2.micro instances (cluster2)
- Security group with proper firewall rules
- FastAPI apps auto-installing on all instances

### Step 4: Create Application Load Balancer

```bash
# Create ALB with path-based routing
python src/load_balancer/create_alb.py
```

**Expected output:**

- AWS Application Load Balancer
- Two target groups (cluster1-tg, cluster2-tg)
- Path routing: `/cluster1` → cluster1, `/cluster2` → cluster2

### Step 5: Run Performance Benchmarks

```bash
# Comprehensive benchmarking
python src/benchmarking/run_benchmark.py
```

**Tests performed:**

- Direct instance endpoints (100 requests each)
- ALB endpoints (1000 requests each)
- Custom load balancer (500 requests)

### Step 6: Test Custom Load Balancer

```bash
# Response-time based load balancing
python src/load_balancer/custom_lb.py
```

### Step 7: Cleanup Resources

```bash
# Delete all AWS resources to avoid charges
python src/aws_automation/teardown_aws.py
```

## 🔧 Project Structure

```
├── src/
│   ├── aws_automation/
│   │   ├── setup_aws.py          # Deploy EC2 infrastructure
│   │   └── teardown_aws.py       # Cleanup AWS resources
│   ├── load_balancer/
│   │   ├── create_alb.py         # AWS Application Load Balancer
│   │   └── custom_lb.py          # Custom response-time LB
│   ├── benchmarking/
│   │   └── run_benchmark.py      # Performance testing
│   └── fastapi/
│       ├── main.py               # FastAPI application
│       └── user_data.py          # EC2 startup script
├── requirements.txt              # Python dependencies
├── .env                         # AWS credentials (create this)
└── README.md                    # This file
```
