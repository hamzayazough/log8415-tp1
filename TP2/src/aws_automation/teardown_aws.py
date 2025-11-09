import boto3

class AWSTeardown:
    def __init__(self, project_name):
        self.ec2_client = boto3.client('ec2')
        self.s3 = boto3.resource('s3')
        self.project_name = project_name
        self.bucket_name = f'{self.project_name}-bucket'
        print(f"AWS Teardown initialized for {self.project_name}")

    def find_project_instances(self):
        """Find project EC2 instances"""
        response = self.ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Project', 'Values': [self.project_name]},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending']}
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        print(f"Found {len(instance_ids)} instances to terminate")
        return instance_ids

    def terminate_instances(self, instance_ids):
        """Terminate EC2 instances"""
        if not instance_ids:
            print("No instances to terminate")
            return
        
        print(f"Terminating {len(instance_ids)} instances...")
        self.ec2_client.terminate_instances(InstanceIds=instance_ids)
        
        print("Waiting for instances to terminate...")
        waiter = self.ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids)
        print("All instances terminated")

    def delete_security_group(self):
        try:
            groups = self.ec2_client.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [f'{self.project_name}-SG']}]
            )
            
            if groups['SecurityGroups']:
                sg_id = groups['SecurityGroups'][0]['GroupId']
                print(f"Deleting security group: {sg_id}")
                self.ec2_client.delete_security_group(GroupId=sg_id)
                print("Security group deleted")
                
        except Exception as e:
            print(f"Security group deletion error (may be in use): {e}")

    def delete_s3_bucket(self):
        try:
            bucket = self.s3.Bucket(self.bucket_name)
            
            print(f"Deleting all objects in bucket: {self.bucket_name}")
            bucket.objects.all().delete()
            print(f"Deleting bucket: {self.bucket_name}")
            bucket.delete()
            print("S3 bucket deleted successfully")
            
        except Exception as e:
            print(f"S3 bucket deletion error: {e}")