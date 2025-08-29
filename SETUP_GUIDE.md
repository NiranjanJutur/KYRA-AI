# PDF Summarizer - Complete Setup Guide

## Prerequisites

- Python 3.8 or higher
- Windows 10/11 (this guide is Windows-focused)
- Internet connection for downloading packages

## Quick Start (Automated Installation)

### Option 1: Using Batch File (Recommended for beginners)
1. Double-click `install_dependencies.bat`
2. Follow the prompts
3. Wait for installation to complete

### Option 2: Using PowerShell
1. Right-click `install_dependencies.ps1` and select "Run with PowerShell"
2. Follow the prompts
3. Wait for installation to complete

## Manual Installation

### 1. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install PyTorch (CPU version for Windows)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip install -r requirements.txt

# Install Windows-specific packages
pip install pywin32
```

## Environment Configuration

### 1. Create .env file
Copy `env_config.txt` to `.env` and update the following variables:

```bash
# Required: Get your Gemini API key from Google AI Studio
GOOGLE_API_KEY=your_actual_api_key_here

# Optional: Google Cloud Vision credentials (for enhanced OCR)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json

# Optional: Custom Tesseract path if not in system PATH
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### 2. Get API Keys
- **Gemini API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Google Cloud Vision**: Only needed if you want enhanced OCR capabilities

## Install Tesseract OCR

### Windows Installation
1. Download from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR`)
3. Add to system PATH:
   - Right-click 'This PC' → Properties → Advanced system settings
   - Environment Variables → System variables → Path → Edit
   - Add: `C:\Program Files\Tesseract-OCR`
   - Click OK on all dialogs

### Verify Tesseract Installation
```bash
tesseract --version
```

## Install Redis (Optional - for Celery)

### Option 1: Windows Redis
1. Download from [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
2. Run the installer
3. Start Redis service

### Option 2: WSL2 with Ubuntu (Recommended)
```bash
# In WSL2 Ubuntu
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Option 3: Docker
```bash
docker run -d -p 6379:6379 redis:latest
```

## Database Setup

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

## Start the Application

### Development Server
```bash
# Activate virtual environment
.venv\Scripts\activate

# Start Django server
python manage.py runserver

# Visit: http://127.0.0.1:8000
```

### Start Celery Worker (if using Redis)
```bash
# In a new terminal, activate virtual environment
.venv\Scripts\activate

# Start Celery worker
celery -A pdf_summarizer worker --loglevel=info
```

## Troubleshooting

### Common Issues

#### 1. Tesseract not found
```python
# Add this to your Django settings or views
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### 2. PyTorch installation issues
```bash
# Try CPU-only version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Or use conda
conda install pytorch torchvision torchaudio cpuonly -c pytorch
```

#### 3. Redis connection issues
```bash
# Test Redis connection
redis-cli ping

# If using WSL2, ensure Redis is running
sudo systemctl status redis-server
```

#### 4. Permission issues
```bash
# Run PowerShell as Administrator
# Or use WSL2 for better compatibility
```

### Performance Optimization

#### 1. GPU Support (if available)
```bash
# Install CUDA version of PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 2. Memory Optimization
```bash
# Set environment variables
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
```

## File Structure After Setup

```
pdf_summarizer/
├── .venv/                    # Virtual environment
├── .env                      # Environment variables (create this)
├── env_config.txt            # Environment template
├── requirements.txt           # Python dependencies
├── install_dependencies.bat  # Windows installer
├── install_dependencies.ps1  # PowerShell installer
├── SETUP_GUIDE.md           # This file
├── manage.py                 # Django management
├── pdf_summarizer/          # Django project
├── summarizer/              # Main app
├── static/                  # Static files
├── media/                   # Uploaded files
└── templates/               # HTML templates
```

## Next Steps

1. **Test the application**: Upload a PDF and try summarization
2. **Configure OCR**: Test image text extraction
3. **Set up production**: Update security settings in `.env`
4. **Monitor performance**: Check Celery worker logs
5. **Scale up**: Consider using PostgreSQL instead of SQLite

## Support

- Check the logs in Django admin
- Verify all environment variables are set
- Ensure Tesseract is in your system PATH
- Test Redis connection if using Celery

## Production Deployment

For production deployment, consider:
- Using PostgreSQL instead of SQLite
- Setting `DEBUG=False` in `.env`
- Enabling HTTPS and security headers
- Using a proper web server (nginx + gunicorn)
- Setting up monitoring and logging
