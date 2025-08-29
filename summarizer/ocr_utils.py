import os
from PIL import Image
import shutil
import sys
import logging
import numpy as np
import cv2
from io import BytesIO
try:
    from google.cloud import vision
except Exception:
    vision = None
from django.conf import settings
import re
import json
from typing import Dict, List, Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Google Cloud Vision client (optional)
vision_client = None
try:
    if vision and os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        vision_client = vision.ImageAnnotatorClient()
        logger.info('Successfully initialized Google Cloud Vision client')
    else:
        logger.info('Google Cloud Vision not available or credentials missing. Using Tesseract OCR.')
except Exception:
    logger.info('Google Cloud Vision initialization failed. Using Tesseract OCR.')
    vision_client = None

def enhance_image_quality(image: Image.Image, enhancement_type: str = 'auto') -> Tuple[Image.Image, List[Image.Image]]:
    """
    Enhanced image preprocessing with multiple techniques for better OCR results
    
    Args:
        image: PIL Image object
        enhancement_type: Type of enhancement ('auto', 'text', 'technical', 'document')
        
    Returns:
        Tuple of (best_processed_image, list_of_all_processed_images)
    """
    try:
        # Convert PIL image to OpenCV format
        # Downscale very large images to speed up processing (keep aspect ratio)
        max_dim = 1600
        if max(image.size) > max_dim:
            scale = max_dim / float(max(image.size))
            new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
            image = image.resize(new_size)
        img_np = np.array(image)
        
        # Convert to grayscale and ensure uint8
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
        gray = np.ascontiguousarray(gray.astype(np.uint8))
        
        processed_images = []
        
        # 1. Basic adaptive thresholding
        thresh_adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(('adaptive_threshold', Image.fromarray(thresh_adaptive)))
        
        # 2. Otsu's thresholding
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('otsu_threshold', Image.fromarray(thresh_otsu)))
        
        # 3. Bilateral filtering for noise reduction
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        _, bilateral_thresh = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('bilateral_filter', Image.fromarray(bilateral_thresh)))
        
        # 4. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        clahe_img = clahe.apply(gray)
        _, clahe_thresh = cv2.threshold(clahe_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('clahe', Image.fromarray(clahe_thresh)))
        
        # 5. Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        opening = cv2.morphologyEx(thresh_adaptive, cv2.MORPH_OPEN, kernel)
        processed_images.append(('morphological_opening', Image.fromarray(opening)))
        
        # 6. Edge enhancement for technical images
        if enhancement_type in ['technical', 'auto']:
            edges = cv2.Canny(gray, 100, 200)
            dilated_edges = cv2.dilate(edges, np.ones((2,2), np.uint8), iterations=1)
            edge_enhanced = cv2.addWeighted(gray, 0.7, dilated_edges, 0.3, 0)
            _, edge_thresh = cv2.threshold(edge_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(('edge_enhanced', Image.fromarray(edge_thresh)))
        
        # 7. Gaussian blur + threshold for noisy images
        gaussian_blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, gaussian_thresh = cv2.threshold(gaussian_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('gaussian_blur', Image.fromarray(gaussian_thresh)))
        
        # 8. Median blur for salt-and-pepper noise
        median_blur = cv2.medianBlur(gray, 5)
        _, median_thresh = cv2.threshold(median_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('median_blur', Image.fromarray(median_thresh)))

        # Limit number of variants to speed up processing
        processed_images = processed_images[:4]
        
        # Return the first processed image as default, along with all variants
        return processed_images[0][1], [img for _, img in processed_images]
        
    except Exception as e:
        logger.warning(f"Image enhancement failed: {str(e)}. Using original image.")
        return image, [image]

def classify_image_content(image: Image.Image) -> Dict[str, any]:
    """
    Advanced image classification to determine content type and processing strategy
    
    Args:
        image: PIL Image object
        
    Returns:
        Dict containing classification results
    """
    try:
        img_np = np.array(image)
        
        # Basic image properties
        height, width = img_np.shape[:2] if len(img_np.shape) > 1 else img_np.shape
        aspect_ratio = float(width) / float(height)
        is_color = bool(len(img_np.shape) == 3 and img_np.shape[2] == 3)
        
        # Convert to grayscale for analysis and ensure uint8
        if is_color:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
        gray = np.ascontiguousarray(gray.astype(np.uint8))
        
        # Edge analysis
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.sum(edges > 0)) / float(edges.shape[0] * edges.shape[1])
        
        # Text detection using contours
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size (typical text size)
        text_contours = [c for c in contours if 10 < cv2.contourArea(c) < 1000]
        text_density = float(len(text_contours)) / float(gray.shape[0] * gray.shape[1])
        
        # Color analysis for color images
        color_info = {}
        if is_color:
            hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            avg_hue = float(np.mean(hsv[:,:,0]))
            avg_sat = float(np.mean(hsv[:,:,1]))
            avg_val = float(np.mean(hsv[:,:,2]))
            
            color_info = {
                'avg_hue': float(avg_hue),
                'avg_saturation': float(avg_sat),
                'avg_value': float(avg_val),
                'is_colorful': bool(avg_sat > 50)
            }
        
        # Determine image type
        image_type = 'general'
        confidence = 0.5
        
        if edge_density > 0.15 and text_density < 0.005:
            image_type = 'technical_diagram'
            confidence = 0.8
        elif text_density > 0.01:
            image_type = 'document'
            confidence = 0.9
        elif edge_density > 0.1:
            image_type = 'diagram'
            confidence = 0.7
        elif aspect_ratio > 2 or aspect_ratio < 0.5:
            image_type = 'banner_or_poster'
            confidence = 0.6
        
        return {
            'image_type': image_type,
            'confidence': float(confidence),
            'edge_density': float(edge_density),
            'text_density': float(text_density),
            'aspect_ratio': float(aspect_ratio),
            'is_color': bool(is_color),
            'color_info': color_info,
            'dimensions': {'width': int(width), 'height': int(height)}
        }
        
    except Exception as e:
        logger.warning(f"Image classification failed: {str(e)}")
        return {
            'image_type': 'general',
            'confidence': 0.3,
            'error': str(e)
        }

