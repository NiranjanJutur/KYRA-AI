# 🔌 PDF Summarizer - API Documentation

## 📋 **Overview**

The PDF Summarizer API provides RESTful endpoints for document processing, text extraction, summarization, and translation services. This API is designed for both web applications and third-party integrations.

## 🔑 **Authentication**

### **Authentication Methods**

#### **Session-Based Authentication (Default)**
```bash
# Login to get session cookie
POST /login/
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

#### **JWT Token Authentication (Optional)**
```bash
# Get JWT token
POST /api/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}

# Use token in headers
Authorization: Bearer <your_jwt_token>
```

### **API Keys (for External Services)**
```bash
# Set in request headers
X-API-Key: your_api_key_here
```

## 📚 **Core Endpoints**

### **1. PDF Document Management**

#### **Upload PDF Document**
```http
POST /upload-pdf/
Content-Type: multipart/form-data

Parameters:
- file: PDF file (required)
- title: Document title (optional)
- summary_type: 'bert_gpt2' or 'gemini' (default: 'bert_gpt2')

Response:
{
    "status": "success",
    "message": "PDF uploaded successfully",
    "pdf_id": 123,
    "title": "Document Title",
    "uploaded_at": "2024-01-15T10:30:00Z"
}
```

#### **Get PDF Document**
```http
GET /pdfs/{pdf_id}/

Response:
{
    "id": 123,
    "title": "Document Title",
    "file_url": "/media/pdfs/document.pdf",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "summary_type": "bert_gpt2",
    "bert_summary": "BERT summary content...",
    "gpt2_summary": "GPT-2 summary content...",
    "gemini_summary": "Gemini summary content...",
    "current_language": "en",
    "translated_summary": null,
    "questions": [],
    "answers": []
}
```

#### **List PDF Documents**
```http
GET /pdfs/

Query Parameters:
- page: Page number (default: 1)
- page_size: Items per page (default: 10)
- search: Search in titles (optional)
- summary_type: Filter by summary type (optional)

Response:
{
    "count": 25,
    "next": "http://localhost:8000/pdfs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 123,
            "title": "Document Title",
            "uploaded_at": "2024-01-15T10:30:00Z",
            "summary_type": "bert_gpt2"
        }
    ]
}
```

#### **Delete PDF Document**
```http
DELETE /pdfs/{pdf_id}/

Response:
{
    "status": "success",
    "message": "PDF deleted successfully"
}
```

### **2. Image Processing & OCR**

#### **Upload Image for OCR**
```http
POST /upload-image/
Content-Type: multipart/form-data

Parameters:
- image: Image file (required, JPG, PNG, PDF)
- title: Image title (optional)
- analysis_source: 'tesseract_ocr' or 'google_vision' (default: 'tesseract_ocr')

Response:
{
    "status": "success",
    "message": "Image uploaded successfully",
    "image_id": 456,
    "title": "Image Title",
    "uploaded_at": "2024-01-15T10:30:00Z"
}
```

#### **Get Image Analysis Results**
```http
GET /images/{image_id}/

Response:
{
    "id": 456,
    "title": "Image Title",
    "image_url": "/media/images/image.jpg",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "analysis_source": "tesseract_ocr",
    "extracted_text": "Extracted text content...",
    "confidence_score": 0.95,
    "image_type": "document",
    "analysis_confidence": 0.92,
    "analysis_description": "Document containing technical specifications",
    "current_language": "en",
    "translated_text": null
}
```

#### **List Images**
```http
GET /images/

Query Parameters:
- page: Page number (default: 1)
- page_size: Items per page (default: 10)
- search: Search in titles (optional)
- image_type: Filter by image type (optional)

Response:
{
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 456,
            "title": "Image Title",
            "uploaded_at": "2024-01-15T10:30:00Z",
            "image_type": "document"
        }
    ]
}
```

### **3. Summarization Services**

#### **Generate Summary**
```http
POST /generate-summary/
Content-Type: application/json

