import boto3

class AWSManager:
    def __init__(self, project_name):
        self.ec2_client = boto3.client('ec2')
        self.project_name = project_name
        print(f"AWS setup initialized for {self.project_name}")

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
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]

            if can_ssh:
                ip_permissions.append({
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                })
            
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=ip_permissions
            )
            
            print(f"Created security group: {sg_id}")
            return sg_id
            
        except Exception as e:
            print(f"Error creating security group: {e}")
            raise
    
    def launch_instance(self, ami_id, security_group_id, instance_name, user_data, key_name='key'):
        print("Launching a t2.large instance")
        response = self.ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.large',
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
        
        instance_id = response['Instances'][0]['InstanceId']

        print(f"Launched instance: {instance_id}")
        return instance_id

    def wait_for_instances(self, instance_ids):
        print("Waiting for instances to be running...")
        waiter = self.ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
        print("All instances are running!")