/**
 * Common JavaScript functions for PDF Summarizer application
 * Contains shared functionality for translation and text-to-speech
 */

// Translation functionality
function translateText(text, targetLang) {
    // Show loading message
    const summaryContent = document.getElementById('summary-content');
    const originalContent = summaryContent.innerHTML;
    summaryContent.innerHTML = 
        '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Translating to ' + 
        document.getElementById('language-selector').options[document.getElementById('language-selector').selectedIndex].text + 
        '...</div>';
    
    // Get CSRF token
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Determine if we're on a PDF or image page
    const urlPath = window.location.pathname;
    let endpoint = '';
    let requestBody = '';
    
    console.log('Translating to language:', targetLang);
    console.log('Current URL path:', urlPath);
    
    if (urlPath.includes('/pdfs/')) {
        // Get the PDF ID from the URL
        const urlParts = urlPath.split('/');
        const pdfId = urlParts[urlParts.indexOf('pdfs') + 1];
        endpoint = `/pdfs/${pdfId}/update-language/`;
        requestBody = `language=${targetLang}`;
        console.log('PDF translation endpoint:', endpoint);
    } else if (urlPath.includes('/images/')) {
        // Get the image ID from the URL
        const urlParts = urlPath.split('/');
        const imageId = urlParts[urlParts.indexOf('images') + 1];
        endpoint = `/images/${imageId}/update-language/`;
        requestBody = `language=${targetLang}`;
        console.log('Image translation endpoint:', endpoint);
    } else {
        // Unknown page type
        showTranslationError(originalContent, 'Translation is not available on this page.');
        return;
    }
    
    // Make AJAX request to translate
    console.log('Sending translation request to:', endpoint);
    console.log('Request body:', requestBody);
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: requestBody
    })
    .then(response => {
        console.log('Translation response status:', response.status);
        if (!response.ok) {
            throw new Error('Translation failed with status: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        console.log('Translation response data:', data);
        if (data.status === 'success') {
            // Reload the page to show the translated content
            location.reload();
        } else if (data.status === 'timeout') {
            showTranslationError(originalContent, 'Translation timed out. The text might be too long. Please try again or try with a smaller document.');
        } else if (data.status === 'invalid_language') {
            showTranslationError(originalContent, 'Invalid language selected. Please choose a different language.');
        } else {
            showTranslationError(originalContent, data.message || 'Translation failed');
        }
    })
    .catch(error => {
        console.error('Translation error:', error);
        showTranslationError(originalContent, error.message);
    });
}

function showTranslationError(originalContent, message = 'Translation failed. Please try again later.') {
    const summaryContent = document.getElementById('summary-content');
    summaryContent.innerHTML = 
        `<div class="alert alert-danger mb-4"><i class="fas fa-exclamation-circle me-2"></i>${message}</div>` + 
        originalContent;
    
    // Add restore button
    const restoreBtn = document.createElement('button');
    restoreBtn.className = 'btn btn-outline-secondary btn-sm mt-2';
    restoreBtn.innerHTML = '<i class="fas fa-undo me-1"></i>Restore Original';
    restoreBtn.onclick = function() { restoreOriginal(); };
    
    document.querySelector('.alert-danger').appendChild(restoreBtn);
}

function restoreOriginal() {
    const summaryContent = document.getElementById('summary-content');
    const originalContent = document.getElementById('original-content');
    if (originalContent && summaryContent) {
        summaryContent.innerHTML = originalContent.value;
        document.getElementById('language-indicator').style.display = 'none';
    } else {
        // If original content is not available, reload the page
        location.reload();
    }
}

function updateLanguagePreference(language) {
    // Get CSRF token
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Make AJAX request to update language preference
    fetch('/update_language_preference/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            'language': language
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Language preference updated:', data);
    })
    .catch(error => {
        console.error('Error updating language preference:', error);
    });
}

// Text-to-speech functionality
let speechSynthesis = window.speechSynthesis;
let speechUtterance = null;

