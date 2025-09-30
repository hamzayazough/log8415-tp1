import boto3
import json
from datetime import datetime

class ALBManager:
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.elbv2_client = boto3.client('elbv2')
        self.project_name = 'LOG8415E-TP1'
        print(f"ALB Manager initialized for {self.project_name}")

    def get_project_instances(self):
        response = self.ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Project', 'Values': [self.project_name]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        cluster1_instances = []
        cluster2_instances = []
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_data = {
                    'InstanceId': instance['InstanceId'],
                    'PublicDnsName': instance.get('PublicDnsName', ''),
                    'PublicIpAddress': instance.get('PublicIpAddress', '')
                }
                
                cluster = 'unknown'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Cluster':
                        cluster = tag['Value']
                        break
                
                if cluster == 'cluster1':
                    cluster1_instances.append(instance_data)
                elif cluster == 'cluster2':
                    cluster2_instances.append(instance_data)
        
        print(f"Found Cluster1: {len(cluster1_instances)} instances, Cluster2: {len(cluster2_instances)} instances")
        return cluster1_instances, cluster2_instances

    def get_vpc_and_subnets(self):
        vpcs = self.ec2_client.describe_vpcs(
            Filters=[{'Name': 'is-default', 'Values': ['true']}]
        )
        vpc_id = vpcs['Vpcs'][0]['VpcId']
        
        subnets = self.ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        subnet_ids = [subnet['SubnetId'] for subnet in subnets['Subnets']]
        
        return vpc_id, subnet_ids

    def get_security_group_id(self):
        groups = self.ec2_client.describe_security_groups(
            Filters=[{'Name': 'group-name', 'Values': [f'{self.project_name}-SG']}]
        )
        return groups['SecurityGroups'][0]['GroupId']

    def create_target_groups(self, vpc_id):
        target_groups = {}
        
        response1 = self.elbv2_client.create_target_group(
            Name=f'{self.project_name}-Cluster1-TG',
            Protocol='HTTP',
            Port=8000,
            VpcId=vpc_id,
            HealthCheckPath='/health',
            HealthCheckIntervalSeconds=30,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=3
        )
        target_groups['cluster1'] = response1['TargetGroups'][0]['TargetGroupArn']
        print(f"Created cluster1 target group: {target_groups['cluster1']}")
        
        response2 = self.elbv2_client.create_target_group(
            Name=f'{self.project_name}-Cluster2-TG',
            Protocol='HTTP',
            Port=8000,
            VpcId=vpc_id,
            HealthCheckPath='/health',
            HealthCheckIntervalSeconds=30,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=3
        )
        target_groups['cluster2'] = response2['TargetGroups'][0]['TargetGroupArn']
        print(f"Created cluster2 target group: {target_groups['cluster2']}")
        
        return target_groups

    def register_targets(self, target_groups, cluster1_instances, cluster2_instances):        
        if cluster1_instances:
            targets1 = [{'Id': instance['InstanceId']} for instance in cluster1_instances]
            self.elbv2_client.register_targets(
                TargetGroupArn=target_groups['cluster1'],
                Targets=targets1
            )
            print(f"Registered {len(targets1)} cluster1 targets")
        
        if cluster2_instances:
            targets2 = [{'Id': instance['InstanceId']} for instance in cluster2_instances]
            self.elbv2_client.register_targets(
                TargetGroupArn=target_groups['cluster2'],
                Targets=targets2
            )
            print(f"Registered {len(targets2)} cluster2 targets")

    def create_load_balancer(self, subnet_ids, security_group_id):
        response = self.elbv2_client.create_load_balancer(
            Name=f'{self.project_name}-ALB',
            Subnets=subnet_ids[:2],
            SecurityGroups=[security_group_id],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4'
        )
        
        alb = response['LoadBalancers'][0]
        alb_arn = alb['LoadBalancerArn']
        alb_dns = alb['DNSName']
        
        print(f"Created ALB: {alb_dns}")
        return alb_arn, alb_dns

    def create_listener_with_rules(self, alb_arn, target_groups):    
        response = self.elbv2_client.create_listener(
            LoadBalancerArn=alb_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'ForwardConfig': {
                        'TargetGroups': [
                            {
                                'TargetGroupArn': target_groups['cluster1'],
                                'Weight': 1
                            },
                            {
                                'TargetGroupArn': target_groups['cluster2'],
                                'Weight': 1
                            }
                        ],
                        'TargetGroupStickinessConfig': {
                            'Enabled': False
                        }
                    }
                }
]
        )
        
        listener_arn = response['Listeners'][0]['ListenerArn']
        print(f"Created listener: {listener_arn}")
        self.elbv2_client.create_rule(
            ListenerArn=listener_arn,
            Priority=100,
            Conditions=[{
                'Field': 'path-pattern',
                'Values': ['/cluster1*']
            }],
            Actions=[{
                'Type': 'forward',
                'TargetGroupArn': target_groups['cluster1']
            }]
        )
        print("Created rule for /cluster1 -> cluster1 target group")
        self.elbv2_client.create_rule(
            ListenerArn=listener_arn,
            Priority=200,
            Conditions=[{
                'Field': 'path-pattern',
                'Values': ['/cluster2*']
            }],
            Actions=[{
                'Type': 'forward',
                'TargetGroupArn': target_groups['cluster2']
            }]
        )
        print("Created rule for /cluster2 -> cluster2 target group")
        
        return listener_arn

    def wait_for_alb(self, alb_arn):
        print("Waiting for ALB to be active...")
        waiter = self.elbv2_client.get_waiter('load_balancer_available')
        waiter.wait(LoadBalancerArns=[alb_arn])
        print("ALB is active!")


    """Method to save ALB info to JSON"""
    def save_alb_info(self, alb_dns, cluster1_instances, cluster2_instances):
        info = {
            'timestamp': datetime.utcnow().isoformat(),
            'project': self.project_name,
            'alb_dns': alb_dns,
            'endpoints': {
                'root': f'http://{alb_dns}',
                'cluster1': f'http://{alb_dns}/cluster1',
                'cluster2': f'http://{alb_dns}/cluster2'
            },
            'clusters': {
                'cluster1': cluster1_instances,
                'cluster2': cluster2_instances
            },
            'total_instances': len(cluster1_instances) + len(cluster2_instances)
        }
        
        with open('alb_info.json', 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"ALB endpoints:")
        print(f"  Root: http://{alb_dns}")
        print(f"  Cluster1: http://{alb_dns}/cluster1")
        print(f"  Cluster2: http://{alb_dns}/cluster2")
        print(f"ALB info saved to alb_info.json")

def main():
    try:
        print("Starting ALB Setup")
        
        manager = ALBManager()
        cluster1_instances, cluster2_instances = manager.get_project_instances()
        if not cluster1_instances and not cluster2_instances:
            print("No instances found. Run setup_aws.py first.")
            return
        
        vpc_id, subnet_ids = manager.get_vpc_and_subnets()
        security_group_id = manager.get_security_group_id()
        
        target_groups = manager.create_target_groups(vpc_id)
        manager.register_targets(target_groups, cluster1_instances, cluster2_instances)
        alb_arn, alb_dns = manager.create_load_balancer(subnet_ids, security_group_id)
        manager.create_listener_with_rules(alb_arn, target_groups)

        manager.wait_for_alb(alb_arn)
        manager.save_alb_info(alb_dns, cluster1_instances, cluster2_instances)
        
        print("\nALB setup completed successfully!")
        print(f"Test endpoints:")
        print(f"  http://{alb_dns}/cluster1")
        print(f"  http://{alb_dns}/cluster2")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()