def extract_text_with_multiple_techniques(image: Image.Image, classification: Dict) -> Dict[str, any]:
    """
    Extract text using multiple OCR techniques and preprocessing methods
    
    Args:
        image: PIL Image object
        classification: Image classification results
        
    Returns:
        Dict containing extraction results
    """
    try:
        import pytesseract
        
        # Configure Tesseract path if needed
        tesseract_cmd = shutil.which('tesseract')
        if not tesseract_cmd:
            common_locations = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract'
            ]
            
            for location in common_locations:
                if os.path.exists(location):
                    pytesseract.pytesseract.tesseract_cmd = location
                    break
            else:
                raise Exception("Tesseract not found")
        
        # Get enhanced image variants
        best_image, all_variants = enhance_image_quality(image, classification['image_type'])
        
        # OCR configuration options
        # Trimmed OCR configurations for performance
        ocr_configs = [
            {'psm': 6, 'lang': 'eng'},  # Uniform block of text
            {'psm': 3, 'lang': 'eng'},  # Fully automatic page segmentation
            {'psm': 11, 'lang': 'eng'}, # Sparse text with OSD
        ]
        
        # Add technical configurations for technical images
        if classification['image_type'] in ['technical_diagram', 'diagram']:
            ocr_configs.extend([
                {'psm': 6, 'lang': 'eng+equ'},  # English + equations
                {'psm': 6, 'lang': 'eng+osd'},  # English + orientation detection
            ])
        
        best_result = {
            'text': '',
            'confidence': 0,
            'config': None,
            'variant': 'original'
        }
        
        # Test all combinations of image variants and OCR configs
        for variant_idx, variant_img in enumerate([image] + all_variants):
            variant_name = 'original' if variant_idx == 0 else f'variant_{variant_idx}'
            
            for config in ocr_configs:
                try:
                    # Build config string
                    config_str = f"--psm {config['psm']} -l {config['lang']}"
                    
                    # Extract text
                    result = pytesseract.image_to_string(variant_img, config=config_str)
                    
                    # Calculate confidence based on text quality
                    text_quality = calculate_text_quality(result)
                    
                    if text_quality > best_result['confidence']:
                        best_result = {
                            'text': result,
                            'confidence': text_quality,
                            'config': config,
                            'variant': variant_name
                        }

                    # Early exit if quality is already good enough
                    if best_result['confidence'] >= 0.75:
                        return best_result
                        
                except Exception as e:
                    logger.debug(f"OCR failed for variant {variant_name} with config {config}: {str(e)}")
                    continue
        
        return best_result
        
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return {
            'text': '',
            'confidence': 0,
            'error': str(e)
        }

