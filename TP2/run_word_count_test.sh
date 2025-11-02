set -e

echo "LOG8415E Assignment - Starting deployment"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment"
    python3 -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies"
    pip install -r requirements.txt
fi

echo "Deploying Word Count Test Infrastructure"
python src/word_count/word_count_setup.py

echo "Deployment complete!"
echo "To check the progress of the tests, ssh into the instance and use the following command: cat ../../var/log/cloud-init-output.log"
echo "To check the performance results, wait until tests are done and check for comparison_hadoop_linux.png, comparison_hadoop_spark.png and timings.csv in /home/ubuntu/results/"
echo "Cleanup: python src/word_count/word_count_teardown.py"