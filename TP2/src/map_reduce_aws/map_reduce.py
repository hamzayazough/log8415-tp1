import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aws_automation import setup_aws
from constants.map_reduce_constants import DEFAULT_AMI_ID, MAPPER_USER_DATA_SCRIPT, REDUCER_USER_DATA_SCRIPT, PROJECT_NAME

def main():
    try:
        manager = setup_aws.AWSManager(PROJECT_NAME)
        
        security_group_id = manager.create_security_group(True)

        manager.upload_file('input.txt', '..\\map_reduce\\friendList.txt')
        # instance_id = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, "mapperInstance", MAPPER_USER_DATA_SCRIPT, "vockey")
        # instance_id = manager.launch_instance(DEFAULT_AMI_ID, security_group_id, "reducerInstance", REDUCER_USER_DATA_SCRIPT, "vockey")
        # manager.wait_for_instances([instance_id])

        print("\Mapper Reducer instances deployment completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        raise
    
if __name__ == "__main__":
    main()