{
    "pdf_id": 123,
    "summary_type": "gemini",
    "custom_prompt": "Summarize this document focusing on key technical details"
}

Response:
{
    "status": "success",
    "summary": "Generated summary content...",
    "summary_type": "gemini",
    "processing_time": 2.5,
    "confidence_score": 0.94
}
```

#### **Regenerate Summary**
```http
POST /pdfs/{pdf_id}/regenerate-summary/
Content-Type: application/json

{
    "summary_type": "bert_gpt2"
}

Response:
{
    "status": "success",
    "message": "BERT/GPT-2 summary regenerated successfully!"
}
```

### **4. Translation Services**

#### **Translate Text**
```http
POST /translate/
Content-Type: application/json

{
    "text": "Text to translate",
    "source_language": "en",
    "target_language": "es",
    "translation_engine": "google"
}

Response:
{
    "status": "success",
    "translated_text": "Texto traducido",
    "source_language": "en",
    "target_language": "es",
    "confidence": 0.98
}
```

#### **Translate Summary**
```http
POST /pdfs/{pdf_id}/translate-summary/
Content-Type: application/json

{
    "target_language": "fr"
}

Response:
{
    "status": "success",
    "translated_summary": "Résumé traduit...",
    "target_language": "fr",
    "translation_confidence": 0.96
}
```

### **5. Question-Answering System**

#### **Ask Question**
```http
POST /pdfs/{pdf_id}/ask-question/
Content-Type: application/json

{
    "question": "What are the main technical specifications mentioned?"
}

Response:
{
    "status": "success",
    "question": "What are the main technical specifications mentioned?",
    "answer": "Based on the document, the main technical specifications include...",
    "confidence_score": 0.87,
    "source_sections": ["Section 2.1", "Section 3.2"]
}
```

### **6. Text-to-Speech**

#### **Generate Speech**
```http
POST /generate-speech/
Content-Type: application/json

{
    "text": "Text to convert to speech",
    "language": "en",
    "voice_speed": "normal"
}

Response:
{
    "status": "success",
    "audio_url": "/media/speech/speech_123.mp3",
    "duration": "00:00:15",
    "file_size": "245KB"
}
```

## 🌍 **Language Support**

### **Supported Languages**

#### **Indian Languages**
```json
{
    "hi": "Hindi",
    "ta": "Tamil", 
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu"
}
```

#### **European Languages**
```json
{
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian"
}
```

#### **Asian Languages**
```json
{
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "th": "Thai",
    "vi": "Vietnamese"
}
```

#### **Middle Eastern Languages**
```json
{
    "ar": "Arabic",
    "fa": "Persian",
    "tr": "Turkish"
}
```

## 📊 **Error Handling**

### **Error Response Format**
```json
{
    "error": "Error message description",
    "error_code": "ERROR_CODE",
    "details": "Additional error details",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### **Common Error Codes**

#### **HTTP Status Codes**
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

#### **Application Error Codes**
- `INVALID_FILE_FORMAT`: Unsupported file type
- `FILE_TOO_LARGE`: File exceeds size limit
- `PROCESSING_FAILED`: Document processing error
- `API_LIMIT_EXCEEDED`: Rate limit exceeded
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions

### **Error Handling Examples**

#### **File Upload Error**
```json
{
    "error": "Invalid file format. Only PDF files are supported.",
    "error_code": "INVALID_FILE_FORMAT",
    "details": "Uploaded file has MIME type: image/jpeg",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### **Authentication Error**
```json
{
    "error": "Authentication credentials were not provided.",
    "error_code": "AUTHENTICATION_REQUIRED",
    "details": "Login required to access this resource",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔒 **Rate Limiting**

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642233600
```

### **Rate Limit Rules**
- **Free Tier**: 100 requests per hour
- **Premium Tier**: 1000 requests per hour
- **Enterprise Tier**: 10000 requests per hour

### **Rate Limit Exceeded Response**
```json
{
    "error": "Rate limit exceeded",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "details": "Limit: 1000 requests/hour, Reset: 1642233600",
    "retry_after": 3600
}
```

## 📱 **SDK & Libraries**

### **Python SDK**
```bash
pip install pdf-summarizer-sdk
```

```python
from pdf_summarizer import PDFSummarizer

# Initialize client
client = PDFSummarizer(api_key="your_api_key")

# Upload and process PDF
result = client.upload_pdf("document.pdf", title="My Document")
summary = client.generate_summary(result.pdf_id, "gemini")

# Translate summary
translated = client.translate_summary(result.pdf_id, "es")
```

### **JavaScript SDK**
```bash
npm install pdf-summarizer-js
```

```javascript
import { PDFSummarizer } from 'pdf-summarizer-js';

// Initialize client
const client = new PDFSummarizer({ apiKey: 'your_api_key' });

// Upload and process PDF
const result = await client.uploadPDF('document.pdf', { title: 'My Document' });
const summary = await client.generateSummary(result.pdfId, 'gemini');

// Translate summary
const translated = await client.translateSummary(result.pdfId, 'es');
```

## 🧪 **Testing & Examples**

### **cURL Examples**

#### **Upload PDF**
```bash
curl -X POST "http://localhost:8000/upload-pdf/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf" \
  -F "title=Sample Document" \
  -F "summary_type=gemini"
```

#### **Generate Summary**
```bash
curl -X POST "http://localhost:8000/generate-summary/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_id": 123,
    "summary_type": "gemini"
  }'
```

#### **Translate Text**
```bash
curl -X POST "http://localhost:8000/translate/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "source_language": "en",
    "target_language": "es"
  }'
