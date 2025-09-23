import boto3
import time
import os

class AWSTeardown:
    def __init__(self):
        """Initialize AWS clients"""
        self.ec2_client = boto3.client('ec2')
        self.elbv2_client = boto3.client('elbv2')
        self.project_name = 'LOG8415E-TP1'
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

    def delete_load_balancer(self):
        """Delete ALB and target groups"""
        try:
            albs = self.elbv2_client.describe_load_balancers(
                Names=[f'{self.project_name}-ALB']
            )
            
            if albs['LoadBalancers']:
                alb_arn = albs['LoadBalancers'][0]['LoadBalancerArn']
                print(f"Deleting ALB: {alb_arn}")
                
                self.elbv2_client.delete_load_balancer(LoadBalancerArn=alb_arn)
                
                print("Waiting for ALB deletion...")
                waiter = self.elbv2_client.get_waiter('load_balancers_deleted')
                waiter.wait(LoadBalancerArns=[alb_arn])
                print("ALB deleted")
            
        except Exception as e:
            print(f"ALB deletion error (may not exist): {e}")

    def delete_target_groups(self):
        target_group_names = [
            f'{self.project_name}-Cluster1-TG',
            f'{self.project_name}-Cluster2-TG'
        ]
        
        for tg_name in target_group_names:
            try:
                tgs = self.elbv2_client.describe_target_groups(
                    Names=[tg_name]
                )
                
                for tg in tgs['TargetGroups']:
                    tg_arn = tg['TargetGroupArn']
                    print(f"Deleting target group: {tg_name}")
                    self.elbv2_client.delete_target_group(TargetGroupArn=tg_arn)
                    print(f"Target group {tg_name} deleted")
                    
            except Exception as e:
                print(f"Target group {tg_name} deletion error (may not exist): {e}")

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

    def cleanup_files(self):
        files_to_remove = [
            'deployment_info.json',
            'alb_info.json',
            'benchmark_results.json',
            'benchmark_results.csv',
            'cloudwatch_metrics.json'
        ]
        
        for file in files_to_remove:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"Removed: {file}")
            except Exception as e:
                print(f"Could not remove {file}: {e}")

def main():
    try:
        print("Starting AWS Infrastructure Teardown")
        print("=" * 50)
        
        teardown = AWSTeardown()
        
        instance_ids = teardown.find_project_instances()
        teardown.terminate_instances(instance_ids)
        
        teardown.delete_load_balancer()
        
        teardown.delete_target_groups()
        
        print("Waiting 30 seconds before deleting security group...")
        time.sleep(30)
        teardown.delete_security_group()
        
        teardown.cleanup_files()
        
        print("\n" + "=" * 50)
        print("TEARDOWN COMPLETED SUCCESSFULLY!")
        print("All AWS resources have been removed.")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error during teardown: {e}")
        raise

if __name__ == "__main__":
    main()