set -e

echo "LOG8415E Assignment - Starting deployment"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment"
    python -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies"
    pip install -r requirements.txt
fi

echo "Deploying MapReduce Infrastructure"
python ./src/map_reduce_aws/map_reduce.py

echo "Deploying Word Count Test Infrastructure"
python ./src/word_count/word_count_setup.py

echo "Deployment complete!"
echo "To check the results of the map reduce experiment, check for recommendations.txt in /home/ec2-user/"
echo "Cleanup map reduce experiment: python ./src/map_reduce_aws/map_reduce_teardown.py"

echo "To check the progress of the word count tests, ssh into the instance and use the following command: cat ../../var/log/cloud-init-output.log"
echo "To check the performance results of the word count tests, wait until tests are done and check for comparison_hadoop_linux.png, comparison_hadoop_spark.png and timings.csv in /home/ubuntu/results/"
echo "Cleanup word count tests: python ./src/word_count/word_count_teardown.py"