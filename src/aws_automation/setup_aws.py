import boto3
import json
from datetime import datetime

class AWSManager:
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.project_name = 'LOG8415E-TP1'
        print(f"AWS setup initialized for {self.project_name}")

    def get_default_vpc(self):
        vpcs = self.ec2_client.describe_vpcs(
            Filters=[{'Name': 'is-default', 'Values': ['true']}]
        )
        return vpcs['Vpcs'][0]['VpcId']

    def create_security_group(self):
        try:
            groups = self.ec2_client.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [f'{self.project_name}-SG']}]
            )
            if groups['SecurityGroups']:
                return groups['SecurityGroups'][0]['GroupId']
            
            response = self.ec2_client.create_security_group(
                GroupName=f'{self.project_name}-SG',
                Description=f'Security group for {self.project_name}',
                VpcId=self.get_default_vpc()
            )
            
            sg_id = response['GroupId']
            
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[{
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }]
            )
            
            print(f"Created security group: {sg_id}")
            return sg_id
            
        except Exception as e:
            print(f"Error creating security group: {e}")
            raise

    def get_user_data_script(self, cluster_name):
        return f'''#!/bin/bash
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

    def launch_instances(self, ami_id, security_group_id):
        all_instances = []
        
        print("Launching 4 t2.large instances for cluster1...")
        response1 = self.ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=4,
            MaxCount=4,
            InstanceType='t2.large',
            SecurityGroupIds=[security_group_id],
            UserData=self.get_user_data_script('cluster1'),
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': f'{self.project_name}-Cluster1'},
                    {'Key': 'Project', 'Value': self.project_name},
                    {'Key': 'Cluster', 'Value': 'cluster1'}
                ]
            }]
        )
        
        cluster1_ids = [instance['InstanceId'] for instance in response1['Instances']]
        all_instances.extend(cluster1_ids)
        
        print("Launching 4 t2.micro instances for cluster2...")
        response2 = self.ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=4,
            MaxCount=4,
            InstanceType='t2.micro',
            SecurityGroupIds=[security_group_id],
            UserData=self.get_user_data_script('cluster2'),
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': f'{self.project_name}-Cluster2'},
                    {'Key': 'Project', 'Value': self.project_name},
                    {'Key': 'Cluster', 'Value': 'cluster2'}
                ]
            }]
        )
        
        cluster2_ids = [instance['InstanceId'] for instance in response2['Instances']]
        all_instances.extend(cluster2_ids)
        
        print(f"Launched instances: Cluster1={cluster1_ids}, Cluster2={cluster2_ids}")
        return all_instances

    def wait_for_instances(self, instance_ids):
        print("Waiting for instances to be running...")
        waiter = self.ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
        print("All instances are running!")

    def get_instance_details(self, instance_ids):
        response = self.ec2_client.describe_instances(InstanceIds=instance_ids)
        cluster1_instances = []
        cluster2_instances = []
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_data = {
                    'InstanceId': instance['InstanceId'],
                    'PublicDnsName': instance.get('PublicDnsName', ''),
                    'PublicIpAddress': instance.get('PublicIpAddress', ''),
                    'State': instance['State']['Name'],
                    'InstanceType': instance['InstanceType']
                }
                
                cluster = 'unknown'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Cluster':
                        cluster = tag['Value']
                        break
                
                instance_data['Cluster'] = cluster
                
                if cluster == 'cluster1':
                    cluster1_instances.append(instance_data)
                else:
                    cluster2_instances.append(instance_data)
        
        return cluster1_instances, cluster2_instances

    def save_deployment_info(self, cluster1_instances, cluster2_instances):
        all_instances = cluster1_instances + cluster2_instances
        
        info = {
            'timestamp': datetime.utcnow().isoformat(),
            'project': self.project_name,
            'clusters': {
                'cluster1': cluster1_instances,
                'cluster2': cluster2_instances
            },
            'total_instances': len(all_instances),
            'endpoints': {
                'cluster1': [f"http://{i['PublicDnsName']}:8000" for i in cluster1_instances if i['PublicDnsName']],
                'cluster2': [f"http://{i['PublicDnsName']}:8000" for i in cluster2_instances if i['PublicDnsName']]
            }
        }
        
        with open('deployment_info.json', 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"Saved deployment info to deployment_info.json")
        print(f"Cluster1 (t2.large): {len(cluster1_instances)} instances")
        print(f"Cluster2 (t2.micro): {len(cluster2_instances)} instances")
        
        for i, instance in enumerate(cluster1_instances, 1):
            if instance['PublicDnsName']:
                print(f"  Cluster1-{i}: http://{instance['PublicDnsName']}:8000")
        
        for i, instance in enumerate(cluster2_instances, 1):
            if instance['PublicDnsName']:
                print(f"  Cluster2-{i}: http://{instance['PublicDnsName']}:8000")

def main():
    try:
        print("Starting AWS Infrastructure Setup")
        
        manager = AWSManager()
        
        ami_id = "ami-0c02fb55956c7d316"
        
        security_group_id = manager.create_security_group()
        instance_ids = manager.launch_instances(ami_id, security_group_id)
        manager.wait_for_instances(instance_ids)
        cluster1_instances, cluster2_instances = manager.get_instance_details(instance_ids)
        manager.save_deployment_info(cluster1_instances, cluster2_instances)
        
        print("\nDeployment completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()