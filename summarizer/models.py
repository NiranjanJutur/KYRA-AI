from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class PDFDocument(models.Model):
    SUMMARY_CHOICES = [
        ('bert_gpt2', 'BERT & GPT-2'),
        ('gemini', 'Google Gemini')
    ]
    
    LANGUAGE_CHOICES = [
        # English
        ('en', 'English'),
        
        # Indian Languages
        ('hi', 'Hindi'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('mr', 'Marathi'),
        ('bn', 'Bengali'),
        ('gu', 'Gujarati'),
        ('kn', 'Kannada'),
        ('ml', 'Malayalam'),
        ('pa', 'Punjabi'),
        ('ur', 'Urdu'),
        
        # European Languages
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ru', 'Russian'),
        
        # Asian Languages
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
        ('th', 'Thai'),
        ('vi', 'Vietnamese'),
        
        # Middle Eastern Languages
        ('ar', 'Arabic'),
        ('fa', 'Persian'),
        ('tr', 'Turkish')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdfs')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    summary_type = models.CharField(max_length=20, choices=SUMMARY_CHOICES, default='bert_gpt2')
    bert_summary = models.TextField(blank=True, null=True)
    gpt2_summary = models.TextField(blank=True, null=True)
    gemini_summary = models.TextField(blank=True, null=True)
    current_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    translated_summary = models.TextField(blank=True, null=True)
    questions = models.TextField(blank=True, null=True, help_text='User questions related to the PDF')
    answers = models.TextField(blank=True, null=True, help_text='Answers to user questions related to the PDF')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-uploaded_at']


class ImageDocument(models.Model):
    ANALYSIS_SOURCE_CHOICES = [
        ('google_vision', 'Google Cloud Vision'),
        ('tesseract_ocr', 'Tesseract OCR'),
        ('ocr_description', 'OCR Description'),
        ('error', 'Error')
    ]
    
    IMAGE_TYPE_CHOICES = [
        ('general', 'General Image'),
        ('document', 'Document'),
        ('technical_diagram', 'Technical Diagram'),
        ('diagram', 'Diagram/Chart'),
        ('banner_or_poster', 'Banner/Poster'),
        ('unknown', 'Unknown')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='images')
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    # Text extraction results
    summary = models.TextField(blank=True, null=True, help_text='Comprehensive image summary')
    extracted_text = models.TextField(blank=True, null=True, help_text='Raw extracted text from image')
    
    # Analysis metadata
    labels = models.TextField(blank=True, null=True, help_text='Comma-separated list of detected labels')
    detected_objects = models.TextField(blank=True, null=True, help_text='Comma-separated list of detected objects')
    faces_detected = models.IntegerField(default=0, help_text='Number of faces detected in the image')
    
    # Classification and confidence
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPE_CHOICES, default='unknown')
    analysis_confidence = models.FloatField(default=0.0, help_text='Confidence score of the analysis (0-1)')
    
    # Analysis source and processing details
    analysis_source = models.CharField(
        max_length=20,
        choices=ANALYSIS_SOURCE_CHOICES,
        default='tesseract_ocr',
        help_text='Source of the image analysis'
    )
    processing_variant = models.CharField(max_length=50, blank=True, null=True, help_text='Image processing variant used')
    ocr_config = models.TextField(blank=True, null=True, help_text='OCR configuration used (JSON)')
    
    # Image properties
    image_width = models.IntegerField(default=0, help_text='Image width in pixels')
    image_height = models.IntegerField(default=0, help_text='Image height in pixels')
    color_type = models.CharField(max_length=50, blank=True, null=True, help_text='Color type description')
    edge_density = models.FloatField(default=0.0, help_text='Edge density in the image')
    text_density = models.FloatField(default=0.0, help_text='Text density in the image')
    
    # Text analysis
    word_count = models.IntegerField(default=0, help_text='Number of words extracted')
    character_count = models.IntegerField(default=0, help_text='Number of characters extracted')
    text_quality = models.CharField(max_length=20, default='unknown', help_text='Quality assessment of extracted text')
    
    # Language support
    current_language = models.CharField(max_length=5, choices=PDFDocument.LANGUAGE_CHOICES, default='en')
    translated_summary = models.TextField(blank=True, null=True, help_text='Translated summary')
    
    # Detailed analysis data (JSON)
    classification_data = models.JSONField(blank=True, null=True, help_text='Detailed classification results')
    analysis_data = models.JSONField(blank=True, null=True, help_text='Comprehensive analysis data')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-uploaded_at']
    
    def get_analysis_summary(self):
        """Get a human-readable summary of the analysis"""
        summary_parts = []
        
        if self.image_type != 'unknown':
            summary_parts.append(f"Image Type: {self.get_image_type_display()}")
        
        if self.analysis_confidence > 0:
            summary_parts.append(f"Confidence: {self.analysis_confidence:.1%}")
        
        if self.word_count > 0:
            summary_parts.append(f"Words Extracted: {self.word_count}")
        
        if self.faces_detected > 0:
            summary_parts.append(f"Faces Detected: {self.faces_detected}")
        
        if self.labels:
            label_count = len(self.labels.split(','))
            summary_parts.append(f"Labels: {label_count}")
        
        return " | ".join(summary_parts) if summary_parts else "No analysis data available"
    
    def get_text_preview(self, max_length=200):
        """Get a preview of the extracted text"""
        if self.extracted_text:
            text = self.extracted_text.strip()
            if len(text) > max_length:
                return text[:max_length] + "..."
            return text
        return "No text extracted"
    
    def get_labels_list(self):
        """Get labels as a list"""
        if self.labels:
            return [label.strip() for label in self.labels.split(',') if label.strip()]
        return []
    
    def get_objects_list(self):
        """Get detected objects as a list"""
        if self.detected_objects:
            return [obj.strip() for obj in self.detected_objects.split(',') if obj.strip()]
        return []