def calculate_text_quality(text: str) -> float:
    """
    Calculate the quality score of extracted text
    
    Args:
        text: Extracted text
        
    Returns:
        Quality score between 0 and 1
    """
    if not text or not text.strip():
        return 0.0
    
    # Clean the text
    clean_text = text.strip()
    words = clean_text.split()
    
    if len(words) == 0:
        return 0.0
    
    # Calculate various quality metrics
    word_count = len(words)
    avg_word_length = sum(len(word) for word in words) / word_count
    
    # Check for common OCR artifacts
    artifact_patterns = [
        r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]',  # Unusual characters
        r'\b[a-zA-Z]{1}\b',  # Single letters
        r'\b[a-zA-Z]{20,}\b',  # Very long words
    ]
    
    artifact_score = 0
    for pattern in artifact_patterns:
        matches = len(re.findall(pattern, clean_text))
        artifact_score += matches / word_count if word_count > 0 else 0
    
    # Calculate readability score
    sentence_count = len(re.split(r'[.!?]+', clean_text))
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else word_count
    
    # Normalize scores
    word_score = min(word_count / 10, 1.0)  # Cap at 10 words
    length_score = min(avg_word_length / 8, 1.0)  # Optimal word length around 8
    sentence_score = min(avg_sentence_length / 20, 1.0)  # Optimal sentence length around 20
    artifact_penalty = min(artifact_score, 0.5)  # Cap penalty at 50%
    
    # Combine scores
    quality_score = (word_score * 0.3 + length_score * 0.2 + sentence_score * 0.2) * (1 - artifact_penalty)
    
    return max(0.0, min(1.0, quality_score))

