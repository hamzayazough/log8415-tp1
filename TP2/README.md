# LOG8415E TP2

## Overview

This assignment sees the implementation of the MapReduce architecture into our previously contructed AWS cloud deployement infrastructure. A simple MapReduce program will be written to implement a "People You Might Know" friendship recommendation algorithmn.

### Assignment Components

-   **AWS Infrastructure**: 1 EC2 instance (t2.large)
-   **Elastic Map Reduce (EMR)**: Big data processing (MapReduce)
-   **Apache Spark**: Open-source distributed system with in-memory processing (streaming)
-   **Apache Hadoop**: Open-source distributed system on disk processing (batch)

## Quick Start

### Step 1: Configure AWS Credentials

```bash
aws configure
```

Enter your AWS credentials when prompted:

-   AWS Access Key ID
-   AWS Secret Access Key
-   Default region: `us-east-1`
-   Default output format: `json`

```bash
aws configure set aws_session_token <your token here>
```

### Step 2: Configure SSH Key Pairs

**Important Notes:**

-   **For MapReduce functionality**: You MUST have a key-pair named "tp2"
-   **Rename your .pem file to tp2.pem** and place it in the root of the project directory
-   The tp2.pem file is crucial for SSH connections between EC2 instances in the MapReduce deployment

### Step 3: Run Complete Deployment

**Linux/Mac:**

```bash
./run_all.sh
```

The script will automatically:

1. run the map reduce experiment
2. run word count tests
