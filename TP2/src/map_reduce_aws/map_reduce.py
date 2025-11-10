import os
import subprocess
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from aws_automation import setup_aws
from constants.map_reduce_constants import (
    DEFAULT_AMI_ID, 
    MAPPER_SENDING_SCRIPT, 
    MAPPER_USER_DATA_SCRIPT, 
    REDUCER_USER_DATA_SCRIPT, 
    PROJECT_NAME,
    SSH_KEY_FILE,
    SSH_OPTIONS,
    EC2_USER,
    EC2_HOME_DIR,
    INSTANCE_TYPE,
    FRIEND_LIST_FILE,
)

def split_file(input_path, m):
    with open(input_path, 'r') as f:
        lines = f.readlines()

    n = len(lines)
    chunk_size = (n + m - 1) // m

    for i in range(m):
        start = i * chunk_size
        end = start + chunk_size
        chunk = lines[start:end]

        if not chunk:
            break

        output_path = f"friendList-{i+1}.txt"
        with open(output_path, 'w') as f_out:
            f_out.writelines(chunk)
            f_out.flush()

        print(f"Created {output_path} ({len(chunk)} lines)")



def main():
    try:
        INSTANCES = 3
        split_file(FRIEND_LIST_FILE, INSTANCES)
        manager = setup_aws.AWSManager(PROJECT_NAME)
        
        security_group_id = manager.create_security_group(True)
        mapper_ids = []
        for i in range(1, INSTANCES + 1):
            mapper_user_data_script = MAPPER_USER_DATA_SCRIPT.replace('INSTANCE_NUMBER', str(i))
            instance_id1 = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, f"mapperInstance-{i}", mapper_user_data_script, "tp2", INSTANCE_TYPE)
            mapper_ids.append((instance_id1, i))

        reducer_user_data_script = REDUCER_USER_DATA_SCRIPT.replace('INSTANCE_NUMBER', str(INSTANCES))
        instance_id2 = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, "reducerInstance", reducer_user_data_script, "tp2", INSTANCE_TYPE)
        manager.wait_for_instances([instance_id1, instance_id2], True)
        ip2 = manager.get_public_ip(instance_id2)

        for instance_id, i in mapper_ids:
            ip1 = manager.get_public_ip(instance_id)
            scp_command = [
                'scp', '-i', SSH_KEY_FILE,
                *SSH_OPTIONS,
                SSH_KEY_FILE, f'{EC2_USER}@{ip1}:{EC2_HOME_DIR}/'
            ]

            mapper_sending_string_formated = MAPPER_SENDING_SCRIPT.format(ip1=ip2)

            ssh_command = [
                'ssh', '-i', SSH_KEY_FILE,
                *SSH_OPTIONS,
                f'{EC2_USER}@{ip1}',
                mapper_sending_string_formated
            ]

            scp_command_2 = [
                'scp', '-i', SSH_KEY_FILE,
                *SSH_OPTIONS,
                f'friendList-{i}.txt',
                f'{EC2_USER}@{ip1}:{EC2_HOME_DIR}/incomplete.txt'
            ]

            ssh_command_2 = [
                'ssh', '-i', SSH_KEY_FILE,
                *SSH_OPTIONS,
                f'{EC2_USER}@{ip1}',
                f'mv {EC2_HOME_DIR}/incomplete.txt {EC2_HOME_DIR}/friendList.txt'
            ]
            
            try:
                print(' '.join(scp_command))
                output1 = subprocess.run(scp_command, capture_output=True, text=True, check=True)                

                print(' '.join(scp_command_2))
                output3 = subprocess.run(scp_command_2, capture_output=True, text=True, check=True)

                print(' '.join(ssh_command_2))
                output4 = subprocess.run(ssh_command_2, capture_output=True, text=True, check=True)

                print(' '.join(ssh_command))
                output2 = subprocess.run(ssh_command, capture_output=True, text=True, check=True)
                
                print("Standard Output 1:")
                print(output1.stdout)
                print("Standard Error 1:")
                print(output1.stderr)

                print("Standard Output 2:")
                print(output2.stdout)
                print("Standard Error 2:")
                print(output2.stderr)

                print("Standard Output 3:")
                print(output3.stdout)
                print("Standard Error 3:")
                print(output3.stderr)

                print("Standard Output 4:")
                print(output4.stdout)
                print("Standard Error 4:")
                print(output4.stderr)

                print(f'File Transfered Successfully for instance {instance_id} {i} ')
            except Exception as e:
                print(f'SCP failed: {e}')

        print("Mapper Reducer instances deployment completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        raise
    
if __name__ == "__main__":
    main()