def generate_comprehensive_image_summary(image: Image.Image, extracted_text: str, classification: Dict) -> Dict[str, any]:
    """
    Generate a comprehensive summary of the image content
    
    Args:
        image: PIL Image object
        extracted_text: Extracted text from the image
        classification: Image classification results
        
    Returns:
        Dict containing comprehensive analysis
    """
    try:
        img_np = np.array(image)
        
        # Basic image analysis
        height, width = img_np.shape[:2] if len(img_np.shape) > 1 else img_np.shape
        is_color = len(img_np.shape) == 3 and img_np.shape[2] == 3
        
        # Color analysis
        color_description = "grayscale"
        if is_color:
            hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            avg_hue = np.mean(hsv[:,:,0])
            avg_sat = np.mean(hsv[:,:,1])
            avg_val = np.mean(hsv[:,:,2])
            
            if avg_sat < 30:
                color_description = "grayscale or monochrome"
            else:
                # Map hue to color names
                if 0 <= avg_hue < 30 or 330 <= avg_hue <= 360:
                    color_description = "reddish"
                elif 30 <= avg_hue < 90:
                    color_description = "yellowish/greenish"
                elif 90 <= avg_hue < 150:
                    color_description = "greenish"
                elif 150 <= avg_hue < 210:
                    color_description = "cyan/blue"
                elif 210 <= avg_hue < 270:
                    color_description = "bluish/purple"
                else:
                    color_description = "magenta/pink"
        
        # Content analysis
        content_type = classification.get('image_type', 'general')
        edge_density = classification.get('edge_density', 0)
        text_density = classification.get('text_density', 0)
        
        # Generate content description
        content_description = ""
        if content_type == 'document':
            content_description = "document or text-heavy image"
        elif content_type == 'technical_diagram':
            content_description = "technical diagram or schematic"
        elif content_type == 'diagram':
            content_description = "diagram or chart"
        elif content_type == 'banner_or_poster':
            content_description = "banner, poster, or wide format image"
        else:
            content_description = "general image"
        
        # Text analysis
        text_analysis = {
            'has_text': len(extracted_text.strip()) > 0,
            'word_count': len(extracted_text.split()),
            'character_count': len(extracted_text),
            'text_quality': 'good' if len(extracted_text.split()) > 5 else 'limited'
        }
        
        # Generate summary
        summary_parts = []
        
        # Image type and content
        summary_parts.append(f"This appears to be a {color_description} {content_description}.")
        
        # Dimensions
        if width > height * 1.5:
            summary_parts.append("The image has a landscape orientation.")
        elif height > width * 1.5:
            summary_parts.append("The image has a portrait orientation.")
        else:
            summary_parts.append("The image has a square or near-square aspect ratio.")
        
        # Text content
        if text_analysis['has_text']:
            if text_analysis['word_count'] > 20:
                summary_parts.append(f"The image contains substantial text content ({text_analysis['word_count']} words).")
            elif text_analysis['word_count'] > 5:
                summary_parts.append(f"The image contains some text content ({text_analysis['word_count']} words).")
            else:
                summary_parts.append("The image contains limited text content.")
        else:
            summary_parts.append("No readable text was detected in the image.")
        
        # Technical features
        if edge_density > 0.1:
            summary_parts.append("The image contains technical elements or diagrams.")
        
        # Combine all parts
        full_summary = " ".join(summary_parts)
        
        return {
            'summary': full_summary,
            'text_analysis': text_analysis,
            'image_properties': {
                'dimensions': {'width': width, 'height': height},
                'color_type': color_description,
                'content_type': content_type,
                'edge_density': edge_density,
                'text_density': text_density
            },
            'extracted_text': extracted_text,
            'confidence': classification.get('confidence', 0.5)
        }
        
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        return {
            'summary': "Unable to generate comprehensive summary due to processing error.",
            'extracted_text': extracted_text,
            'error': str(e)
        }

def analyze_image_with_vision_api(image: Image.Image) -> Dict[str, any]:
    """
    Analyze image using Google Cloud Vision API
    
    Args:
        image: PIL Image object
        
    Returns:
        Dict: Analysis results including text, labels, and other detected features
    """
    try:
        if not vision_client:
            raise Exception("Google Cloud Vision client not initialized")
            
        # Convert PIL Image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Create image object
        vision_image = vision.Image(content=img_byte_arr)

        # Perform detection tasks
        text_detection = vision_client.text_detection(image=vision_image)
        label_detection = vision_client.label_detection(image=vision_image)
        object_detection = vision_client.object_localization(image=vision_image)
        face_detection = vision_client.face_detection(image=vision_image)
        
        # Extract results
        results = {
            'text': text_detection.text_annotations[0].description if text_detection.text_annotations else "",
            'labels': [label.description for label in label_detection.label_annotations],
            'objects': [obj.name for obj in object_detection.localized_object_annotations],
            'faces_detected': len(face_detection.face_annotations),
            'confidence': 0.9  # High confidence for Vision API
        }
        
        return results
    except Exception as e:
        logger.error(f"Google Cloud Vision API analysis failed: {str(e)}")
        return {'text': '', 'labels': [], 'objects': [], 'faces_detected': 0, 'confidence': 0}

