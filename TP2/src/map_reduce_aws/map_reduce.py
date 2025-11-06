import os
import subprocess
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aws_automation import setup_aws
from constants.map_reduce_constants import DEFAULT_AMI_ID, MAPPER_USER_DATA_SCRIPT, REDUCER_USER_DATA_SCRIPT, PROJECT_NAME, MAPPER_SENDING_SCRIPT

def main():
    try:
        manager = setup_aws.AWSManager(PROJECT_NAME)
        
        security_group_id = manager.create_security_group(True)

        (instance_id1, ip1) = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, "mapperInstance", MAPPER_USER_DATA_SCRIPT, "vockey")
        (instance_id2, ip2) = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, "reducerInstance", REDUCER_USER_DATA_SCRIPT, "vockey")
        manager.wait_for_instances([instance_id1, instance_id2])

        MAPPER_SENDING_SCRIPT = MAPPER_SENDING_SCRIPT.replace('HOST_PUBLIC_IP_ADDRESS', ip2)
        print(MAPPER_SENDING_SCRIPT)

        scp_command = [
            'scp', '-i' 'tp2.pem',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-r', '.\\jobs\\send-to-reducer.sh'
            f'ubuntu@{ip1}:~'
        ]

        try:
            subprocess.run(scp_command, check=True)
            print('File Transfered Successfully')
        except e:
            print(f'SCP failed: {e}')




        print("\Mapper Reducer instances deployment completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        raise
    
if __name__ == "__main__":
    main()