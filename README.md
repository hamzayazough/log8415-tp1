# LOG8415E Assignment 1 - Load Balancer From Scratch

## Project Structure

```
.
├── src/                    # FastAPI application source code
├── scripts/               # AWS automation scripts
├── benchmarks/           # Benchmarking tools and scripts
├── load_balancer/        # Custom load balancer implementation
├── docs/                 # Documentation and reports
└── README.md             # This file
```

## Overview

This project implements a custom load balancer for AWS EC2 instances using:

- 8 EC2 instances (4 t2.micro + 4 t2.large) for clusters
- 1 additional instance for the custom load balancer (9 total - AWS Educate limit)
- Two clusters with different instance types
- FastAPI application deployment
- Custom load balancer with response time monitoring
- Comprehensive benchmarking and performance analysis

## Getting Started

(Instructions will be added as we develop each component)
