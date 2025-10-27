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

echo "Step 1: Deploying infrastructure"
python src/aws_automation/setup_aws.py

echo "Step 2: Creating load balancer"
python src/load_balancer/create_alb.py

echo "Step 3: Waiting for apps to start"
sleep 60

echo "Step 4: Running benchmarks"
python src/benchmarking/run_benchmark.py

echo "Step 5: Collecting metrics"
python src/monitoring/cloudwatch_metrics.py

echo "Deployment complete! Check generated JSON/CSV files."
echo "Cleanup: python src/aws_automation/teardown_aws.py"