function speakText() {
    if (speechUtterance && speechSynthesis.speaking) {
        console.log('Speech already in progress');
        return;
    }
    
    // Get the text to speak
    const summaryContent = document.getElementById('summary-content');
    let textToSpeak = summaryContent.innerText || summaryContent.textContent;
    
    // Check if there's text to speak
    if (!textToSpeak || textToSpeak.trim() === '') {
        alert('No text available to speak');
        return;
    }
    
    // Create speech utterance
    speechUtterance = new SpeechSynthesisUtterance(textToSpeak);
    
    // Get selected language
    const languageSelector = document.getElementById('language-selector');
    const selectedLanguage = languageSelector.value;
    
    // Map language code to BCP 47 language tag
    const langMap = {
        'hi': 'hi-IN',  // Hindi
        'ta': 'ta-IN',  // Tamil
        'te': 'te-IN',  // Telugu
        'ml': 'ml-IN',  // Malayalam
        'bn': 'bn-IN',  // Bengali
        'gu': 'gu-IN',  // Gujarati
        'mr': 'mr-IN',  // Marathi
        'fr': 'fr-FR',  // French
        'de': 'de-DE',  // German
        'es': 'es-ES',  // Spanish
        'it': 'it-IT',  // Italian
        'pt': 'pt-PT',  // Portuguese
        'ru': 'ru-RU',  // Russian
        'zh-CN': 'zh-CN', // Chinese (Simplified)
        'ja': 'ja-JP',  // Japanese
        'ko': 'ko-KR',  // Korean
        'ar': 'ar-SA',  // Arabic
        'he': 'he-IL',  // Hebrew
        'tr': 'tr-TR',  // Turkish
        'th': 'th-TH',  // Thai
        'vi': 'vi-VN',  // Vietnamese
        'id': 'id-ID',  // Indonesian
        'ms': 'ms-MY',  // Malay
        'en': 'en-US',   // English (default)
        'kn': 'kn-IN' // Kannada
    };
    
    let voiceLang = langMap[selectedLanguage] || 'en-US'; // Default to en-US if not found
    
    // Find a suitable voice
    let voices = speechSynthesis.getVoices();
    console.log('Available voices:', voices);
    
    let selectedVoice = voices.find(voice => voice.lang === voiceLang);
    
    // Fallback for Indian languages if specific voice not found
    if (!selectedVoice && selectedLanguage === 'kn') {
        console.log('Kannada voice not found, trying hi-IN as fallback.');
        selectedVoice = voices.find(voice => voice.lang === 'hi-IN');
    }
    
    if (!selectedVoice) {
        console.log(`No specific voice found for ${voiceLang}, trying general ${voiceLang.substring(0, 2)} voice.`);
        selectedVoice = voices.find(voice => voice.lang.startsWith(voiceLang.substring(0, 2)));
    }
    
    if (!selectedVoice) {
        console.log('No suitable voice found, falling back to any available voice.');
        selectedVoice = voices[0]; // Take the first available voice as a last resort
    }
    
    if (selectedVoice) {
        speechUtterance.voice = selectedVoice;
        console.log('Using voice:', selectedVoice.name, '(', selectedVoice.lang, ')');
    } else {
        console.warn('No voices available on this browser.');
        alert('Text-to-speech is not supported or no voices are available in your browser.');
        return;
    }
    
    // Set speech properties
    speechUtterance.pitch = 1;
    speechUtterance.rate = 1;
    
    // Event handlers
    speechUtterance.onstart = function() {
        console.log('Speech started');
        document.getElementById('speaking-indicator').innerText = 'Speaking...';
        document.getElementById('play-button').style.display = 'none';
        document.getElementById('pause-button').style.display = 'inline-block';
        document.getElementById('stop-button').style.display = 'inline-block';
    };
    
    speechUtterance.onend = function() {
        console.log('Speech ended');
        document.getElementById('speaking-indicator').innerText = '';
        document.getElementById('play-button').style.display = 'inline-block';
        document.getElementById('pause-button').style.display = 'none';
        document.getElementById('stop-button').style.display = 'none';
    };
    
    speechUtterance.onerror = function(event) {
        console.error('Speech synthesis error:', event.error);
        document.getElementById('speaking-indicator').innerText = 'Error';
        alert('Speech synthesis error: ' + event.error);
        document.getElementById('play-button').style.display = 'inline-block';
        document.getElementById('pause-button').style.display = 'none';
        document.getElementById('stop-button').style.display = 'none';
    };
    
    // Speak the text
    speechSynthesis.speak(speechUtterance);
}

