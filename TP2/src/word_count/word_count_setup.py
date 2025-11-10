import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aws_automation import setup_aws
from constants.word_count_constants import UBUNTU_AMI_ID, USER_DATA_SCRIPT_WORDCOUNT, WORD_COUNT_PROJECT_NAME

def main():
    try:
        manager = setup_aws.AWSManager(WORD_COUNT_PROJECT_NAME)
        
        security_group_id = manager.create_security_group(True)
        instance_id = manager.launch_instance(UBUNTU_AMI_ID, security_group_id, "WordCountTestInstance", USER_DATA_SCRIPT_WORDCOUNT, "tp2")
        manager.wait_for_instances([instance_id])

        print("\nWord Count test instance deployment completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        raise
    
if __name__ == "__main__":
    main()