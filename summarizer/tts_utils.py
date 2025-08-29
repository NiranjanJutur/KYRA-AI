import os
import tempfile
import logging
from gtts import gTTS
from django.conf import settings
from django.http import FileResponse
import uuid

logger = logging.getLogger(__name__)

# Language code mapping for gTTS
LANGUAGE_MAPPING = {
    'en': 'en',
    'hi': 'hi',
    'ta': 'ta',
    'te': 'te',
    'mr': 'mr',
    'bn': 'bn',
    'gu': 'gu',
    'kn': 'kn',
    'ml': 'ml',
    'pa': 'pa',
    'ur': 'ur',
    'es': 'es',
    'fr': 'fr',
    'de': 'de',
    'it': 'it',
    'pt': 'pt',
    'ru': 'ru',
    'zh': 'zh',
    'ja': 'ja',
    'ko': 'ko',
    'th': 'th',
    'vi': 'vi',
    'ar': 'ar',
    'fa': 'fa',
    'tr': 'tr'
}

def text_to_speech(text, language_code='en', slow=False):
    """
    Convert text to speech and return the audio file path
    
    Args:
        text (str): Text to convert to speech
        language_code (str): Language code for the text
        slow (bool): Whether to speak slowly (useful for learning)
    
    Returns:
        dict: Dictionary with status and file path or error message
    """
    try:
        if not text or len(text.strip()) == 0:
            return {'status': 'error', 'message': 'No text provided for speech conversion'}
        
        # Clean and prepare text for TTS
        text = text.strip()
        
        # Handle special characters and encoding issues
        try:
            # Ensure text is properly encoded
            text = text.encode('utf-8').decode('utf-8')
        except UnicodeError:
            # If encoding fails, try to clean the text
            text = ''.join(char for char in text if ord(char) < 65536)
        
        # Map language code to gTTS language code
        gtts_lang = LANGUAGE_MAPPING.get(language_code, 'en')
        
        # Validate language code
        if gtts_lang not in LANGUAGE_MAPPING.values():
            logger.warning(f"Unsupported language code: {language_code}, falling back to English")
            gtts_lang = 'en'
        
        # Create a unique filename
        filename = f"speech_{uuid.uuid4().hex}.mp3"
        
        # Create media directory for speech files if it doesn't exist
        speech_dir = os.path.join(settings.MEDIA_ROOT, 'speech')
        os.makedirs(speech_dir, exist_ok=True)
        
        file_path = os.path.join(speech_dir, filename)
        
        # Convert text to speech with error handling
        try:
            tts = gTTS(text=text, lang=gtts_lang, slow=slow)
            tts.save(file_path)
            
            # Verify file was created
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise Exception("Audio file was not created or is empty")
                
        except Exception as tts_error:
            logger.error(f"gTTS error for language {gtts_lang}: {str(tts_error)}")
            
            # Fallback to English if the target language fails
            if gtts_lang != 'en':
                logger.info(f"Falling back to English for text: {text[:100]}...")
                try:
                    tts = gTTS(text=text, lang='en', slow=slow)
                    tts.save(file_path)
                except Exception as fallback_error:
                    logger.error(f"Fallback to English also failed: {str(fallback_error)}")
                    raise fallback_error
            else:
                raise tts_error
        
        # Return the relative path for URL generation
        relative_path = os.path.join('speech', filename)
        
        logger.info(f"Successfully generated speech for text in {language_code} (file: {filename})")
        return {
            'status': 'success',
            'file_path': relative_path,
            'full_path': file_path
        }
        
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return {
            'status': 'error',
            'message': f'Failed to convert text to speech: {str(e)}'
        }

def get_speech_url(file_path):
    """
    Generate URL for speech file
    
    Args:
        file_path (str): Relative path to the speech file
    
    Returns:
        str: Full URL to the speech file
    """
    return f"{settings.MEDIA_URL}{file_path}"

def cleanup_speech_file(file_path):
    """
    Clean up speech file after use
    
    Args:
        file_path (str): Full path to the speech file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up speech file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up speech file: {str(e)}")
