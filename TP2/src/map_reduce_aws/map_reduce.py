import os
import subprocess
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from aws_automation import setup_aws
from constants.map_reduce_constants import DEFAULT_AMI_ID, MAPPER_SENDING_SCRIPT, MAPPER_USER_DATA_SCRIPT, REDUCER_USER_DATA_SCRIPT, PROJECT_NAME


def main():
    try:
        manager = setup_aws.AWSManager(PROJECT_NAME)
        
        security_group_id = manager.create_security_group(True)

        instance_id1 = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, "mapperInstance", MAPPER_USER_DATA_SCRIPT, "tp2", 't2.micro')
        instance_id2 = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, "reducerInstance", REDUCER_USER_DATA_SCRIPT, "tp2", 't2.micro')
        manager.wait_for_instances([instance_id1, instance_id2])
        ip1 = manager.get_public_ip(instance_id1)
        ip2 = manager.get_public_ip(instance_id2)

        scp_command = [
            'scp', '-i', 'tp2.pem',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            'tp2.pem', f'ec2-user@{ip1}:/home/ec2-user/'
        ]
        print(MAPPER_SENDING_SCRIPT)

        mapper_sending_string_formated = MAPPER_SENDING_SCRIPT.format(ip1=ip2)

        ssh_command = [
            'ssh', '-i', 'tp2.pem',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ec2-user@{ip1}',
            mapper_sending_string_formated
        ]

        scp_command_2 = [
            'scp', '-i', 'tp2.pem',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            './src/map_reduce_aws/friendList.txt',
            f'ec2-user@{ip1}:/home/ec2-user/'
        ]
        print(scp_command)
        print(ssh_command)
        print(scp_command_2)

        try:
            subprocess.run(scp_command, check=True)
            subprocess.run(ssh_command, check=True)
            subprocess.run(scp_command_2, check=True)
            
            print('File Transfered Successfully')
        except Exception as e:
            print(f'SCP failed: {e}')

        print("Mapper Reducer instances deployment completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        raise
    
if __name__ == "__main__":
    main()
