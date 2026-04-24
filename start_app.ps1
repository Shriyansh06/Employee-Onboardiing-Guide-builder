# PowerShell Script to run the Onboarding Guide Builder
# This script attempts to find the correct Python executable even if it's not in the PATH.

$ErrorActionPreference = "Stop"

Write-Host "Searching for Python and Streamlit..." -ForegroundColor Cyan

# 1. Try to find python in .venv
$localVenv = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $localVenv) {
    $pythonExe = $localVenv
}
else {
    # Fallback to pip path logic
    $pipPath = Get-Command pip -ErrorAction SilentlyContinue
    $pythonExe = "python" # Default fallback
    if ($pipPath) {
        $pythonDir = Split-Path (Split-Path $pipPath.Source -Parent) -Parent
        $candidate = Join-Path $pythonDir "python.exe"
        if (Test-Path $candidate -and $candidate -notmatch "WindowsApps") {
            $pythonExe = $candidate
        } else {
            $candidate2 = Join-Path (Split-Path $pipPath.Source -Parent) "python.exe"
            if (Test-Path $candidate2 -and $candidate2 -notmatch "WindowsApps") {
                $pythonExe = $candidate2
            }
        }
    }
}

Write-Host "Using Python: $pythonExe" -ForegroundColor Green

# 2. Ensure dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Cyan
try {
    & $pythonExe -m pip install -r requirements.txt --quiet
    Write-Host "Dependencies verified." -ForegroundColor Green
} catch {
    Write-Host "Warning: Failed to install requirements automatically. Some modules might be missing." -ForegroundColor Yellow
}

# 3. Run Streamlit
Write-Host "Starting Streamlit app..." -ForegroundColor Cyan
try {
    & $pythonExe -m streamlit run project/app.py
} catch {
    Write-Host "Failed to start. Try running this manually:" -ForegroundColor Red
    Write-Host "pip install streamlit"
    Write-Host "python -m streamlit run project/app.py"
}
