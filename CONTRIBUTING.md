# 🤝 Contributing to PDF Summarizer

Thank you for your interest in contributing to PDF Summarizer! This document provides guidelines and information for contributors.

## 📋 **Table of Contents**

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Questions or Problems?](#questions-or-problems)

## 📜 **Code of Conduct**

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## 🚀 **How Can I Contribute?**

### **Reporting Bugs**
- Use the GitHub issue tracker
- Include detailed steps to reproduce
- Provide system information and error logs
- Check if the bug has already been reported

### **Suggesting Enhancements**
- Use the GitHub issue tracker with the "enhancement" label
- Describe the problem and proposed solution
- Consider the impact on existing functionality
- Provide mockups or examples if applicable

### **Code Contributions**
- Fork the repository
- Create a feature branch
- Make your changes
- Add tests for new functionality
- Ensure all tests pass
- Submit a pull request

## 🛠️ **Development Setup**

### **Prerequisites**
- Python 3.8+
- Git
- Virtual environment tool
- Code editor (VS Code recommended)

### **Setup Steps**
```bash
# 1. Fork and clone the repository
git clone https://github.com/yourusername/pdf_summarizer.git
cd pdf_summarizer

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 3. Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# 4. Set up environment variables
copy env_config.txt .env
# Edit .env with your API keys

# 5. Run migrations
python manage.py migrate

# 6. Create superuser for testing
python manage.py createsuperuser

# 7. Start development server
python manage.py runserver
```

### **Development Tools**
- **VS Code Extensions**: Python, Django, GitLens
- **Linting**: flake8, black, isort
- **Testing**: pytest, coverage
- **Git Hooks**: pre-commit hooks for code quality

## 🔄 **Pull Request Process**

### **Before Submitting**
1. **Fork the repository** and create a feature branch
2. **Make your changes** following coding standards
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass** locally

### **Pull Request Guidelines**
- **Title**: Clear, descriptive title
- **Description**: Detailed explanation of changes
- **Related Issues**: Link to relevant issues
- **Screenshots**: Include UI changes if applicable
- **Testing**: Describe how to test the changes

### **Review Process**
- All PRs require at least one review
- Address review comments promptly
- Maintainers may request changes
- PRs are merged after approval

## 📝 **Coding Standards**

### **Python Code Style**
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Maximum line length: 88 characters (black formatter)
- Use meaningful variable and function names

### **Django Best Practices**
- Follow Django coding style
- Use class-based views when appropriate
- Implement proper error handling
- Use Django forms for data validation

### **Code Organization**
- Keep functions and classes focused
- Use meaningful docstrings
- Organize imports properly
- Separate business logic from views

### **Example Code Structure**
```python
"""
Module for handling PDF document operations.

This module provides functionality for uploading, processing,
and summarizing PDF documents using various AI models.
"""

from typing import Dict, List, Optional
from django.core.exceptions import ValidationError
from .models import PDFDocument
from .utils import extract_text_from_pdf


def process_pdf_document(pdf_file, user) -> Dict[str, str]:
    """
    Process a PDF document and generate summaries.
    
    Args:
        pdf_file: Uploaded PDF file
        user: User who uploaded the file
        
    Returns:
        Dictionary containing summary results
        
    Raises:
        ValidationError: If file processing fails
    """
    try:
        # Extract text from PDF
        text_content = extract_text_from_pdf(pdf_file)
        
        # Generate summaries
        summaries = generate_summaries(text_content)
        
        return summaries
        
    except Exception as e:
        raise ValidationError(f"Failed to process PDF: {str(e)}")
```

## 🧪 **Testing Guidelines**

### **Test Structure**
- Unit tests for individual functions
- Integration tests for API endpoints
- Model tests for database operations
- View tests for user interactions

### **Test Naming**
```python
def test_extract_text_from_pdf_success():
    """Test successful text extraction from PDF."""
    pass

def test_extract_text_from_pdf_invalid_file():
    """Test text extraction with invalid file format."""
    pass

def test_extract_text_from_pdf_empty_file():
    """Test text extraction with empty PDF file."""
    pass
```

### **Running Tests**
```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test summarizer.tests.test_models

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### **Test Data**
- Use factories for test data creation
- Avoid hardcoded test data
- Clean up test data after tests
- Use realistic test scenarios

## 📚 **Documentation**

### **Code Documentation**
- Use docstrings for all functions and classes
- Follow Google docstring format
- Include examples in docstrings
- Document complex algorithms

### **API Documentation**
- Document all API endpoints
- Include request/response examples
- Document error codes and messages
- Keep documentation up to date

### **User Documentation**
- Update README.md for new features
- Include screenshots for UI changes
- Provide step-by-step guides
- Document configuration options

## 🔍 **Code Review Checklist**

### **Functionality**
- [ ] Does the code work as intended?
- [ ] Are edge cases handled?
- [ ] Is error handling appropriate?
- [ ] Are there any security concerns?

### **Code Quality**
- [ ] Is the code readable and maintainable?
- [ ] Are there any code smells?
- [ ] Is the code properly documented?
- [ ] Are there any performance issues?

### **Testing**
- [ ] Are there adequate tests?
- [ ] Do all tests pass?
- [ ] Is test coverage sufficient?
- [ ] Are tests meaningful and focused?

### **Documentation**
- [ ] Is the code properly documented?
- [ ] Are API changes documented?
- [ ] Is the README updated?
- [ ] Are there inline comments where needed?

## ❓ **Questions or Problems?**

### **Getting Help**
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: For private or sensitive matters
- **Documentation**: Check existing docs first

### **Community Guidelines**
- Be respectful and inclusive
- Help others when possible
- Share knowledge and experiences
- Follow the project's code of conduct

## 🎯 **Areas for Contribution**

### **High Priority**
- Bug fixes and performance improvements
- Security enhancements
- Documentation improvements
- Test coverage expansion

### **Medium Priority**
- New language support
- Additional AI model integrations
- UI/UX improvements
- API enhancements

### **Low Priority**
- Code refactoring
- Performance optimizations
- Additional features
- Integration examples

## 📈 **Recognition**

Contributors will be recognized in:
- GitHub contributors list
- Project documentation
- Release notes
- Community acknowledgments

---

**Thank you for contributing to PDF Summarizer! 🎉**

Your contributions help make this project better for everyone in the community.
