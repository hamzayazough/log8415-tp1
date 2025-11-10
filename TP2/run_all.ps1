Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "LOG8415E Assignment - Starting deployment"

# Create virtual environment if not present
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment"
    python -m venv .venv
}

# Activate virtual environment
$activateScript = ".\.venv\Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    . $activateScript
}
else {
    Write-Host "ERROR: Could not find activate.ps1 for the virtual environment."
    exit 1
}

# Install dependencies if requirements.txt exists
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies"
    pip install -r requirements.txt
}

Write-Host "Deploying MapReduce Infrastructure"
python "src/map_reduce_aws/map_reduce.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Deploying Word Count Test Infrastructure"
python "src/word_count/word_count_setup.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Deployment complete!"
Write-Host "To check MapReduce results, check for recommendations.txt and selected_recommendations.txt in your home directory."
Write-Host ""
Write-Host "Cleanup MapReduce experiment:"
Write-Host "    python ./src/map_reduce_aws/map_reduce_teardown.py"
Write-Host ""
Write-Host "For word count progress, inspect cloud-init logs on the instance."
Write-Host "For results, check for: comparison_hadoop_linux.png, comparison_hadoop_spark.png, timings.csv in results directory."
Write-Host ""
Write-Host "Cleanup word count tests:"
Write-Host "    python ./src/word_count/word_count_teardown.py"
