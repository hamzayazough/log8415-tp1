import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
from aws_automation import teardown_aws
from constants.word_count_constants import WORD_COUNT_PROJECT_NAME

def main():
    try:
        print("Starting AWS Infrastructure Teardown")
        print("=" * 50)
        
        teardown = teardown_aws.AWSTeardown(WORD_COUNT_PROJECT_NAME)
        
        instance_ids = teardown.find_project_instances()
        
        teardown.terminate_instances(instance_ids)
        
        print("Waiting 30 seconds before deleting security group...")
        time.sleep(30)
        teardown.delete_security_group()
        
        print("\n" + "=" * 50)
        print("TEARDOWN COMPLETED SUCCESSFULLY!")
        print("All AWS resources have been removed.")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error during teardown: {e}")
        raise

if __name__ == "__main__":
    main()