function pauseSpeech() {
    if (speechSynthesis.speaking && !speechSynthesis.paused) {
        speechSynthesis.pause();
        console.log('Speech paused');
        document.getElementById('speaking-indicator').innerText = 'Paused';
        document.getElementById('play-button').style.display = 'inline-block';
        document.getElementById('pause-button').style.display = 'none';
    }
}

function resumeSpeech() {
    if (speechSynthesis.paused) {
        speechSynthesis.resume();
        console.log('Speech resumed');
        document.getElementById('speaking-indicator').innerText = 'Speaking...';
        document.getElementById('play-button').style.display = 'none';
        document.getElementById('pause-button').style.display = 'inline-block';
    }
}

function stopSpeech() {
    if (speechSynthesis.speaking || speechSynthesis.paused) {
        speechSynthesis.cancel();
        console.log('Speech stopped');
        document.getElementById('speaking-indicator').innerText = '';
        document.getElementById('play-button').style.display = 'inline-block';
        document.getElementById('pause-button').style.display = 'none';
        document.getElementById('stop-button').style.display = 'none';
    }
}

// Ensure voices are loaded before trying to use them
window.speechSynthesis.onvoiceschanged = function() {
    console.log('Voices changed/loaded. Available voices:', window.speechSynthesis.getVoices().length);
};

// Event listeners for speech controls
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('play-button').addEventListener('click', speakText);
    document.getElementById('pause-button').addEventListener('click', pauseSpeech);
    document.getElementById('stop-button').addEventListener('click', stopSpeech);

    // Initial state of buttons
    document.getElementById('pause-button').style.display = 'none';
    document.getElementById('stop-button').style.display = 'none';

    // Store original content for translation restoration
    const summaryContentElement = document.getElementById('summary-content');
    if (summaryContentElement) {
        const originalContentInput = document.getElementById('original-content');
        if (originalContentInput) {
            originalContentInput.value = summaryContentElement.innerHTML;
        } else {
            // If original-content hidden input doesn't exist, create it dynamically
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.id = 'original-content';
            hiddenInput.value = summaryContentElement.innerHTML;
            document.body.appendChild(hiddenInput);
        }
    }

    // Language selector change event
    const languageSelector = document.getElementById('language-selector');
    if (languageSelector) {
        languageSelector.addEventListener('change', function() {
            const selectedLang = this.value;
            const currentSummaryText = document.getElementById('summary-content').innerText;
            translateText(currentSummaryText, selectedLang);
            updateLanguagePreference(selectedLang);
        });
    }

    // Check for translation status on page load
    const urlParams = new URLSearchParams(window.location.search);
    const translated = urlParams.get('translated');
    const lang = urlParams.get('lang');
    const originalContentElement = document.getElementById('original-content');
    const languageIndicator = document.getElementById('language-indicator');

    if (translated === 'true' && lang && originalContentElement && languageIndicator) {
        languageIndicator.innerText = `Translated to ${lang.toUpperCase()}`;
        languageIndicator.style.display = 'inline-block';

        const restoreBtn = document.createElement('button');
        restoreBtn.className = 'btn btn-outline-secondary btn-sm ms-2';
        restoreBtn.innerHTML = '<i class="fas fa-undo me-1"></i>Restore Original';
        restoreBtn.onclick = function() { restoreOriginal(); };
        languageIndicator.appendChild(restoreBtn);
    }
});