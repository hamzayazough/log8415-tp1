import boto3
import json
from datetime import datetime, timedelta, timezone

class CloudWatchMonitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.ec2_client = boto3.client('ec2')
        self.elbv2_client = boto3.client('elbv2')
        self.project_name = 'LOG8415E-TP1'
        print(f"CloudWatch Monitor initialized for {self.project_name}")

    def get_project_instances(self):
        response = self.ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Project', 'Values': [self.project_name]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        print(f"Found {len(instance_ids)} instances to monitor")
        return instance_ids

    def get_alb_arn(self):
        try:
            response = self.elbv2_client.describe_load_balancers(
                Names=[f'{self.project_name}-ALB']
            )
            alb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
            alb_name = alb_arn.split('/')[-3] + '/' + alb_arn.split('/')[-2] + '/' + alb_arn.split('/')[-1]
            return alb_name
        except:
            print("ALB not found")
            return None

    def convert_datapoints(self, datapoints):
        """Convert datetime objects in datapoints to ISO format strings"""
        converted = []
        for dp in datapoints:
            dp_copy = dp.copy()
            if 'Timestamp' in dp_copy:
                dp_copy['Timestamp'] = dp_copy['Timestamp'].isoformat()
            converted.append(dp_copy)
        return converted

    def get_ec2_metrics(self, instance_ids, period_minutes=5):
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=period_minutes)
        
        metrics_data = {}
        
        for instance_id in instance_ids:
            print(f"Getting metrics for instance {instance_id}")
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum']
            )
            
            network_in = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkIn',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            network_out = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkOut',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            metrics_data[instance_id] = {
                'cpu_utilization': self.convert_datapoints(cpu_response['Datapoints']),
                'network_in': self.convert_datapoints(network_in['Datapoints']),
                'network_out': self.convert_datapoints(network_out['Datapoints'])
            }
        
        return metrics_data

    def get_alb_metrics(self, alb_name, period_minutes=5):
        if not alb_name:
            return {}
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=period_minutes)
        
        request_count = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='RequestCount',
            Dimensions=[{'Name': 'LoadBalancer', 'Value': alb_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum']
        )
        
        response_time = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='TargetResponseTime',
            Dimensions=[{'Name': 'LoadBalancer', 'Value': alb_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average']
        )
        
        healthy_hosts = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='HealthyHostCount',
            Dimensions=[{'Name': 'LoadBalancer', 'Value': alb_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average']
        )
        
        return {
            'request_count': self.convert_datapoints(request_count['Datapoints']),
            'response_time': self.convert_datapoints(response_time['Datapoints']),
            'healthy_hosts': self.convert_datapoints(healthy_hosts['Datapoints'])
        }

    def analyze_metrics(self, ec2_metrics, alb_metrics):
        analysis = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {},
            'instances': {},
            'alb': alb_metrics
        }
        
        total_cpu = 0
        instance_count = 0
        
        for instance_id, metrics in ec2_metrics.items():
            cpu_avg = 0
            if metrics['cpu_utilization']:
                cpu_values = [dp['Average'] for dp in metrics['cpu_utilization']]
                cpu_avg = sum(cpu_values) / len(cpu_values)
                total_cpu += cpu_avg
                instance_count += 1
            
            network_in_total = sum([dp['Sum'] for dp in metrics['network_in']])
            network_out_total = sum([dp['Sum'] for dp in metrics['network_out']])
            
            analysis['instances'][instance_id] = {
                'avg_cpu': cpu_avg,
                'network_in_bytes': network_in_total,
                'network_out_bytes': network_out_total,
                'data_points': len(metrics['cpu_utilization'])
            }
        
        analysis['summary'] = {
            'total_instances': instance_count,
            'avg_cpu_across_instances': total_cpu / instance_count if instance_count > 0 else 0,
            'total_requests': sum([dp['Sum'] for dp in alb_metrics.get('request_count', [])]),
            'avg_response_time': sum([dp['Average'] for dp in alb_metrics.get('response_time', [])]) / len(alb_metrics.get('response_time', [])) if alb_metrics.get('response_time') else 0
        }
        
        return analysis

    def save_metrics(self, analysis):
        with open('cloudwatch_metrics.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print("CloudWatch metrics saved to cloudwatch_metrics.json")

    def print_summary(self, analysis):
        print("\n" + "="*60)
        print("CLOUDWATCH METRICS SUMMARY")
        print("="*60)
        
        summary = analysis['summary']
        print(f"\nOVERALL PERFORMANCE:")
        print(f"  • Total instances monitored: {summary['total_instances']}")
        print(f"  • Average CPU utilization: {summary['avg_cpu_across_instances']:.2f}%")
        print(f"  • Total ALB requests: {summary['total_requests']}")
        print(f"  • Average response time: {summary['avg_response_time']:.3f}s")
        
        print(f"\nINSTANCE DETAILS:")
        for instance_id, metrics in analysis['instances'].items():
            print(f"  {instance_id}:")
            print(f"    CPU: {metrics['avg_cpu']:.2f}%")
            print(f"    Network In: {metrics['network_in_bytes']} bytes")
            print(f"    Network Out: {metrics['network_out_bytes']} bytes")
        
        print("\n" + "="*60)

def main():
    try:
        print("Starting CloudWatch Metrics Collection")
        
        monitor = CloudWatchMonitor()
        
        # Get resources
        instance_ids = monitor.get_project_instances()
        if not instance_ids:
            print("No instances found. Run setup_aws.py first.")
            return
        
        alb_name = monitor.get_alb_arn()
        
        # Collect metrics
        print("Collecting CloudWatch metrics...")
        ec2_metrics = monitor.get_ec2_metrics(instance_ids)
        alb_metrics = monitor.get_alb_metrics(alb_name)
        
        # Analyze and save
        analysis = monitor.analyze_metrics(ec2_metrics, alb_metrics)
        monitor.save_metrics(analysis)
        monitor.print_summary(analysis)
        
        print("\nCloudWatch monitoring completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()