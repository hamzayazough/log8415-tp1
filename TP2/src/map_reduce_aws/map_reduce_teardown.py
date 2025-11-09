import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aws_automation import teardown_aws
from constants.map_reduce_constants import PROJECT_NAME

def main():
    teardown = teardown_aws.AWSTeardown(PROJECT_NAME)
    teardown.teardown_project()

if __name__ == "__main__":
    main()