def extract_text_from_image(image_file, image_type='auto'):
    """
    Enhanced text extraction from image with comprehensive analysis
    
    Args:
        image_file: File object or path to image
        image_type: Type of image ('auto', 'general', 'technical', 'document')
        
    Returns:
        dict: Comprehensive analysis results
    """
    try:
        # Check if pytesseract is installed
        try:
            import pytesseract  # noqa: F401
            pytesseract_available = True
        except ImportError:
            logger.warning("pytesseract module is not installed; falling back to description only")
            pytesseract_available = False
        
        # Handle both file objects and file paths
        if isinstance(image_file, str):
            if not os.path.exists(image_file):
                logger.error(f"Image file not found at {image_file}")
                return {
                    'success': False,
                    'error': f"Image file not found at {image_file}",
                    'text': '',
                    'labels': [],
                    'objects': [],
                    'source': 'error'
                }
            image = Image.open(image_file)
        else:
            image = Image.open(image_file)
        
        # Get image details
        width, height = image.size
        format_type = image.format
        mode = image.mode
        logger.info(f"Processing image: {width}x{height}, Format: {format_type}, Mode: {mode}")
        
        # Try Google Cloud Vision API first if available
        if vision_client:
            try:
                vision_results = analyze_image_with_vision_api(image)
                if vision_results['text'] or vision_results['labels']:
                    # Generate summary for Vision API results
                    classification = classify_image_content(image)
                    summary_results = generate_comprehensive_image_summary(
                        image, vision_results['text'], classification
                    )
                    
                    return {
                        'success': True,
                        'text': vision_results['text'],
                        'summary': summary_results['summary'],
                        'labels': vision_results['labels'],
                        'objects': vision_results['objects'],
                        'faces_detected': vision_results['faces_detected'],
                        'classification': classification,
                        'analysis': summary_results,
                        'source': 'google_vision',
                        'confidence': vision_results['confidence']
                    }
            except Exception as e:
                logger.warning(f"Google Vision API failed, falling back to OCR: {str(e)}")
        
        # Auto-detect image type if not specified
        if image_type == 'auto':
            classification = classify_image_content(image)
            image_type = classification['image_type']
            logger.info(f"Image classified as: {image_type}")
        else:
            classification = classify_image_content(image)
        
        extracted_text = ''
        extraction_confidence = 0.0
        ocr_config_used = None
        processing_variant = None

        if pytesseract_available:
            try:
                # Extract text using multiple techniques
                extraction_results = extract_text_with_multiple_techniques(image, classification)
                if extraction_results.get('error'):
                    raise Exception(extraction_results['error'])
                extracted_text = extraction_results['text']
                extraction_confidence = extraction_results.get('confidence', 0.0)
                ocr_config_used = extraction_results.get('config')
                processing_variant = extraction_results.get('variant')
            except Exception as e:
                # If OCR fails (e.g., tesseract missing), continue with description-only path
                logger.warning(f"OCR unavailable or failed, using description-only path: {str(e)}")

        # Generate comprehensive summary regardless of OCR availability
        summary_results = generate_comprehensive_image_summary(image, extracted_text, classification)
        
        # If minimal text detected, enhance the summary
        if len(extracted_text.strip().split()) < 5:
            logger.info("Minimal text detected, enhancing summary with image analysis")
            summary_results['summary'] += " The image appears to contain visual content that may not be easily readable as text."
        
        return {
            'success': True,
            'text': extracted_text,
            'summary': summary_results['summary'],
            'labels': [],
            'objects': [],
            'faces_detected': 0,
            'classification': classification,
            'analysis': summary_results,
            'source': 'tesseract_ocr' if pytesseract_available else 'ocr_description',
            'confidence': extraction_confidence,
            'ocr_config': ocr_config_used,
            'processing_variant': processing_variant
        }
        
    except Exception as e:
        # Final safety: still return a description-only summary if possible
        try:
            image = Image.open(image_file) if not isinstance(image_file, str) else Image.open(image_file)
            classification = classify_image_content(image)
            summary_results = generate_comprehensive_image_summary(image, '', classification)
            logger.warning(f"Falling back to description-only due to error: {str(e)}")
            return {
                'success': True,
                'text': '',
                'summary': summary_results['summary'],
                'labels': [],
                'objects': [],
                'faces_detected': 0,
                'classification': classification,
                'analysis': summary_results,
                'source': 'ocr_description',
                'confidence': 0.0
            }
        except Exception:
            logger.exception(f"Error in enhanced OCR processing: {str(e)}")
            return {
                'success': False,
                'error': f"Error extracting text from image: {str(e)}",
                'text': '',
                'labels': [],
                'objects': [],
                'source': 'error'
            }