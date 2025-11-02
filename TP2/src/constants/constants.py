USER_DATA_SCRIPT = '''#!/bin/bash
yum update -y
yum install -y python3 python3-pip
pip3 install fastapi uvicorn

mkdir -p /home/ec2-user/app
cd /home/ec2-user/app

cat > main.py << 'EOF'
from fastapi import FastAPI
import subprocess

app = FastAPI()

def get_instance_id():
    try:
        result = subprocess.run(['curl', '-s', 'http://169.254.169.254/latest/meta-data/instance-id'], 
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    except:
        return 'unknown'

@app.get("/")
async def root():
    instance_id = get_instance_id()
    return {{"message": f"Instance {{instance_id}} is responding now!", "instance_id": instance_id, "cluster": "{cluster_name}"}}

@app.get("/health")
async def health():
    return {{"status": "healthy", "instance_id": get_instance_id(), "cluster": "{cluster_name}"}}

@app.get("/cluster1")
async def cluster1():
    instance_id = get_instance_id()
    return {{"message": f"Cluster1 - Instance {{instance_id}} is responding now!", "instance_id": instance_id, "cluster": "cluster1"}}

@app.get("/cluster2")
async def cluster2():
    instance_id = get_instance_id()
    return {{"message": f"Cluster2 - Instance {{instance_id}} is responding now!", "instance_id": instance_id, "cluster": "cluster2"}}
EOF

chown -R ec2-user:ec2-user /home/ec2-user/app
cd /home/ec2-user/app
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
'''

PROJECT_NAME = 'LOG8415E-TP2'
DEFAULT_AMI_ID = "ami-0c02fb55956c7d316"
