import boto3
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from constants.aws_automatisation_constants import ALLOW_HTTP_FROM_ANYWHERE, ALLOW_APP_PORT_8000_FROM_ANYWHERE, ALLOW_SSH_FROM_ANYWHERE

class AWSManager:
    def __init__(self, project_name, create_bucket=False):
        self.ec2_client = boto3.client('ec2')
        self.new_ec2 = boto3.resource('ec2')
        self.project_name = project_name
        self.s3 = None
        self.bucket_name = None
        
        if create_bucket:
            self.create_bucket()
            
        print(f"AWS setup initialized for {self.project_name}")

    def create_bucket(self):
        if self.s3 is None:
            self.s3 = boto3.resource('s3')
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()["Account"]
            self.bucket_name = f'{self.project_name}-{account_id}-bucket'
        
        try:
            self.s3.meta.client.head_bucket(Bucket=self.bucket_name)
            print(f"Using existing bucket: {self.bucket_name}")
        except:
            self.s3.create_bucket(Bucket=self.bucket_name)
            print(f"Created new bucket: {self.bucket_name}")

    def get_default_vpc(self):
        vpcs = self.ec2_client.describe_vpcs(
            Filters=[{'Name': 'is-default', 'Values': ['true']}]
        )
        return vpcs['Vpcs'][0]['VpcId']

    def create_security_group(self, can_ssh=False):
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
            
            ip_permissions = [
                ALLOW_HTTP_FROM_ANYWHERE,
                ALLOW_APP_PORT_8000_FROM_ANYWHERE
            ]
            
            ## If we need connection to EC2 via SSH
            if can_ssh:
                ip_permissions.append(ALLOW_SSH_FROM_ANYWHERE)
            
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=ip_permissions
            )
            
            print(f"Created security group: {sg_id}")
            return sg_id
            
        except Exception as e:
            print(f"Error creating security group: {e}")
            raise
    
    # ami -> Amazon Machine Image and its purpose is to define the OS and pre-installed software in our new VM
    # key_name -> The name of the key pair to use for SSH access
    def launch_instance(self, ami_id, security_group_id, instance_name, user_data, key_name, instance_type='t2.large'):
        print(f'Launching a {instance_type}  instance')
        response = self.ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            UserData=user_data,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': f'{instance_name}'},
                    {'Key': 'Project', 'Value': self.project_name},
                ]
            }]
        )
        
        # Returning instance Id
        return response['Instances'][0]['InstanceId']
    
    def upload_file(self, file_name: str, file_path: str):
        if self.s3 is None:
            print("S3 not initialized. Creating bucket...")
            self.create_bucket()
            
        try:
            self.s3.Object(self.bucket_name, file_name).load()
            print(f'File {file_name} already exists')
        except:
            print(f'Upload file {file_name}')
            self.s3.Object(self.bucket_name, file_name).put(Body=open(file_path, 'rb'))
    
    def get_public_ip(self, instance_id):
        return self.new_ec2.Instance(instance_id).public_ip_address


    def wait_for_instances(self, instance_ids):
        print("Waiting for instances to be running...")
        waiter = self.ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
        print("All instances are running!")