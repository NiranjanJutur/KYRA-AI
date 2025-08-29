import os
import json
import logging

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import PDFDocument, ImageDocument, UserProfile
from .forms import PDFUploadForm, ImageUploadForm, UserProfileForm
from .summarizer_utils import extract_text_from_pdf, get_bert_gpt2_summary, get_gemini_summary
from .ocr_utils import extract_text_from_image
from .tasks import translate_summary_task, translate_text_sync
from .tts_utils import text_to_speech, get_speech_url
from celery.result import AsyncResult
import requests
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

@login_required
@require_POST
def regenerate_summary(request, pk):
    try:
        pdf = PDFDocument.objects.get(pk=pk, user=request.user)
        text = extract_text_from_pdf(pdf.file)
        
        # Get summary type from request or use current type
        summary_type = request.POST.get('summary_type', pdf.summary_type)
        
        try:
            if summary_type == 'bert_gpt2':
                summaries = get_bert_gpt2_summary(text)
                pdf.bert_summary = summaries['summary']
                success_msg = 'BERT/GPT-2 summary regenerated successfully!'
            else:  # gemini
                summaries = get_gemini_summary(text)
                pdf.gemini_summary = summaries['gemini_summary']
                success_msg = 'Gemini summary regenerated successfully!'
            
            pdf.summary_type = summary_type
            pdf.save()
            messages.success(request, success_msg)
            
            return JsonResponse({
                'status': 'success',
                'message': success_msg
            })
        except Exception as e:
            return JsonResponse({'error': f'Failed to regenerate {summary_type} summary'}, status=500)
            
    except PDFDocument.DoesNotExist:
        return JsonResponse({'error': 'PDF not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def ask_question(request, pk):
    try:
        pdf = PDFDocument.objects.get(pk=pk, user=request.user)
        question = request.POST.get('question')
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
            
        # Get the appropriate summary text based on current language
        summary_text = None
        if pdf.current_language == 'en':
            summary_text = pdf.gemini_summary if pdf.gemini_summary else pdf.bert_summary
        else:
            # Use translated summary if available
            if pdf.translated_summary and pdf.current_language != 'en':
                summary_text = pdf.translated_summary
            else:
                summary_text = pdf.gemini_summary if pdf.gemini_summary else pdf.bert_summary
        
        if summary_text:
            # Enhanced question answering with better context matching
            import re
            
            # Clean and prepare the summary text
            summary_text = re.sub(r'\s+', ' ', summary_text).strip()
            sentences = re.split(r'(?<=[.!?])\s+', summary_text)
            
            # Convert question to lowercase for case-insensitive matching
            question_lower = question.lower().strip()
            
            # Enhanced keyword extraction with better Unicode support
            try:
                # Use a more robust regex pattern for word extraction
                question_words = set(re.findall(r'[\w\u0900-\u097F\u0A80-\u0AFF\u0B80-\u0BFF\u0C80-\u0CFF\u0D80-\u0DFF\u0E80-\u0EFF\u0F00-\u0FFF\u1000-\u109F\u1100-\u11FF\u1200-\u137F\u1380-\u139F\u13A0-\u13FF\u1400-\u167F\u1680-\u169F\u16A0-\u16FF\u1700-\u171F\u1720-\u173F\u1740-\u175F\u1760-\u177F\u1780-\u17FF\u1800-\u18AF\u1900-\u194F\u1950-\u197F\u1980-\u19DF\u19E0-\u19FF\u1A00-\u1A1F\u1A20-\u1AAF\u1AB0-\u1AFF\u1B00-\u1B7F\u1B80-\u1BBF\u1BC0-\u1BFF\u1C00-\u1C4F\u1C50-\u1C7F\u1C80-\u1C8F\u1C90-\u1CBF\u1CD0-\u1CFF\u1D00-\u1D7F\u1D80-\u1DBF\u1DC0-\u1DFF\u1E00-\u1EFF\u1F00-\u1FFF\u2000-\u206F\u2070-\u209F\u20A0-\u20CF\u20D0-\u20FF\u2100-\u214F\u2150-\u218F\u2190-\u21FF\u2200-\u22FF\u2300-\u23FF\u2400-\u243F\u2440-\u245F\u2460-\u24FF\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u27C0-\u27EF\u27F0-\u27FF\u2800-\u28FF\u2900-\u297F\u2980-\u29FF\u2A00-\u2AFF\u2B00-\u2BFF\u2C00-\u2C5F\u2C60-\u2C7F\u2C80-\u2CFF\u2D00-\u2D2F\u2D30-\u2D7F\u2D80-\u2DDF\u2DE0-\u2DFF\u2E00-\u2E7F\u2E80-\u2EFF\u2F00-\u2FDF\u2FF0-\u2FFF\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u3100-\u312F\u3130-\u318F\u3190-\u319F\u31A0-\u31BF\u31C0-\u31EF\u31F0-\u31FF\u3200-\u32FF\u3300-\u33FF\u3400-\u4DBF\u4DC0-\u4DFF\u4E00-\u9FFF\uA000-\uA48F\uA490-\uA4CF\uA4D0-\uA4FF\uA500-\uA63F\uA640-\uA69F\uA6A0-\uA6FF\uA700-\uA71F\uA720-\uA7FF\uA800-\uA82F\uA830-\uA83F\uA840-\uA87F\uA880-\uA8DF\uA8E0-\uA8FF\uA900-\uA92F\uA930-\uA95F\uA960-\uA97F\uA980-\uA9DF\uA9E0-\uA9FF\uAA00-\uAA5F\uAA60-\uAA7F\uAA80-\uAADF\uAAE0-\uAAFF\uAB00-\uAB2F\uAB30-\uAB6F\uAB70-\uABBF\uABC0-\uABFF\uAC00-\uD7AF\uD7B0-\uD7FF\uD800-\uDB7F\uDB80-\uDBFF\uDC00-\uDFFF\uE000-\uF8FF\uF900-\uFAFF\uFB00-\uFB4F\uFB50-\uFDFF\uFE00-\uFE0F\uFE10-\uFE1F\uFE20-\uFE2F\uFE30-\uFE4F\uFE50-\uFE6F\uFE70-\uFEFF\uFF00-\uFFEF\uFFF0-\uFFFF]+', question_lower))
            except:
                # Fallback to basic word extraction
                question_words = set(re.findall(r'\b\w+\b', question_lower))
             
            # Extended stop words for better filtering (including some common words in other languages)
            stop_words = {
                # English stop words
                'what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into',
                'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'within', 'without',
                'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'his', 'hers',
                'ours', 'theirs', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'while', 'where', 'as', 'so',
                'than', 'too', 'very', 'just', 'now', 'then', 'here', 'there', 'all', 'any', 'both', 'each', 'few',
                'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'such', 'can',
                'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn',
                'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn',
                'wasn', 'weren', 'won', 'wouldn',
                
                # Common Hindi words (basic)
                'क्या', 'कब', 'कहाँ', 'कौन', 'क्यों', 'कैसे', 'है', 'हैं', 'था', 'थे', 'था', 'हो', 'होता', 'होती',
                'यह', 'वह', 'ये', 'वे', 'मैं', 'तुम', 'आप', 'हम', 'मेरा', 'तेरा', 'आपका', 'हमारा', 'और', 'या', 'लेकिन',
                'अगर', 'तो', 'तब', 'जब', 'जहाँ', 'जैसे', 'इसलिए', 'क्योंकि', 'सभी', 'कोई', 'दोनों', 'हर', 'कुछ',
                'अधिक', 'सबसे', 'दूसरा', 'कुछ', 'ऐसा', 'नहीं', 'न', 'केवल', 'अपना', 'वही', 'ऐसा', 'सकता', 'सकती',
                'चाहिए', 'अब', 'डी', 'एल', 'एम', 'ओ', 'रे', 'वी', 'वाई'
            }
            
            # Filter out stop words and short words
            keywords = [word for word in question_words if word not in stop_words and len(word) > 2]
            keywords_set = set(keywords)  # Convert to set for intersection operation
            
            # Enhanced sentence matching with scoring
            relevant_sentences = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                try:
                    # Use the same robust regex pattern for sentence words
                    sentence_words = set(re.findall(r'[\w\u0900-\u097F\u0A80-\u0AFF\u0B80-\u0BFF\u0C80-\u0CFF\u0D80-\u0DFF\u0E80-\u0EFF\u0F00-\u0FFF\u1000-\u109F\u1100-\u11FF\u1200-\u137F\u1380-\u139F\u13A0-\u13FF\u1400-\u167F\u1680-\u169F\u16A0-\u16FF\u1700-\u171F\u1720-\u173F\u1740-\u175F\u1760-\u177F\u1780-\u17FF\u1800-\u18AF\u1900-\u194F\u1950-\u197F\u1980-\u19DF\u19E0-\u19FF\u1A00-\u1A1F\u1A20-\u1AAF\u1AB0-\u1AFF\u1B00-\u1B7F\u1B80-\u1BBF\u1BC0-\u1BFF\u1C00-\u1C4F\u1C50-\u1C7F\u1C80-\u1C8F\u1C90-\u1CBF\u1CD0-\u1CFF\u1D00-\u1D7F\u1D80-\u1DBF\u1DC0-\u1DFF\u1E00-\u1EFF\u1F00-\u1FFF\u2000-\u206F\u2070-\u209F\u20A0-\u20CF\u20D0-\u20FF\u2100-\u214F\u2150-\u218F\u2190-\u21FF\u2200-\u22FF\u2300-\u23FF\u2400-\u243F\u2440-\u245F\u2460-\u24FF\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u27C0-\u27EF\u27F0-\u27FF\u2800-\u28FF\u2900-\u297F\u2980-\u29FF\u2A00-\u2AFF\u2B00-\u2BFF\u2C00-\u2C5F\u2C60-\u2C7F\u2C80-\u2CFF\u2D00-\u2D2F\u2D30-\u2D7F\u2D80-\u2DDF\u2DE0-\u2DFF\u2E00-\u2E7F\u2E80-\u2EFF\u2F00-\u2FDF\u2FF0-\u2FFF\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u3100-\u312F\u3130-\u318F\u3190-\u319F\u31A0-\u31BF\u31C0-\u31EF\u31F0-\u31FF\u3200-\u32FF\u3300-\u33FF\u3400-\u4DBF\u4DC0-\u4DFF\u4E00-\u9FFF\uA000-\uA48F\uA490-\uA4CF\uA4D0-\uA4FF\uA500-\uA63F\uA640-\uA69F\uA6A0-\uA6FF\uA700-\uA71F\uA720-\uA7FF\uA800-\uA82F\uA830-\uA83F\uA840-\uA87F\uA880-\uA8DF\uA8E0-\uA8FF\uA900-\uA92F\uA930-\uA95F\uA960-\uA97F\uA980-\uA9DF\uA9E0-\uA9FF\uAA00-\uAA5F\uAA60-\uAA7F\uAA80-\uAADF\uAAE0-\uAAFF\uAB00-\uAB2F\uAB30-\uAB6F\uAB70-\uABBF\uABC0-\uABFF\uAC00-\uD7AF\uD7B0-\uD7FF\uD800-\uDB7F\uDB80-\uDBFF\uDC00-\uDFFF\uE000-\uF8FF\uF900-\uFAFF\uFB00-\uFB4F\uFB50-\uFDFF\uFE00-\uFE0F\uFE10-\uFE1F\uFE20-\uFE2F\uFE30-\uFE4F\uFE50-\uFE6F\uFE70-\uFEFF\uFF00-\uFFEF\uFFF0-\uFFFF]+', sentence_lower))
                except:
                    # Fallback to basic word extraction
                    sentence_words = set(re.findall(r'\b\w+\b', sentence_lower))
                
                # Calculate relevance score
                exact_matches = len(keywords_set.intersection(sentence_words))
                partial_matches = sum(1 for keyword in keywords if any(keyword in word for word in sentence_words))
                total_score = exact_matches * 2 + partial_matches
                
                if total_score > 0:
                    relevant_sentences.append((sentence, total_score))
            
            # Sort by relevance score
            relevant_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # Generate answer based on relevance
            if relevant_sentences:
                # Take top 2-3 most relevant sentences
                top_sentences = relevant_sentences[:min(3, len(relevant_sentences))]
                answer_text = ' '.join([s[0] for s in top_sentences])
                
                # Format the answer nicely
                if len(answer_text) > 500:
                    answer_text = answer_text[:500] + "..."
                
                answer = f"Based on the document: {answer_text}"
            else:
                # Fallback: provide a general summary excerpt
                summary_excerpt = summary_text[:300] + "..." if len(summary_text) > 300 else summary_text
                answer = f"I couldn't find specific information about that in the document. Here's a relevant excerpt from the summary: {summary_excerpt}"
            
            # Get additional information from web search (optional)
            try:
                web_answer = perform_web_search(question)
                final_answer = f"📄 Document Answer:\n{answer}\n\n🌐 Additional Information:\n{web_answer}"
            except:
                final_answer = f"📄 Document Answer:\n{answer}"
            
            # Store question and answer with timestamp
            from django.utils import timezone
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if pdf.questions:
                pdf.questions += f"\n---\n[{timestamp}] {question}"
                pdf.answers += f"\n---\n[{timestamp}] {final_answer}"
            else:
                pdf.questions = f"[{timestamp}] {question}"
                pdf.answers = f"[{timestamp}] {final_answer}"
            
            pdf.save()
            
            return JsonResponse({
                'status': 'success',
                'answer': final_answer,
                'timestamp': timestamp
            })
        else:
            return JsonResponse({'error': 'No summary available for this document'}, status=400)
            
    except PDFDocument.DoesNotExist:
        return JsonResponse({'error': 'PDF not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def perform_web_search(query):
    """Placeholder for web search functionality."""
    # In a real application, you would integrate with a web search API here (e.g., Google Search API, Bing Search API)
    # For now, we'll return a dummy result.
    print(f"Performing web search for: {query}")
    # Simulate a delay or API call
    import time
    time.sleep(1)
    return f"Web search results for '{query}': Information from the internet suggests that... (This is a placeholder answer)"

@login_required
def delete_image(request, pk):
    try:
        image = ImageDocument.objects.get(pk=pk, user=request.user)
        image.delete()
        messages.success(request, 'Image deleted successfully!')
        return redirect('pdf_list')
    except ImageDocument.DoesNotExist:
        messages.error(request, 'Image not found.')
        return redirect('pdf_list')

@login_required
def download_image(request, pk):
    try:
        image = ImageDocument.objects.get(pk=pk, user=request.user)
        file_path = image.file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as image_file:
                response = FileResponse(image_file)
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
        else:
            messages.error(request, 'Image file not found.')
            return redirect('pdf_list')
    except ImageDocument.DoesNotExist:
        messages.error(request, 'Image not found.')
        return redirect('pdf_list')

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    summaries_count = PDFDocument.objects.filter(user=request.user).count()
    images_count = ImageDocument.objects.filter(user=request.user).count()
    
    context = {
        'user': request.user,
        'profile': user_profile,
        'summaries_count': summaries_count,
        'images_count': images_count
    }
    return render(request, 'summarizer/profile.html', context)

@login_required
def profile_settings(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'summarizer/profile_settings.html', {'form': form})

@login_required
def upload_pdf(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create PDFDocument instance but don't save yet
                pdf_doc = form.save(commit=False)
                pdf_doc.user = request.user
                pdf_doc.title = os.path.splitext(request.FILES['file'].name)[0]
                
                # Extract text and generate summaries
                text = extract_text_from_pdf(request.FILES['file'])
                
                if pdf_doc.summary_type == 'bert_gpt2':
                    try:
                        summaries = get_bert_gpt2_summary(text)
                        pdf_doc.bert_summary = summaries['summary']
                        # Note: gpt2_summary field doesn't exist in the model, using bert_summary for both
                    except Exception as e:
                        messages.warning(request, f'BERT/GPT-2 summarization failed: {str(e)}')
                        pdf_doc.bert_summary = "Summarization failed. Please try again."
                else:  # gemini
                    try:
                        summaries = get_gemini_summary(text)
                        pdf_doc.gemini_summary = summaries['gemini_summary']
                    except Exception as e:
                        messages.warning(request, f'Gemini summarization failed: {str(e)}')
                        pdf_doc.gemini_summary = "Summarization failed. Please try again."
                
                # Save the document with summaries
                pdf_doc.save()
                messages.success(request, 'PDF uploaded and summarized successfully!')
                return redirect('pdf_detail', pk=pdf_doc.pk)
                
            except Exception as e:
                messages.error(request, f'Error processing PDF: {str(e)}')
    else:
        form = PDFUploadForm()
    
    return render(request, 'summarizer/upload.html', {'form': form})

class PDFListView(LoginRequiredMixin, ListView):
    model = PDFDocument
    template_name = 'summarizer/pdf_list.html'
    context_object_name = 'pdfs'
    ordering = ['-uploaded_at']
    paginate_by = 10

    def get_queryset(self):
        return PDFDocument.objects.filter(user=self.request.user).order_by('-uploaded_at')

class ImageListView(LoginRequiredMixin, ListView):
    model = ImageDocument
    template_name = 'summarizer/image_list.html'
    context_object_name = 'images'
    ordering = ['-uploaded_at']
    paginate_by = 10

    def get_queryset(self):
        return ImageDocument.objects.filter(user=self.request.user).order_by('-uploaded_at')

@login_required
def pdf_detail(request, pk):
    try:
        pdf = PDFDocument.objects.get(pk=pk)
        
        # Handle question submission
        if request.method == 'POST':
            question = request.POST.get('question')
            if question:
                # If there are existing questions, append the new one
                if pdf.questions:
                    pdf.questions += f"\n---\n{question}"
                else:
                    pdf.questions = question
                
                # Get the appropriate summary text
                summary_text = pdf.gemini_summary if pdf.gemini_summary else pdf.bert_summary
                if summary_text:
                    # Enhanced answer generation based on the summary
                    # Split the summary into sentences for better context matching
                    import re
                    sentences = re.split(r'(?<=[.!?])\s+', summary_text)
                    
                    # Convert question to lowercase for case-insensitive matching
                    question_lower = question.lower()
                    
                    # Look for sentences that might contain relevant information to the question
                    relevant_sentences = []
                    
                    # Keywords from the question (simple approach)
                    question_words = set(question_lower.split())
                    # Remove common words that don't add much meaning
                    stop_words = {'what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
                    keywords = [word for word in question_words if word not in stop_words]
                    
                    # Find sentences with the most keyword matches
                    for sentence in sentences:
                        sentence_lower = sentence.lower()
                        matches = sum(1 for keyword in keywords if keyword in sentence_lower)
                        if matches > 0:
                            relevant_sentences.append((sentence, matches))
                    
                    # Sort by number of matches (descending)
                    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
                    
                    if relevant_sentences:
                        # Take the top 3 most relevant sentences
                        answer_text = ' '.join([s[0] for s in relevant_sentences[:3]])
                        answer = f"Based on the document: {answer_text}"
                    else:
                        # Fallback if no relevant sentences found
                        answer = f"I couldn't find specific information about that in the document. Here's a part of the summary that might help: {summary_text[:200]}..."
                    
                    # Perform web search for additional information
                    web_answer = perform_web_search(question)
                    
                    # Combine answers from PDF and web search
                    final_answer = f"Document-based answer: {answer}\n\nInternet-based answer: {web_answer}"
                    
                    # Store the final combined answer
                    if pdf.answers:
                        pdf.answers += f"\n---\n{final_answer}"
                    else:
                        pdf.answers = final_answer
                    
                    pdf.save()
                    messages.success(request, 'Your question has been saved and answered.')
        
        # Prepare questions and answers for template
        questions = []
        answers = []
        if pdf.questions:
            questions = pdf.questions.split('\n---\n')
        if pdf.answers:
            answers = pdf.answers.split('\n---\n')
        
        # Combine questions and answers into pairs
        qa_pairs = []
        for i in range(len(questions)):
            if i < len(answers):
                qa_pairs.append({'question': questions[i], 'answer': answers[i]})
            else:
                qa_pairs.append({'question': questions[i], 'answer': 'Answer pending...'})
                
        return render(request, 'summarizer/pdf_detail.html', {
            'pdf': pdf, 
            'questions': questions,
            'qa_pairs': qa_pairs
        })
    except PDFDocument.DoesNotExist:
        messages.error(request, 'PDF not found.')
        return redirect('pdf_list')

@login_required
@require_POST
def update_language(request, pk):
    try:
        pdf = PDFDocument.objects.get(pk=pk, user=request.user)
        language = request.POST.get('language')

        if language and language in dict(PDFDocument.LANGUAGE_CHOICES):
            if language == 'en':
                pdf.current_language = 'en'
                pdf.translated_summary = None
                pdf.save()
                return JsonResponse({'status': 'success', 'language': 'en'})

            # Get the appropriate summary to translate
            summary_to_translate = None
            if pdf.gemini_summary:
                summary_to_translate = pdf.gemini_summary
            elif pdf.bert_summary:
                summary_to_translate = pdf.bert_summary
            else:
                return JsonResponse({'status': 'error', 'message': 'No summary available to translate'}, status=400)

            # Use synchronous translation instead of Celery
            translation_result = translate_text_sync(summary_to_translate, language)
            
            if translation_result['status'] == 'success':
                pdf.translated_summary = translation_result['translated_text']
                pdf.current_language = language
                pdf.save()
                return JsonResponse({'status': 'success', 'language': language})
            else:
                return JsonResponse({'status': 'error', 'message': translation_result['message']}, status=500)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid language'}, status=400)

    except PDFDocument.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'PDF not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in update_language: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def check_translation_status(request, task_id):
    task_result = AsyncResult(task_id)
    if task_result.ready():
        result = task_result.get()
        if result['status'] == 'success':
            return JsonResponse({'status': 'success', 'language': result['language']})
        else:
            return JsonResponse({'status': 'error', 'message': result.get('message', 'Translation failed')}, status=500)
    return JsonResponse({'status': 'processing'})

@login_required
def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create ImageDocument instance but don't save yet
                image_doc = form.save(commit=False)
                image_doc.user = request.user
                uploaded_file = request.FILES['image']
                image_doc.title = os.path.splitext(uploaded_file.name)[0]

                # Extract information from image using enhanced OCR
                result = extract_text_from_image(uploaded_file)

                # Safer error display and consistent redirects
                if not result['success']:
                    error_message = result.get('error', 'Unknown error')
                    logger.error(f"OCR failed: {error_message}")
                    if 'Tesseract is not installed' in error_message:
                        messages.warning(request, 'Tesseract OCR is not installed.')
                        return redirect('tesseract_installation')
                    elif 'pytesseract' in error_message:
                        messages.error(request, 'Python Tesseract module is missing.')
                    else:
                        messages.error(request, f'Error processing image: {error_message}')
                    return redirect('upload_image')
                
                # Store comprehensive analysis results
                image_doc.summary = result.get('summary', '')
                image_doc.extracted_text = result.get('text', '')
                image_doc.labels = ', '.join(result.get('labels', [])) if result.get('labels') else ''
                image_doc.detected_objects = ', '.join(result.get('objects', [])) if result.get('objects') else ''
                image_doc.faces_detected = result.get('faces_detected', 0)
                image_doc.analysis_source = result.get('source', 'tesseract_ocr')
                image_doc.analysis_confidence = result.get('confidence', 0.0)
                
                # Store classification data
                if result.get('classification'):
                    classification = result['classification']
                    image_doc.image_type = classification.get('image_type', 'unknown')
                    image_doc.edge_density = classification.get('edge_density', 0.0)
                    image_doc.text_density = classification.get('text_density', 0.0)
                    image_doc.color_type = classification.get('color_info', {}).get('color_description', '')
                    image_doc.classification_data = classification
                
                # Store analysis data
                if result.get('analysis'):
                    analysis = result['analysis']
                    image_doc.word_count = analysis.get('text_analysis', {}).get('word_count', 0)
                    image_doc.character_count = analysis.get('text_analysis', {}).get('character_count', 0)
                    image_doc.text_quality = analysis.get('text_analysis', {}).get('text_quality', 'unknown')
                    image_doc.analysis_data = analysis
                
                # Store image properties
                if result.get('analysis', {}).get('image_properties'):
                    props = result['analysis']['image_properties']
                    image_doc.image_width = props.get('dimensions', {}).get('width', 0)
                    image_doc.image_height = props.get('dimensions', {}).get('height', 0)
                
                # Store processing details
                image_doc.processing_variant = result.get('processing_variant', '')
                if result.get('ocr_config'):
                    import json
                    image_doc.ocr_config = json.dumps(result['ocr_config'])
                
                # Optionally refine the summary using Gemini if API key is configured
                try:
                    context_text = (result.get('summary', '') or '') + "\n\nOCR Text (if any):\n" + (result.get('text', '') or '')
                    # Avoid overly long payloads
                    context_text = context_text[:6000]
                    # Build a compact, structured evidence block to reduce hallucinations
                    classification = result.get('classification') or {}
                    analysis_json = result.get('analysis') or {}
                    evidence_lines = [
                        f"image_type: {classification.get('image_type','unknown')}",
                        f"edge_density: {classification.get('edge_density',0)}",
                        f"text_density: {classification.get('text_density',0)}",
                        f"color_type: {analysis_json.get('image_properties',{}).get('color_type','unknown')}",
                        f"dimensions: {analysis_json.get('image_properties',{}).get('dimensions',{})}",
                        f"word_count: {analysis_json.get('text_analysis',{}).get('word_count',0)}",
                        f"text_quality: {analysis_json.get('text_analysis',{}).get('text_quality','unknown')}"
                    ]
                    evidence_block = "\n".join(evidence_lines) if evidence_lines else "Unknown"
                    ocr_snippet = (result.get('text','')[:600] or "Unknown")

                    custom = (
                        "You are an expert visual analyst. Write a concise, factual SHORT NOTE.\n\n"
                        "EVIDENCE (authoritative; do not contradict):\n" + evidence_block + "\n\n"
                        "OCR_SNIPPET (quote only if present):\n" + ocr_snippet + "\n\n"
                        "Output format:\n"
                        "- 5–8 bullet points\n"
                        "- Each bullet ≤ 15 words\n"
                        "- Cover: composition (layout, orientation, focus)\n"
                        "- Cover: colors/lighting (hues, brightness, contrast)\n"
                        "- Cover: notable elements (objects, structures, shapes, densities)\n"
                        "- Cover: any readable text (quote briefly if present)\n"
                        "- Cover: conservative context (scene type, setting)\n"
                        "- Final line: Takeaway: <most important single insight>\n"
                        "- Final line after that: Explanation: <2–3 short sentences citing the EVIDENCE fields you used>\n\n"
                        "Rules:\n"
                        "- Use ONLY EVIDENCE and OCR_SNIPPET; if missing, write 'Unknown'\n"
                        "- Be precise, concrete, and objective (e.g., 'Greenish cast', not 'Looks natural')\n"
                        "- Always mention dimensions if provided\n"
                        "- No extra sections, no speculation, no headings"
                    )
                    gemini = get_gemini_summary(context_text, custom_prompt=custom)
                    refined = gemini.get('gemini_summary')
                    if refined and 'Error' not in refined:
                        image_doc.summary = refined
                except Exception as e:
                    logger.debug(f"Gemini refinement skipped: {str(e)}")

                # Save the document
                image_doc.save()
                
                # Show appropriate success message
                if result['source'] == 'google_vision':
                    messages.success(request, 'Image analyzed successfully using Google Cloud Vision!')
                elif result['source'] == 'tesseract_ocr':
                    messages.success(request, 'Image processed successfully using enhanced OCR!')
                elif result['source'] == 'ocr_description':
                    messages.info(request, 'Image uploaded. Limited text detected, generated description instead.')
                
                return redirect('image_detail', pk=image_doc.pk)
                
            except Exception as e:
                logger.exception(f"Error in upload_image view: {str(e)}")
                messages.error(request, f'Error processing image: {str(e)}')
    else:
        form = ImageUploadForm()
    
    return render(request, 'summarizer/upload_image.html', {'form': form})

@login_required
def image_detail(request, pk):
    try:
        image = ImageDocument.objects.get(pk=pk)
        return render(request, 'summarizer/image_detail.html', {'image': image})
    except ImageDocument.DoesNotExist:
        messages.error(request, 'Image not found.')
        return redirect('pdf_list')

@login_required
@require_POST
def ask_image_question(request, pk):
    try:
        image = ImageDocument.objects.get(pk=pk, user=request.user)
        question = request.POST.get('question', '').strip()
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)

        # Choose context: translated or original summary; fallback to extracted text
        context_text = None
        if image.current_language != 'en' and image.translated_summary:
            context_text = image.translated_summary
        else:
            context_text = image.summary if image.summary else image.extracted_text

        if not context_text:
            return JsonResponse({'error': 'No content available to answer from'}, status=400)

        # Use Gemini for answer if available
        prompt = f"""
You are a helpful assistant. Given the following image analysis content, answer the user's question precisely and concisely.

Image content:
{context_text}

Question: {question}

Answer:
"""
        try:
            gemini = get_gemini_summary(prompt, custom_prompt="")
            answer = gemini.get('gemini_summary') or ""
        except Exception as e:
            answer = ""

        if not answer:
            # Simple heuristic fallback: return the most relevant sentences
            import re
            sentences = re.split(r'(?<=[.!?])\s+', context_text)
            q = question.lower()
            scored = []
            for s in sentences:
                score = sum(1 for w in q.split() if w in s.lower())
                if score:
                    scored.append((score, s))
            scored.sort(reverse=True)
            answer = ' '.join(s for _, s in scored[:3]) or context_text[:300]

        # Augment with quick web snippets for credibility
        try:
            snippets = _web_search_snippets(question)
            if snippets:
                answer = f"{answer}\n\nSources:\n" + "\n".join([f"- {s}" for s in snippets[:3]])
        except Exception as e:
            logger.debug(f"Web search enrichment failed: {str(e)}")

        # Store Q&A in analysis_data JSON
        from django.utils import timezone
        qa_entry = {
            'ts': timezone.now().isoformat(),
            'q': question,
            'a': answer
        }
        data = image.analysis_data or {}
        qa_list = data.get('qa', [])
        qa_list.append(qa_entry)
        data['qa'] = qa_list
        image.analysis_data = data
        image.save(update_fields=['analysis_data'])

        return JsonResponse({'status': 'success', 'answer': answer})
    except ImageDocument.DoesNotExist:
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        logger.exception(f"Error in ask_image_question: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def _web_search_snippets(query: str):
    """Fetch a few web snippets for the query using DuckDuckGo HTML results (no API key)."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36'
    }
    url = 'https://html.duckduckgo.com/html/'
    resp = requests.post(url, data={'q': query}, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = []
    for r in soup.select('div.result'):  # parse titles/snippets
        title = r.select_one('a.result__a')
        snippet = r.select_one('a.result__snippet')
        if title:
            text = title.get_text(strip=True)
            if snippet:
                text += f" — {snippet.get_text(strip=True)}"
            results.append(text)
        if len(results) >= 5:
            break
    return results

@login_required
@require_POST
def update_image_language(request, pk):
    """Update image summary language"""
    try:
        image = ImageDocument.objects.get(pk=pk, user=request.user)
        language = request.POST.get('language')

        if language and language in dict(PDFDocument.LANGUAGE_CHOICES):
            if language == 'en':
                image.current_language = 'en'
                image.translated_summary = None
                image.save()
                return JsonResponse({'status': 'success', 'language': 'en'})

            # Get the appropriate text to translate
            text_to_translate = None
            if image.summary:
                text_to_translate = image.summary
            elif image.extracted_text:
                text_to_translate = image.extracted_text
            else:
                return JsonResponse({'status': 'error', 'message': 'No text available to translate'}, status=400)

            # Use synchronous translation
            translation_result = translate_text_sync(text_to_translate, language)
            
            if translation_result['status'] == 'success':
                image.translated_summary = translation_result['translated_text']
                image.current_language = language
                image.save()
                return JsonResponse({'status': 'success', 'language': language})
            else:
                return JsonResponse({'status': 'error', 'message': translation_result['message']}, status=500)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid language'}, status=400)

    except ImageDocument.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Image not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in update_image_language: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def image_text_to_speech(request, pk):
    """Convert image summary to speech"""
    try:
        image = ImageDocument.objects.get(pk=pk, user=request.user)
        
        # Get the text to convert to speech
        text_to_speak = None
        language_code = request.POST.get('language', 'en')
        
        # Determine which text to speak based on language
        if language_code == 'en':
            text_to_speak = image.summary if image.summary else image.extracted_text
        else:
            # Use translated summary if available
            if image.translated_summary and image.current_language == language_code:
                text_to_speak = image.translated_summary
            else:
                # Fall back to original summary
                text_to_speak = image.summary if image.summary else image.extracted_text
        
        if not text_to_speak:
            return JsonResponse({
                'status': 'error',
                'message': 'No text available to convert to speech'
            }, status=400)
        
        # Convert text to speech
        result = text_to_speech(text_to_speak, language_code)
        
        if result['status'] == 'success':
            # Generate URL for the audio file
            audio_url = get_speech_url(result['file_path'])
            
            return JsonResponse({
                'status': 'success',
                'audio_url': audio_url,
                'message': 'Text converted to speech successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result['message']
            }, status=500)
            
    except ImageDocument.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Image not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in image_text_to_speech: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def tesseract_installation(request):
    """View for displaying Tesseract OCR installation instructions"""
    return render(request, 'summarizer/tesseract_installation.html')


@login_required
def update_language_preference(request):
    """Update the user's language preference"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            language = data.get('language')
            
            if language and language in dict(PDFDocument.LANGUAGE_CHOICES):
                # Store the language preference in the user's session
                request.session['preferred_language'] = language
                
                # If you have a user profile model, you could also store it there
                if hasattr(request.user, 'profile'):
                    request.user.profile.preferred_language = language
                    request.user.profile.save()
                
                return JsonResponse({'status': 'success', 'language': language})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid language'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@login_required
def delete_pdf(request, pk):
    try:
        pdf = PDFDocument.objects.get(pk=pk, user=request.user)
        pdf.delete()
        messages.success(request, 'PDF deleted successfully.')
        return redirect('pdf_list')
    except PDFDocument.DoesNotExist:
        messages.error(request, 'PDF not found.')
        return redirect('pdf_list')


def download_pdf(request, pk):
    try:
        pdf = PDFDocument.objects.get(pk=pk)
        if pdf.user != request.user:
            raise Http404("You do not have permission to access this file.")
        file_path = pdf.file.path
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=pdf.title + ".pdf")
    except PDFDocument.DoesNotExist:
        raise Http404("PDF not found.")
    except Exception as e:
        raise Http404(f"Error downloading PDF: {str(e)}")

@login_required
@require_POST
def text_to_speech_view(request, pk):
    """
    Convert PDF summary to speech
    """
    try:
        pdf = PDFDocument.objects.get(pk=pk, user=request.user)
        
        # Get the text to convert to speech
        text_to_speak = None
        language_code = request.POST.get('language', 'en')
        summary_type = request.POST.get('summary_type', 'gemini')
        
        # Determine which text to speak based on summary type and language
        if summary_type == 'bert':
            # Use BERT summary
            text_to_speak = pdf.bert_summary
        else:
            # Use Gemini summary or translated version
            if language_code == 'en':
                text_to_speak = pdf.gemini_summary
            else:
                # Use translated summary if available
                if pdf.translated_summary and pdf.current_language == language_code:
                    text_to_speak = pdf.translated_summary
                else:
                    # Fall back to original Gemini summary
                    text_to_speak = pdf.gemini_summary
        
        if not text_to_speak:
            return JsonResponse({
                'status': 'error',
                'message': 'No text available to convert to speech'
            }, status=400)
        
        # Convert text to speech
        result = text_to_speech(text_to_speak, language_code)
        
        if result['status'] == 'success':
            # Generate URL for the audio file
            audio_url = get_speech_url(result['file_path'])
            
            return JsonResponse({
                'status': 'success',
                'audio_url': audio_url,
                'message': 'Text converted to speech successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result['message']
            }, status=500)
            
    except PDFDocument.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'PDF not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in text_to_speech_view: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)