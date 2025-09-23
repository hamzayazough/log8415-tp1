#!/usr/bin/env python3
"""
Application Load Balancer Setup Script for LOG8415E Assignment

This script creates:
- Application Load Balancer (ALB)
- Two target groups: cluster1-tg (t2.large) and cluster2-tg (t2.micro)
- Path-based routing rules: /cluster1 → cluster1-tg, /cluster2 → cluster2-tg
- Health checks for all target groups
"""

import boto3
import os
import time
import json
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

class ALBManager:
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
            self.alb_name = f'{self.project_name}-ALB'
            self.security_group_name = f'{self.project_name}-SG'
            
            print(f"ALB Manager initialized for region: {self.region}")
            
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please check your .env file.")
            raise
        except Exception as e:
            print(f"❌ Error initializing AWS client: {e}")
            raise

    def get_project_instances(self):
        """Get all project instances grouped by cluster"""
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'tag:Project',
                        'Values': [self.project_name]
                    },
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running']
                    }
                ]
            )
            
            cluster1_instances = []
            cluster2_instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_info = {
                        'InstanceId': instance['InstanceId'],
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'PublicDnsName': instance.get('PublicDnsName', 'N/A'),
                        'PublicIpAddress': instance.get('PublicIpAddress', 'N/A')
                    }
                    
                    # Get cluster from tags
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Cluster':
                            if tag['Value'] == 'cluster1':
                                cluster1_instances.append(instance_info)
                            elif tag['Value'] == 'cluster2':
                                cluster2_instances.append(instance_info)
                            break
            
            print(f"Found {len(cluster1_instances)} cluster1 instances and {len(cluster2_instances)} cluster2 instances")
            return cluster1_instances, cluster2_instances
            
        except Exception as e:
            print(f"❌ Error getting project instances: {e}")
            raise

    def get_default_vpc_and_subnets(self):
        """Get default VPC and its subnets"""
        try:
            # Get default VPC
            vpc_response = self.ec2_client.describe_vpcs(
                Filters=[{'Name': 'isDefault', 'Values': ['true']}]
            )
            
            if not vpc_response['Vpcs']:
                raise Exception("No default VPC found")
            
            vpc_id = vpc_response['Vpcs'][0]['VpcId']
            print(f"Using default VPC: {vpc_id}")
            
            # Get subnets in default VPC
            subnet_response = self.ec2_client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            subnet_ids = [subnet['SubnetId'] for subnet in subnet_response['Subnets']]
            
            if len(subnet_ids) < 2:
                raise Exception("Need at least 2 subnets for ALB")
            
            print(f"Using subnets: {subnet_ids}")
            return vpc_id, subnet_ids
            
        except Exception as e:
            print(f"❌ Error getting VPC/subnets: {e}")
            raise

    def get_security_group_id(self):
        """Get the project security group ID"""
        try:
            response = self.ec2_client.describe_security_groups(
                GroupNames=[self.security_group_name]
            )
            
            sg_id = response['SecurityGroups'][0]['GroupId']
            print(f"Using security group: {sg_id}")
            return sg_id
            
        except ClientError as e:
            if 'InvalidGroup.NotFound' in str(e):
                print(f"❌ Security group '{self.security_group_name}' not found. Please run setup_aws.py first.")
                raise
            else:
                print(f"❌ Error getting security group: {e}")
                raise

    def create_target_groups(self, vpc_id):
        """Create target groups for both clusters"""
        target_groups = {}
        
        # Target group configurations
        tg_configs = [
            {
                'name': f'{self.project_name}-cluster1-tg',
                'cluster': 'cluster1',
                'description': 'Target group for cluster1 instances (t2.large)'
            },
            {
                'name': f'{self.project_name}-cluster2-tg',
                'cluster': 'cluster2',
                'description': 'Target group for cluster2 instances (t2.micro)'
            }
        ]
        
        for config in tg_configs:
            try:
                print(f"Creating target group: {config['name']}")
                
                response = self.elbv2_client.create_target_group(
                    Name=config['name'],
                    Protocol='HTTP',
                    Port=8000,
                    VpcId=vpc_id,
                    HealthCheckProtocol='HTTP',
                    HealthCheckPath='/health',
                    HealthCheckPort='8000',  # Explicitly set health check port
                    HealthCheckIntervalSeconds=30,
                    HealthCheckTimeoutSeconds=5,
                    HealthyThresholdCount=2,
                    UnhealthyThresholdCount=5,
                    Tags=[
                        {'Key': 'Name', 'Value': config['name']},
                        {'Key': 'Project', 'Value': self.project_name},
                        {'Key': 'Cluster', 'Value': config['cluster']}
                    ]
                )
                
                tg_arn = response['TargetGroups'][0]['TargetGroupArn']
                target_groups[config['cluster']] = {
                    'arn': tg_arn,
                    'name': config['name']
                }
                
                print(f"Target group created: {config['name']}")
                
            except Exception as e:
                print(f"❌ Error creating target group {config['name']}: {e}")
                raise
        
        return target_groups

    def register_targets(self, target_groups, cluster1_instances, cluster2_instances):
        """Register instances with their respective target groups"""
        
        # Register cluster1 instances
        if cluster1_instances and 'cluster1' in target_groups:
            print(f"Registering {len(cluster1_instances)} cluster1 instances...")
            
            targets = [
                {'Id': instance['InstanceId'], 'Port': 8000}
                for instance in cluster1_instances
            ]
            
            try:
                self.elbv2_client.register_targets(
                    TargetGroupArn=target_groups['cluster1']['arn'],
                    Targets=targets
                )
                print(f"Registered {len(targets)} cluster1 targets")
            except Exception as e:
                print(f"❌ Error registering cluster1 targets: {e}")
                raise
        
        # Register cluster2 instances
        if cluster2_instances and 'cluster2' in target_groups:
            print(f"Registering {len(cluster2_instances)} cluster2 instances...")
            
            targets = [
                {'Id': instance['InstanceId'], 'Port': 8000}
                for instance in cluster2_instances
            ]
            
            try:
                self.elbv2_client.register_targets(
                    TargetGroupArn=target_groups['cluster2']['arn'],
                    Targets=targets
                )
                print(f"Registered {len(targets)} cluster2 targets")
            except Exception as e:
                print(f"❌ Error registering cluster2 targets: {e}")
                raise

    def create_load_balancer(self, subnet_ids, security_group_id):
        """Create the Application Load Balancer"""
        try:
            print(f"Creating Application Load Balancer: {self.alb_name}")
            
            response = self.elbv2_client.create_load_balancer(
                Name=self.alb_name,
                Subnets=subnet_ids,
                SecurityGroups=[security_group_id],
                Scheme='internet-facing',
                Type='application',
                IpAddressType='ipv4',
                Tags=[
                    {'Key': 'Name', 'Value': self.alb_name},
                    {'Key': 'Project', 'Value': self.project_name}
                ]
            )
            
            alb_info = response['LoadBalancers'][0]
            alb_arn = alb_info['LoadBalancerArn']
            alb_dns = alb_info['DNSName']
            
            print(f"Application Load Balancer created: {self.alb_name}")
            print(f"   DNS Name: {alb_dns}")
            
            return alb_arn, alb_dns
            
        except Exception as e:
            print(f"❌ Error creating load balancer: {e}")
            raise

    def create_listener_and_rules(self, alb_arn, target_groups):
        """Create listener and path-based routing rules"""
        try:
            print("Creating listener and routing rules...")
            
            # Create default action (forward to cluster1 by default)
            default_actions = []
            if 'cluster1' in target_groups:
                default_actions = [
                    {
                        'Type': 'forward',
                        'TargetGroupArn': target_groups['cluster1']['arn']
                    }
                ]
            elif 'cluster2' in target_groups:
                default_actions = [
                    {
                        'Type': 'forward',
                        'TargetGroupArn': target_groups['cluster2']['arn']
                    }
                ]
            else:
                # Fixed response if no target groups
                default_actions = [
                    {
                        'Type': 'fixed-response',
                        'FixedResponseConfig': {
                            'StatusCode': '503',
                            'ContentType': 'text/plain',
                            'MessageBody': 'No healthy targets available'
                        }
                    }
                ]
            
            # Create listener
            listener_response = self.elbv2_client.create_listener(
                LoadBalancerArn=alb_arn,
                Protocol='HTTP',
                Port=80,
                DefaultActions=default_actions
            )
            
            listener_arn = listener_response['Listeners'][0]['ListenerArn']
            print(f"Listener created: {listener_arn}")
            
            # Create path-based rules
            rules = []
            
            # Rule for /cluster1 path
            if 'cluster1' in target_groups:
                rule1_response = self.elbv2_client.create_rule(
                    ListenerArn=listener_arn,
                    Conditions=[
                        {
                            'Field': 'path-pattern',
                            'Values': ['/cluster1*']
                        }
                    ],
                    Priority=100,
                    Actions=[
                        {
                            'Type': 'forward',
                            'TargetGroupArn': target_groups['cluster1']['arn']
                        }
                    ]
                )
                rules.append(('cluster1', rule1_response['Rules'][0]['RuleArn']))
                print("Created rule: /cluster1* → cluster1 target group")
            
            # Rule for /cluster2 path
            if 'cluster2' in target_groups:
                rule2_response = self.elbv2_client.create_rule(
                    ListenerArn=listener_arn,
                    Conditions=[
                        {
                            'Field': 'path-pattern',
                            'Values': ['/cluster2*']
                        }
                    ],
                    Priority=200,
                    Actions=[
                        {
                            'Type': 'forward',
                            'TargetGroupArn': target_groups['cluster2']['arn']
                        }
                    ]
                )
                rules.append(('cluster2', rule2_response['Rules'][0]['RuleArn']))
                print("Created rule: /cluster2* → cluster2 target group")
            
            return listener_arn, rules
            
        except Exception as e:
            print(f"❌ Error creating listener/rules: {e}")
            raise

    def wait_for_target_health(self, target_groups):
        """Wait for targets to become healthy"""
        print("Waiting for targets to become healthy...")
        
        max_wait_time = 300  # 5 minutes
        check_interval = 15
        waited_time = 0
        
        while waited_time < max_wait_time:
            all_healthy = True
            
            for cluster, tg_info in target_groups.items():
                try:
                    response = self.elbv2_client.describe_target_health(
                        TargetGroupArn=tg_info['arn']
                    )
                    
                    healthy_count = 0
                    total_count = 0
                    
                    for target in response['TargetHealthDescriptions']:
                        total_count += 1
                        if target['TargetHealth']['State'] == 'healthy':
                            healthy_count += 1
                        elif target['TargetHealth']['State'] in ['unhealthy', 'unused']:
                            all_healthy = False
                    
                    print(f"   {cluster}: {healthy_count}/{total_count} healthy")
                    
                    if healthy_count == 0 and total_count > 0:
                        all_healthy = False
                        
                except Exception as e:
                    print(f"   Error checking {cluster} health: {e}")
                    all_healthy = False
            
            if all_healthy:
                print("All targets are healthy!")
                return True
            
            time.sleep(check_interval)
            waited_time += check_interval
            print(f"   Waited {waited_time}s/{max_wait_time}s...")
        
        print("  Timeout waiting for all targets to be healthy")
        return False

    def save_alb_info(self, alb_dns, target_groups, cluster1_instances, cluster2_instances):
        """Save ALB information to JSON file"""
        alb_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'project': self.project_name,
            'region': self.region,
            'alb_name': self.alb_name,
            'alb_dns': alb_dns,
            'endpoints': {
                'root': f'http://{alb_dns}',
                'cluster1': f'http://{alb_dns}/cluster1',
                'cluster2': f'http://{alb_dns}/cluster2'
            },
            'target_groups': target_groups,
            'instances': {
                'cluster1': cluster1_instances,
                'cluster2': cluster2_instances
            }
        }
        
        output_file = 'alb_info.json'
        with open(output_file, 'w') as f:
            json.dump(alb_info, f, indent=2)
        
        print(f"ALB information saved to: {output_file}")
        return alb_info

    def print_alb_summary(self, alb_dns, target_groups, cluster1_instances, cluster2_instances):
        """Print ALB deployment summary"""
        print("\n" + "="*80)
        print("APPLICATION LOAD BALANCER DEPLOYED SUCCESSFULLY!")
        print("="*80)
        
        print(f"\nALB SUMMARY:")
        print(f"   • Load Balancer: {self.alb_name}")
        print(f"   • DNS Name: {alb_dns}")
        print(f"   • Region: {self.region}")
        print(f"   • Target Groups: {len(target_groups)}")
        
        print(f"\nENDPOINTS:")
        print(f"   • Root (default): http://{alb_dns}")
        print(f"   • Cluster1 path: http://{alb_dns}/cluster1")
        print(f"   • Cluster2 path: http://{alb_dns}/cluster2")
        
        if 'cluster1' in target_groups:
            print(f"\nCLUSTER1 TARGET GROUP:")
            print(f"   • Target Group: {target_groups['cluster1']['name']}")
            print(f"   • Instances: {len(cluster1_instances)}")
            for i, instance in enumerate(cluster1_instances, 1):
                print(f"     {i}. {instance['InstanceId']} ({instance['PrivateIpAddress']})")
        
        if 'cluster2' in target_groups:
            print(f"\nCLUSTER2 TARGET GROUP:")
            print(f"   • Target Group: {target_groups['cluster2']['name']}")
            print(f"   • Instances: {len(cluster2_instances)}")
            for i, instance in enumerate(cluster2_instances, 1):
                print(f"     {i}. {instance['InstanceId']} ({instance['PrivateIpAddress']})")
        
        print(f"\nNEXT STEPS:")
        print(f"   1. Test endpoints:")
        print(f"      curl http://{alb_dns}")
        print(f"      curl http://{alb_dns}/cluster1")
        print(f"      curl http://{alb_dns}/cluster2")
        print(f"   2. Run benchmarks: python src/benchmarking/run_benchmark.py")
        print(f"   3. Cleanup when done: python src/aws_automation/teardown_aws.py")
        
        print("\n" + "="*80)

