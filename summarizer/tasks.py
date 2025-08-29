from celery import shared_task
from deep_translator import GoogleTranslator
from .models import PDFDocument
import logging

logger = logging.getLogger(__name__)

@shared_task
def translate_summary_task(pdf_id, language):
    try:
        pdf = PDFDocument.objects.get(pk=pdf_id)
        
        # Get the appropriate summary based on what's available
        original_summary = None
        if pdf.gemini_summary:
            original_summary = pdf.gemini_summary
        elif pdf.bert_summary:
            original_summary = pdf.bert_summary
        else:
            return {'status': 'error', 'message': 'No summary available to translate'}

        if not original_summary or len(original_summary.strip()) == 0:
            return {'status': 'error', 'message': 'No summary available to translate'}

        # Translate the summary
        translator = GoogleTranslator(source='auto', target=language)
        translated = translator.translate(original_summary)
        
        # Update the PDF document
        pdf.translated_summary = translated
        pdf.current_language = language
        pdf.save()
        
        logger.info(f"Successfully translated PDF {pdf_id} to {language}")
        return {'status': 'success', 'language': language}
        
    except PDFDocument.DoesNotExist:
        logger.error(f"PDF with id {pdf_id} not found")
        return {'status': 'error', 'message': 'PDF not found'}
    except Exception as e:
        logger.error(f"Translation error for PDF {pdf_id}: {str(e)}")
        return {'status': 'error', 'message': f'Translation failed: {str(e)}'}

def translate_text_sync(text, target_language):
    """
    Synchronous translation function that doesn't require Celery
    """
    try:
        if not text or len(text.strip()) == 0:
            return {'status': 'error', 'message': 'No text to translate'}
        
        translator = GoogleTranslator(source='auto', target=target_language)
        translated = translator.translate(text)
        
        return {'status': 'success', 'translated_text': translated}
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return {'status': 'error', 'message': f'Translation failed: {str(e)}'}