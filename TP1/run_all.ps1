Write-Host "Starting deployment..." -ForegroundColor Green

if (-not $env:VIRTUAL_ENV) {
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .venv\Scripts\Activate.ps1
    }
}

try {
    Write-Host "Step 1: Deploying infrastructure..." -ForegroundColor Yellow
    python src/aws_automation/setup_aws.py
    if ($LASTEXITCODE -ne 0) { throw "Infrastructure deployment failed" }

    Write-Host "Step 2: Creating load balancer..." -ForegroundColor Yellow
    python src/load_balancer/create_alb.py
    if ($LASTEXITCODE -ne 0) { throw "ALB creation failed" }

    Write-Host "Step 3: Waiting for apps to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 60

    Write-Host "Step 4: Running benchmarks..." -ForegroundColor Yellow
    python src/benchmarking/benchmarking_struct.py
    if ($LASTEXITCODE -ne 0) { throw "Benchmarking failed" }

    Write-Host "Step 5: Collecting metrics..." -ForegroundColor Yellow
    python src/monitoring/cloudwatch_metrics.py
    if ($LASTEXITCODE -ne 0) { throw "Metrics collection failed" }

    Write-Host "Deployment complete! Check generated JSON/CSV files." -ForegroundColor Green
    Write-Host "Cleanup: python src/aws_automation/teardown_aws.py" -ForegroundColor Yellow

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}