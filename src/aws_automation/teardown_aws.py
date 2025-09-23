#!/usr/bin/env python3
"""
AWS Infrastructure Teardown Script for LOG8415E Assignment

This script safely removes all AWS resources created by setup_aws.py:
- Terminates all EC2 instances with project tags
- Deletes security groups
- Removes Application Load Balancers and target groups
"""

import boto3
import os
import time
import json
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

class AWSInfrastructureTeardown:
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
            self.elbv2_client = self.session.client('elbv2')
            
            # Configuration
            self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            self.project_name = 'LOG8415E-TP1'
            self.security_group_name = f'{self.project_name}-SG'
            self.key_name = os.getenv('KEY_NAME', 'log8415-key')
            
            print(f"AWS Teardown Manager initialized for region: {self.region}")
            
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please check your .env file.")
            raise
        except Exception as e:
            print(f"❌ Error initializing AWS client: {e}")
            raise

    def find_project_instances(self):
        """Find all EC2 instances belonging to this project"""
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'tag:Project',
                        'Values': [self.project_name]
                    },
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running', 'pending', 'stopping', 'stopped']
                    }
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'State': instance['State']['Name'],
                        'InstanceType': instance['InstanceType'],
                        'PublicDnsName': instance.get('PublicDnsName', 'N/A'),
                        'Cluster': self.get_tag_value(instance.get('Tags', []), 'Cluster')
                    })
            
            return instances
            
        except Exception as e:
            print(f"❌ Error finding project instances: {e}")
            return []

    def get_tag_value(self, tags, key):
        """Get value of a specific tag"""
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return 'N/A'

    def terminate_instances(self, instances):
        """Terminate all project instances"""
        if not instances:
            print(" No instances found to terminate")
            return
        
        instance_ids = [instance['InstanceId'] for instance in instances]
        
        print(f"🗑️  Terminating {len(instance_ids)} instances...")
        
        # Group by cluster for reporting
        cluster1_instances = [i for i in instances if i['Cluster'] == 'cluster1']
        cluster2_instances = [i for i in instances if i['Cluster'] == 'cluster2']
        
        if cluster1_instances:
            print(f"   • Cluster1: {len(cluster1_instances)} instances")
            for instance in cluster1_instances:
                print(f"     - {instance['InstanceId']} ({instance['InstanceType']}) - {instance['State']}")
        
        if cluster2_instances:
            print(f"   • Cluster2: {len(cluster2_instances)} instances")
            for instance in cluster2_instances:
                print(f"     - {instance['InstanceId']} ({instance['InstanceType']}) - {instance['State']}")
        
        try:
            # Terminate instances
            response = self.ec2_client.terminate_instances(InstanceIds=instance_ids)
            
            print("Termination request sent for all instances")
            
            # Wait for termination
            print("Waiting for instances to terminate...")
            waiter = self.ec2_client.get_waiter('instance_terminated')
            
            try:
                waiter.wait(
                    InstanceIds=instance_ids,
                    WaiterConfig={
                        'Delay': 15,
                        'MaxAttempts': 40
                    }
                )
                print("All instances have been terminated")
                
            except Exception as e:
                print(f"  Timeout waiting for termination. Instances may still be terminating: {e}")
                
        except Exception as e:
            print(f"❌ Error terminating instances: {e}")
            raise

    def find_project_load_balancers(self):
        """Find Application Load Balancers for this project"""
        try:
            response = self.elbv2_client.describe_load_balancers()
            
            project_albs = []
            for alb in response['LoadBalancers']:
                # Check if ALB has project tag
                try:
                    tags_response = self.elbv2_client.describe_tags(
                        ResourceArns=[alb['LoadBalancerArn']]
                    )
                    
                    for tag_description in tags_response['TagDescriptions']:
                        for tag in tag_description['Tags']:
                            if tag['Key'] == 'Project' and tag['Value'] == self.project_name:
                                project_albs.append(alb)
                                break
                                
                except Exception as e:
                    print(f"  Error checking ALB tags: {e}")
                    continue
            
            return project_albs
            
        except Exception as e:
            print(f"❌ Error finding load balancers: {e}")
            return []

    def delete_load_balancers(self):
        """Delete Application Load Balancers and target groups"""
        albs = self.find_project_load_balancers()
        
        if not albs:
            print(" No load balancers found to delete")
            return
        
        for alb in albs:
            alb_name = alb['LoadBalancerName']
            alb_arn = alb['LoadBalancerArn']
            
            print(f"🗑️  Deleting load balancer: {alb_name}")
            
            try:
                # Get and delete target groups first
                response = self.elbv2_client.describe_target_groups(
                    LoadBalancerArn=alb_arn
                )
                
                for tg in response['TargetGroups']:
                    tg_name = tg['TargetGroupName']
                    tg_arn = tg['TargetGroupArn']
                    
                    print(f"   🗑️  Deleting target group: {tg_name}")
                    self.elbv2_client.delete_target_group(TargetGroupArn=tg_arn)
                
                # Delete the load balancer
                self.elbv2_client.delete_load_balancer(LoadBalancerArn=alb_arn)
                print(f"Load balancer deletion initiated: {alb_name}")
                
            except Exception as e:
                print(f"❌ Error deleting load balancer {alb_name}: {e}")

    def delete_security_groups(self):
        """Delete project security groups"""
        try:
            # Find security groups by name
            try:
                response = self.ec2_client.describe_security_groups(
                    GroupNames=[self.security_group_name]
                )
                
                for sg in response['SecurityGroups']:
                    sg_id = sg['GroupId']
                    sg_name = sg['GroupName']
                    
                    print(f"🗑️  Deleting security group: {sg_name} ({sg_id})")
                    
                    # Delete the security group
                    self.ec2_client.delete_security_group(GroupId=sg_id)
                    print(f"Security group deleted: {sg_name}")
                    
            except ClientError as e:
                if 'InvalidGroup.NotFound' in str(e):
                    print(" Security group not found (may have been deleted already)")
                else:
                    print(f"❌ Error deleting security group: {e}")
                    
        except Exception as e:
            print(f"❌ Error in security group cleanup: {e}")

    def delete_key_pairs(self):
        """Delete project key pairs"""
        try:
            # Check if key pair exists
            response = self.ec2_client.describe_key_pairs(
                KeyNames=[self.key_name]
            )
            
            print(f"🗑️  Deleting key pair: {self.key_name}")
            self.ec2_client.delete_key_pair(KeyName=self.key_name)
            print(f"Key pair deleted: {self.key_name}")
            
            # Try to remove local key file
            key_file = f"{self.key_name}.pem"
            if os.path.exists(key_file):
                os.remove(key_file)
                print(f"🗑️  Removed local key file: {key_file}")
                
        except ClientError as e:
            if 'InvalidKeyPair.NotFound' in str(e):
                print(" Key pair not found (may have been deleted already)")
            else:
                print(f"❌ Error deleting key pair: {e}")
        except Exception as e:
            print(f"❌ Error in key pair cleanup: {e}")

    def cleanup_deployment_files(self):
        """Remove local deployment files"""
        files_to_remove = ['deployment_info.json', 'alb_info.json', 'benchmark_results.json']
        
        for file_name in files_to_remove:
            try:
                if os.path.exists(file_name):
                    os.remove(file_name)
                    print(f"🗑️  Removed local file: {file_name}")
            except Exception as e:
                print(f"  Could not remove {file_name}: {e}")

    def verify_cleanup(self):
        """Verify that all resources have been cleaned up"""
        print("\n🔍 Verifying cleanup...")
        
        # Check for remaining instances
        instances = self.find_project_instances()
        if instances:
            print(f"  {len(instances)} instances still exist (may be terminating)")
            for instance in instances:
                print(f"   - {instance['InstanceId']}: {instance['State']}")
        else:
            print("No project instances found")
        
        # Check for remaining load balancers
        albs = self.find_project_load_balancers()
        if albs:
            print(f"  {len(albs)} load balancers still exist (may be deleting)")
        else:
            print("No project load balancers found")
        
        # Check for security groups
        try:
            response = self.ec2_client.describe_security_groups(
                GroupNames=[self.security_group_name]
            )
            print(f"  Security group still exists: {self.security_group_name}")
        except ClientError as e:
            if 'InvalidGroup.NotFound' in str(e):
                print("Security group has been deleted")

    def save_teardown_report(self, instances_terminated, albs_deleted):
        """Save teardown report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'project': self.project_name,
            'region': self.region,
            'instances_terminated': len(instances_terminated),
            'load_balancers_deleted': len(albs_deleted),
            'instances': instances_terminated,
            'load_balancers': [alb['LoadBalancerName'] for alb in albs_deleted]
        }
        
        output_file = 'teardown_report.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Teardown report saved to: {output_file}")

def main():
    """Main function to tear down AWS infrastructure"""
    try:
        print("🗑️  Starting AWS Infrastructure Teardown for LOG8415E Assignment")
        print("="*70)
        
        # Confirm with user
        print("  WARNING: This will permanently delete all project resources!")
        print("   • All EC2 instances will be TERMINATED")
        print("   • All data on instances will be LOST") 
        print("   • Load balancers will be DELETED")
        print("   • Security groups will be DELETED")
        
        confirm = input("\n❓ Are you sure you want to continue? (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("❌ Teardown cancelled by user")
            return
        
        # Initialize teardown manager
        teardown = AWSInfrastructureTeardown()
        
        # Find current resources
        print("\n🔍 Discovering project resources...")
        instances = teardown.find_project_instances()
        albs = teardown.find_project_load_balancers()
        
        if not instances and not albs:
            print(" No project resources found to delete")
            teardown.delete_security_groups()
            teardown.cleanup_deployment_files()
            print("\nTeardown completed - no resources were found")
            return
        
        print(f"\nRESOURCES TO DELETE:")
        print(f"   • EC2 Instances: {len(instances)}")
        print(f"   • Load Balancers: {len(albs)}")
        print(f"   • Security Groups: 1 (if exists)")
        
        # Delete load balancers first (they depend on instances)
        if albs:
            print(f"\n🗑️  STEP 1: Deleting load balancers...")
            teardown.delete_load_balancers()
            
            # Wait a moment for ALB deletion to start
            print("Waiting for load balancer deletion to complete...")
            time.sleep(30)
        
        # Terminate instances
        if instances:
            print(f"\n🗑️  STEP 2: Terminating instances...")
            teardown.terminate_instances(instances)
        
        # Delete security groups (wait for instances to terminate first)
        print(f"\n🗑️  STEP 3: Deleting security groups...")
        teardown.delete_security_groups()
        
        # Delete key pairs
        print(f"\n🗑️  STEP 4: Deleting key pairs...")
        teardown.delete_key_pairs()
        
        # Clean up local files
        print(f"\n🗑️  STEP 5: Cleaning up local files...")
        teardown.cleanup_deployment_files()
        
        # Verify cleanup
        teardown.verify_cleanup()
        
        # Save report
        teardown.save_teardown_report(instances, albs)
        
        print("\n" + "="*70)
        print("TEARDOWN COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nAll project resources have been deleted.")
        print("   You can now safely re-run setup_aws.py for a fresh deployment.")
        
    except KeyboardInterrupt:
        print("\n  Teardown interrupted by user")
        print("  Some resources may still exist - please check AWS console")
    except Exception as e:
        print(f"\n❌ Teardown failed: {e}")
        print("  Some resources may still exist - please check AWS console")
        raise

if __name__ == "__main__":
    main()