# PDF Summarizer - Dependency Installer (PowerShell)
Write-Host "========================================" -ForegroundColor Green
Write-Host "PDF Summarizer - Dependency Installer" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check pip installation
Write-Host "`nChecking pip installation..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: pip is not installed" -ForegroundColor Red
    Write-Host "Please install pip or upgrade Python" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install PyTorch (CPU version for Windows)
Write-Host "`nInstalling PyTorch (CPU version for Windows)..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
Write-Host "`nInstalling other dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install additional Windows-specific packages
Write-Host "`nInstalling additional Windows-specific packages..." -ForegroundColor Yellow
pip install pywin32

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy env_config.txt to .env and update with your API keys" -ForegroundColor White
Write-Host "2. Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor White
Write-Host "3. Add Tesseract to your system PATH" -ForegroundColor White
Write-Host "4. Install Redis for Windows (optional, for Celery)" -ForegroundColor White
Write-Host "5. Run: python manage.py migrate" -ForegroundColor White
Write-Host "6. Run: python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "For Redis installation on Windows:" -ForegroundColor Cyan
Write-Host "- Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
Write-Host "- Or use WSL2 with Ubuntu" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to continue"