def main():
    """Main function to set up Application Load Balancer"""
    try:
        print("Starting Application Load Balancer Setup for LOG8415E Assignment")
        print("="*70)
        
        # Initialize ALB manager
        alb_manager = ALBManager()
        
        # Get project instances
        cluster1_instances, cluster2_instances = alb_manager.get_project_instances()
        
        if not cluster1_instances and not cluster2_instances:
            print("❌ No running instances found. Please run setup_aws.py first.")
            return
        
        # Get VPC and subnets
        vpc_id, subnet_ids = alb_manager.get_default_vpc_and_subnets()
        
        # Get security group
        security_group_id = alb_manager.get_security_group_id()
        
        # Create target groups
        target_groups = alb_manager.create_target_groups(vpc_id)
        
        # Register targets
        alb_manager.register_targets(target_groups, cluster1_instances, cluster2_instances)
        
        # Create load balancer
        alb_arn, alb_dns = alb_manager.create_load_balancer(subnet_ids, security_group_id)
        
        # Create listener and rules
        listener_arn, rules = alb_manager.create_listener_and_rules(alb_arn, target_groups)
        
        # Wait for targets to be healthy
        alb_manager.wait_for_target_health(target_groups)
        
        # Save ALB info
        alb_manager.save_alb_info(alb_dns, target_groups, cluster1_instances, cluster2_instances)
        
        # Print summary
        alb_manager.print_alb_summary(alb_dns, target_groups, cluster1_instances, cluster2_instances)
        
    except KeyboardInterrupt:
        print("\n  ALB setup interrupted by user")
    except Exception as e:
        print(f"\n❌ ALB setup failed: {e}")
        raise

if __name__ == "__main__":
    main()