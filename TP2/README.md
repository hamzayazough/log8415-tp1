# LOG8415E TP2

## Overview

This assignment sees the implementation of the MapReduce architecture into our previously contructed AWS cloud deployement infrastructure. A simple MapReduce program will be written to implement a "People You Might Know" friendship recommendation algorithmn.

### Assignment Components

- **AWS Infrastructure**: 1 EC2 instance (t2.large)
- **Elastic Map Reduce (EMR)**: Big data processing (MapReduce)
- **Apache Spark**: Open-source distributed system with in-memory processing (streaming)
- **Apache Hadoop**: Open-source distributed system on disk processing (batch)

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

important note: you MUST have a key-pair setup with the key name being "key". The key.pem file MUST be in the same folder as this script.

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