```

### **Python Examples**

#### **Complete Workflow**
```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Login to get session
session = requests.Session()
login_data = {"username": "your_username", "password": "your_password"}
response = session.post(f"{BASE_URL}/login/", data=login_data)

# Upload PDF
with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {"title": "Sample Document", "summary_type": "gemini"}
    response = session.post(f"{BASE_URL}/upload-pdf/", files=files, data=data)
    pdf_data = response.json()
    pdf_id = pdf_data["pdf_id"]

# Generate summary
summary_data = {"pdf_id": pdf_id, "summary_type": "gemini"}
response = session.post(f"{BASE_URL}/generate-summary/", json=summary_data)
summary = response.json()

# Translate summary
translate_data = {"target_language": "es"}
response = session.post(f"{BASE_URL}/pdfs/{pdf_id}/translate-summary/", json=translate_data)
translated = response.json()

print(f"Summary: {summary['summary']}")
print(f"Translated: {translated['translated_summary']}")
```

## 📈 **Performance & Monitoring**

### **Response Time Metrics**
- **PDF Upload**: < 5 seconds
- **Summary Generation**: < 30 seconds
- **OCR Processing**: < 15 seconds
- **Translation**: < 3 seconds

### **Monitoring Endpoints**
```http
GET /health/
GET /metrics/
GET /status/
```

### **Health Check Response**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "services": {
        "database": "healthy",
        "redis": "healthy",
        "celery": "healthy",
        "external_apis": "healthy"
    },
    "version": "1.0.0"
}
```

## 🔄 **Webhooks**

### **Webhook Configuration**
```http
POST /webhooks/
Content-Type: application/json

{
    "url": "https://your-domain.com/webhook",
    "events": ["pdf.processed", "summary.generated"],
    "secret": "webhook_secret_key"
}
```

### **Webhook Events**
- `pdf.uploaded`: PDF file uploaded
- `pdf.processed`: PDF processing completed
- `summary.generated`: Summary generation completed
- `translation.completed`: Translation completed
- `ocr.completed`: OCR processing completed

### **Webhook Payload Example**
```json
{
    "event": "summary.generated",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "pdf_id": 123,
        "summary_type": "gemini",
        "processing_time": 2.5
    }
}
```

---

**This API documentation provides comprehensive coverage of all available endpoints, authentication methods, error handling, and integration examples for the PDF Summarizer platform.**
