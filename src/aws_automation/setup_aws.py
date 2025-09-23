
import boto3
import os
import time
import json
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

class AWSInfrastructureManager:
    def __init__(self):
        """Initialize AWS clients and configuration"""
        try:
            # Load AWS credentials from environment
            self.session = boto3.Session(
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
            
            self.ec2_client = self.session.client('ec2')
            self.ec2_resource = self.session.resource('ec2')
            
            # Configuration
            self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            self.project_name = 'LOG8415E-TP1'
            self.security_group_name = f'{self.project_name}-SG'
            self.key_name = os.getenv('KEY_NAME', 'log8415-key')
            
            # Instance configuration (AWS Academy limit: 9 instances total)
            self.cluster1_config = {
                'instance_type': 't2.large',
                'count': 4,
                'cluster_name': 'cluster1'
            }
            
            self.cluster2_config = {
                'instance_type': 't2.micro', 
                'count': 4,  # Reduced to 4 to allow for load balancer instance (8 + 1 = 9 total)
                'cluster_name': 'cluster2'
            }
            
            print(f" AWS Infrastructure Manager initialized for region: {self.region}")
            
        except NoCredentialsError:
            print("AWS credentials not found. Please check your .env file.")
            raise
        except Exception as e:
            print(f"Error initializing AWS client: {e}")
            raise

    def ensure_key_pair(self):
        """Skip key pair creation for AWS Academy environment"""
        print(" Skipping key pair creation (AWS Academy restriction)")
        print(" Instances will be launched without key pairs (no SSH access)")
        return None  # Return None to indicate no key pair

    def get_latest_amazon_linux_ami(self):
        """Use a well-known Amazon Linux 2 AMI ID for AWS Academy"""
        # Common Amazon Linux 2 AMI for us-east-1 (AWS Academy standard)
        ami_id = "ami-0c02fb55956c7d316"  # Amazon Linux 2 AMI (HVM) - Kernel 5.10
        print(f" Using Amazon Linux 2 AMI: {ami_id} (AWS Academy standard)")
        return ami_id

    def get_default_vpc(self):
        """Get the default VPC ID"""
        try:
            response = self.ec2_client.describe_vpcs(
                Filters=[{"Name": "isDefault", "Values": ["true"]}]
            )
            
            if response['Vpcs']:
                vpc_id = response['Vpcs'][0]['VpcId']
                print(f" Using default VPC: {vpc_id}")
                return vpc_id
            else:
                # If no default VPC, get the first available VPC
                response = self.ec2_client.describe_vpcs()
                if response['Vpcs']:
                    vpc_id = response['Vpcs'][0]['VpcId']
                    print(f" Using VPC: {vpc_id} (no default VPC found)")
                    return vpc_id
                else:
                    raise Exception("No VPC found")
                    
        except Exception as e:
            print(f"Error getting VPC: {e}")
            raise

    def create_security_group(self):
        """Create security group with SSH and FastAPI access"""
        try:
            # Get default VPC
            vpc_id = self.get_default_vpc()
            
            # Check if security group already exists
            try:
                response = self.ec2_client.describe_security_groups(
                    GroupNames=[self.security_group_name]
                )
                sg_id = response['SecurityGroups'][0]['GroupId']
                print(f" Security group already exists: {sg_id}")
                return sg_id
            except ClientError as e:
                if 'InvalidGroup.NotFound' not in str(e):
                    raise

            # Create new security group
            print(f"Creating security group: {self.security_group_name}")
            
            response = self.ec2_client.create_security_group(
                GroupName=self.security_group_name,
                Description=f'Security group for {self.project_name} - SSH and FastAPI access',
                VpcId=vpc_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'security-group',
                        'Tags': [
                            {'Key': 'Name', 'Value': self.security_group_name},
                            {'Key': 'Project', 'Value': self.project_name}
                        ]
                    }
                ]
            )
            
            sg_id = response['GroupId']
            
            # Add inbound rules
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 8000,
                        'ToPort': 8000,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'FastAPI access'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP access for ALB'}]
                    }
                ]
            )
            
            print(f" Security group created: {sg_id}")
            return sg_id
            
        except Exception as e:
            print(f"Error creating security group: {e}")
            raise

    def get_user_data_script(self, cluster_name):
        """Generate user data script for EC2 instances"""
        user_data = f'''#!/bin/bash
# LOG8415E Assignment - FastAPI Auto-Install Script
# Cluster: {cluster_name}

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting user data script for {cluster_name} at $(date)"

# Update system
yum update -y

# Install Python 3 and pip
yum install -y python3 python3-pip curl

# Create app directory
mkdir -p /home/ec2-user/app
cd /home/ec2-user/app

# Create the FastAPI application
cat > main.py << 'EOF'
import os
import subprocess
from fastapi import FastAPI
from datetime import datetime
import uvicorn

app = FastAPI(title="LOG8415E FastAPI App", version="1.0.0")

def get_instance_id():
    try:
        result = subprocess.run([
            'curl', '-s', 
            'http://169.254.169.254/latest/meta-data/instance-id'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except:
        pass
    
    return os.environ.get('INSTANCE_ID', 'unknown')

def get_cluster_info():
    return "{cluster_name}"

@app.get("/")
async def root():
    instance_id = get_instance_id()
    cluster = get_cluster_info()
    timestamp = datetime.utcnow().isoformat()
    
    message = f"Instance {{instance_id}} is responding now!"
    
    return {{
        "message": message,
        "instance_id": instance_id,
        "cluster": cluster,
        "timestamp": timestamp
    }}

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "instance_id": get_instance_id()}}

@app.get("/cluster1")
async def cluster1():
    instance_id = get_instance_id()
    timestamp = datetime.utcnow().isoformat()
    
    return {{
        "message": f"Cluster1 - Instance {{instance_id}} is responding now!",
        "instance_id": instance_id,
        "cluster": "cluster1",
        "timestamp": timestamp
    }}

@app.get("/cluster2") 
async def cluster2():
    instance_id = get_instance_id()
    timestamp = datetime.utcnow().isoformat()
    
    return {{
        "message": f"Cluster2 - Instance {{instance_id}} is responding now!",
        "instance_id": instance_id,
        "cluster": "cluster2", 
        "timestamp": timestamp
    }}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
EOF

# Install FastAPI and dependencies
pip3 install fastapi uvicorn

# Create systemd service for auto-start
cat > /etc/systemd/system/fastapi-app.service << 'EOF'
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/app
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=3
Environment=CLUSTER={cluster_name}

[Install]
WantedBy=multi-user.target
EOF

# Set proper ownership
chown -R ec2-user:ec2-user /home/ec2-user/app

# Enable and start the service
systemctl daemon-reload
systemctl enable fastapi-app
systemctl start fastapi-app

# Wait a moment for the service to start
sleep 10

# Check service status
systemctl status fastapi-app

echo "User data script completed for {cluster_name} at $(date)"
'''
        
        return user_data

    def launch_instances(self, ami_id, security_group_id):
        """Launch EC2 instances for both clusters"""
        all_instances = []
        
        # Launch cluster1 instances (t2.large)
        print(f"Launching {self.cluster1_config['count']} {self.cluster1_config['instance_type']} instances for {self.cluster1_config['cluster_name']}")
        
        try:
            cluster1_response = self.ec2_client.run_instances(
                ImageId=ami_id,
                MinCount=self.cluster1_config['count'],
                MaxCount=self.cluster1_config['count'],
                InstanceType=self.cluster1_config['instance_type'],
                SecurityGroupIds=[security_group_id],
                UserData=self.get_user_data_script(self.cluster1_config['cluster_name']),
                MetadataOptions={
                    'HttpTokens': 'optional',  # Allow IMDSv1 for compatibility
                    'HttpPutResponseHopLimit': 2
                },
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': f"{self.project_name}-{self.cluster1_config['cluster_name']}"},
                            {'Key': 'Project', 'Value': self.project_name},
                            {'Key': 'Cluster', 'Value': self.cluster1_config['cluster_name']},
                            {'Key': 'InstanceType', 'Value': self.cluster1_config['instance_type']}
                        ]
                    }
                ]
            )
            
            cluster1_instances = [instance['InstanceId'] for instance in cluster1_response['Instances']]
            all_instances.extend(cluster1_instances)
            print(f" Cluster1 instances launched: {cluster1_instances}")
            
        except Exception as e:
            print(f"Error launching cluster1 instances: {e}")
            raise

        print(f"Launching {self.cluster2_config['count']} {self.cluster2_config['instance_type']} instances for {self.cluster2_config['cluster_name']}")
        
        try:
            cluster2_response = self.ec2_client.run_instances(
                ImageId=ami_id,
                MinCount=self.cluster2_config['count'],
                MaxCount=self.cluster2_config['count'],
                InstanceType=self.cluster2_config['instance_type'],
                SecurityGroupIds=[security_group_id],
                UserData=self.get_user_data_script(self.cluster2_config['cluster_name']),
                MetadataOptions={
                    'HttpTokens': 'optional',
                    'HttpPutResponseHopLimit': 2
                },
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': f"{self.project_name}-{self.cluster2_config['cluster_name']}"},
                            {'Key': 'Project', 'Value': self.project_name},
                            {'Key': 'Cluster', 'Value': self.cluster2_config['cluster_name']},
                            {'Key': 'InstanceType', 'Value': self.cluster2_config['instance_type']}
                        ]
                    }
                ]
            )
            
            cluster2_instances = [instance['InstanceId'] for instance in cluster2_response['Instances']]
            all_instances.extend(cluster2_instances)
            print(f" Cluster2 instances launched: {cluster2_instances}")
            
        except Exception as e:
            print(f"Error launching cluster2 instances: {e}")
            raise

        return all_instances

    def wait_for_instances(self, instance_ids):
        """Wait for all instances to be running"""
        print(f"Waiting for {len(instance_ids)} instances to be running...")
        
        waiter = self.ec2_client.get_waiter('instance_running')
        
        try:
            waiter.wait(
                InstanceIds=instance_ids,
                WaiterConfig={
                    'Delay': 15,
                    'MaxAttempts': 40
                }
            )
            print(" All instances are now running!")
            
        except Exception as e:
            print(f"  Timeout waiting for instances. Some may still be starting: {e}")

    def get_instance_details(self, instance_ids):
        """Get detailed information about instances"""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=instance_ids)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_info = {
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'PublicDnsName': instance.get('PublicDnsName', 'N/A'),
                        'PublicIpAddress': instance.get('PublicIpAddress', 'N/A'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                        'Cluster': 'N/A'
                    }
                    
                    # Get cluster info from tags
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Cluster':
                            instance_info['Cluster'] = tag['Value']
                            break
                    
                    instances.append(instance_info)
            
            return instances
            
        except Exception as e:
            print(f"Error getting instance details: {e}")
            return []

    def save_deployment_info(self, instances):
        """Save deployment information to JSON file"""
        deployment_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'project': self.project_name,
            'region': self.region,
            'total_instances': len(instances),
            'clusters': {
                'cluster1': [],
                'cluster2': []
            },
            'endpoints': []
        }
        
        for instance in instances:
            cluster = instance['Cluster']
            if cluster in deployment_info['clusters']:
                deployment_info['clusters'][cluster].append(instance)
            
            if instance['PublicDnsName'] != 'N/A':
                deployment_info['endpoints'].append(f"http://{instance['PublicDnsName']}:8000")
        
        # Save to file
        output_file = 'deployment_info.json'
        with open(output_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"Deployment information saved to: {output_file}")
        return deployment_info

    def print_deployment_summary(self, instances):
        """Print a summary of the deployment"""
        print("\n" + "="*80)
        print("DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        cluster1_instances = [i for i in instances if i['Cluster'] == 'cluster1']
        cluster2_instances = [i for i in instances if i['Cluster'] == 'cluster2']
        
        print(f"\nDEPLOYMENT SUMMARY:")
        print(f"   • Total Instances: {len(instances)}")
        print(f"   • Cluster1 (t2.large): {len(cluster1_instances)} instances")
        print(f"   • Cluster2 (t2.micro): {len(cluster2_instances)} instances")
        print(f"   • Region: {self.region}")
        
        print(f"\nCLUSTER1 ENDPOINTS ({len(cluster1_instances)} instances):")
        for i, instance in enumerate(cluster1_instances, 1):
            if instance['PublicDnsName'] != 'N/A':
                print(f"   {i}. http://{instance['PublicDnsName']}:8000")
                print(f"      Instance ID: {instance['InstanceId']}")
                print(f"      Public IP: {instance['PublicIpAddress']}")
        
        print(f"\nCLUSTER2 ENDPOINTS ({len(cluster2_instances)} instances):")
        for i, instance in enumerate(cluster2_instances, 1):
            if instance['PublicDnsName'] != 'N/A':
                print(f"   {i}. http://{instance['PublicDnsName']}:8000")
                print(f"      Instance ID: {instance['InstanceId']}")
                print(f"      Public IP: {instance['PublicIpAddress']}")
        

def main():
    try:
        print("Starting AWS Infrastructure Setup for LOG8415E Assignment")
        print("="*60)
        
        manager = AWSInfrastructureManager()
        manager.ensure_key_pair()
        ami_id = manager.get_latest_amazon_linux_ami()
        security_group_id = manager.create_security_group()
        instance_ids = manager.launch_instances(ami_id, security_group_id)
        manager.wait_for_instances(instance_ids)
        instances = manager.get_instance_details(instance_ids)
        manager.save_deployment_info(instances)
        manager.print_deployment_summary(instances)
        
    except KeyboardInterrupt:
        print("\n  Setup interrupted by user")
    except Exception as e:
        print(f"\nSetup failed: {e}")
        raise

if __name__ == "__main__":
    main()