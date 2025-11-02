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

echo "Deployment complete! Now just wait for the tests to run."
echo "Cleanup: python src/word_count/word_count_teardown.py"