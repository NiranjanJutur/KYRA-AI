# 📚 PDF Summarizer - AI-Powered Document Analysis Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)](https://djangoproject.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A sophisticated Django web application that leverages cutting-edge AI models to provide intelligent document summarization, image text extraction, and multilingual translation capabilities. Built with modern web technologies and designed for both individual users and enterprise environments.

## 🚀 **Key Features**

### **🤖 AI-Powered Summarization**
- **Dual AI Models**: BERT + GPT-2 combination for comprehensive document analysis
- **Google Gemini Integration**: Advanced AI-powered summarization with structured output
- **Smart Content Analysis**: Automatic detection of document type and content structure
- **Context-Aware Summaries**: Maintains document context and key relationships

### **📷 Advanced Image Processing**
- **Multi-Engine OCR**: Tesseract OCR + Google Cloud Vision integration
- **Image Enhancement**: Automatic quality improvement for better text extraction
- **Content Classification**: Smart categorization of images (documents, diagrams, technical content)
- **Batch Processing**: Handle multiple images simultaneously

### **🌍 Multilingual Support**
- **40+ Languages**: Comprehensive language coverage including Indian, European, Asian, and Middle Eastern languages
- **Real-time Translation**: Instant translation of summaries and extracted text
- **Cultural Context**: Language-specific formatting and cultural considerations
- **Text-to-Speech**: Audio output in multiple languages

### **💼 Enterprise Features**
- **User Management**: Role-based access control and user profiles
- **Document Management**: Secure storage and organization of PDFs and images
- **Question-Answering**: Interactive Q&A system for document analysis
- **Background Processing**: Celery-based asynchronous task processing
- **API Integration**: RESTful API endpoints for external integrations

## 🏗️ **Architecture Overview**

### **Technology Stack**
```
Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
Backend: Django 4.2.7, Python 3.8+
AI/ML: PyTorch, Transformers, Google Gemini API
Database: SQLite (dev) / PostgreSQL (production)
Task Queue: Celery + Redis
OCR: Tesseract, Google Cloud Vision
Translation: Deep Translator, Google Translate
```

### **System Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Django App    │    │   AI Services   │
│   (Bootstrap 5) │◄──►│   (Views/API)   │◄──►│  (PyTorch/Gemini)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Celery Tasks  │
                       │  (Background)   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   (Task Queue)  │
                       └─────────────────┘
```

## 📋 **Prerequisites**

- **Python 3.8+** with pip
- **Windows 10/11** (primary target) or Linux/macOS
- **8GB+ RAM** (recommended for AI models)
- **Internet connection** for API services and package installation

## 🛠️ **Installation & Setup**

### **Quick Start (Automated)**
```bash
# Option 1: Windows Batch File
install_dependencies.bat

# Option 2: PowerShell Script
install_dependencies.ps1
```

### **Manual Installation**
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/pdf_summarizer.git
cd pdf_summarizer

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
copy env_config.txt .env
# Edit .env with your API keys

# 5. Run migrations
python manage.py migrate

# 6. Start development server
python manage.py runserver
```

### **Environment Configuration**
Create a `.env` file with the following variables:
```bash
# Required: Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Google Cloud Vision credentials
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Optional: Custom Tesseract path
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### **External Dependencies**
- **Tesseract OCR**: [Download for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- **Redis**: For Celery task queue (optional)
- **Google AI Studio**: For Gemini API key

## 🎯 **Usage Guide**

### **PDF Summarization**
1. **Upload PDF**: Drag & drop or browse to select document
2. **Choose Model**: Select BERT+GPT-2 or Gemini summarization
3. **Generate Summary**: AI processes document and generates structured summary
4. **View Results**: Compare different summary approaches
5. **Translate**: Convert summary to any supported language

### **Image Text Extraction**
1. **Upload Image**: Support for JPG, PNG, PDF formats
2. **OCR Processing**: Automatic text extraction with quality enhancement
3. **Content Analysis**: Smart classification and content description
4. **Export Options**: Download extracted text or translated versions

### **Advanced Features**
- **Question-Answering**: Ask specific questions about uploaded documents
- **Batch Processing**: Handle multiple files simultaneously
- **User Profiles**: Customize experience and save preferences
- **API Access**: Integrate with external applications

## 🔧 **API Endpoints**

### **Core Endpoints**
```bash
POST /upload-pdf/          # Upload and process PDF documents
POST /upload-image/        # Upload and extract text from images
GET  /pdfs/               # List user's PDF documents
GET  /pdfs/<id>/          # Get specific PDF with summaries
POST /translate/           # Translate text to different languages
POST /ask-question/       # Q&A system for documents
```

### **Authentication**
- JWT-based authentication system
- Role-based access control
- Secure file upload handling

## 📊 **Performance & Scalability**

### **Optimization Features**
- **Asynchronous Processing**: Celery workers for background tasks
- **Caching**: Redis-based caching for improved response times
- **Image Optimization**: Automatic resizing and compression
- **Memory Management**: Efficient handling of large documents

### **Scalability Considerations**
- **Horizontal Scaling**: Multiple Celery workers
- **Database Optimization**: Efficient queries and indexing
- **CDN Integration**: Static file delivery optimization
- **Load Balancing**: Ready for production deployment

## 🧪 **Testing & Quality Assurance**

### **Test Coverage**
- Unit tests for core functionality
- Integration tests for API endpoints
- Performance testing for AI models
- Security testing for file uploads

### **Code Quality**
- PEP 8 compliance
- Type hints and documentation
- Error handling and logging
- Security best practices

## 🚀 **Deployment**

### **Development**
```bash
python manage.py runserver
# Visit: http://127.0.0.1:8000
```

### **Production**
```bash
# Using Gunicorn
gunicorn pdf_summarizer.wsgi:application

# Using Docker
docker-compose up -d

# Using Heroku
git push heroku main
```

### **Environment Variables**
```bash
DEBUG=False
SECRET_KEY=your_production_secret_key
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
# Fork the repository
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and commit
git commit -m 'Add amazing feature'

# Push to branch
git push origin feature/amazing-feature

# Create Pull Request
```

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Google AI Studio** for Gemini API access
- **Hugging Face** for transformer models
- **Tesseract OCR** for image text extraction
- **Django Community** for the excellent web framework
- **Open Source Community** for various libraries and tools

## 📞 **Support & Contact**

- **Issues**: [GitHub Issues](https://github.com/yourusername/pdf_summarizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/pdf_summarizer/discussions)
- **Email**: your.email@example.com
- **Documentation**: [Wiki](https://github.com/yourusername/pdf_summarizer/wiki)

## 🌟 **Star History**

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/pdf_summarizer&type=Date)](https://star-history.com/#yourusername/pdf_summarizer&Date)

---

**Made with ❤️ by [Your Name]**

*If this project helps you, please give it a ⭐ star!*