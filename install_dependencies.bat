@echo off
echo ========================================
echo PDF Summarizer - Dependency Installer
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Checking pip installation...
pip --version
if %errorlevel% neq 0 (
    echo ERROR: pip is not installed
    echo Please install pip or upgrade Python
    pause
    exit /b 1
)

echo.
echo Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing PyTorch (CPU version for Windows)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo.
echo Installing other dependencies...
pip install -r requirements.txt

echo.
echo Installing additional Windows-specific packages...
pip install pywin32

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Copy env_config.txt to .env and update with your API keys
echo 2. Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
echo 3. Add Tesseract to your system PATH
echo 4. Install Redis for Windows (optional, for Celery)
echo 5. Run: python manage.py migrate
echo 6. Run: python manage.py runserver
echo.
echo For Redis installation on Windows:
echo - Download from: https://github.com/microsoftarchive/redis/releases
echo - Or use WSL2 with Ubuntu
echo.
pause
