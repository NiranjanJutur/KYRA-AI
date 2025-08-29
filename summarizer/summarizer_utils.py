import os
import google.generativeai as genai
from transformers import pipeline
import pdfplumber
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# Initialize summarizer once as a global variable for reuse
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    print(f"Warning: Could not initialize summarizer: {e}")
    summarizer = None

def get_bert_gpt2_summary(text, max_length=150, min_length=50):
    if summarizer is None:
        return {'summary': 'Summarizer not available. Please check your installation.'}
    
    # Split text into chunks if it's too long
    max_chunk_length = 1024
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    
    summaries = []
    
    for chunk in chunks:
        if len(chunk.strip()) > 100:  # Only summarize chunks with substantial content
            try:
                # Get summary with different parameters for variety
                summary = summarizer(chunk, 
                                   max_length=max_length, 
                                   min_length=min_length,
                                   do_sample=True, 
                                   top_k=50, 
                                   top_p=0.95)[0]['summary_text']
                summaries.append(summary)
            except Exception as e:
                print(f"Error summarizing chunk: {e}")
                continue
    
    if not summaries:
        return {'summary': 'Could not generate summary. Please try again.'}
    
    return {
        'summary': ' '.join(summaries)
    }

def get_gemini_summary(text, custom_prompt=None, max_length=150):
    try:
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Use custom prompt if provided, otherwise use default prompt
        default_prompt = """Analyze the following text and provide a structured summary. Follow these exact formatting rules:

1. Start with a title line
2. Add two newlines after the title
3. Format each section like this:

📌 Key Points:

• [Main point 1]
    ◦ [Supporting detail]
    ◦ [Supporting detail]


• [Main point 2]
    ◦ [Supporting detail]
    ◦ [Supporting detail]


🔑 Core Concepts:

• [Important concept 1]


• [Important concept 2]


💡 Key Takeaways:

• [Major takeaway 1]


• [Major takeaway 2]

Important: 
- Add TWO newlines between each main point
- Add ONE newline between sub-points
- Keep consistent indentation
- Use proper spacing throughout

Please analyze and summarize the following text:"""
        
        # Prepare prompt for summarization
        prompt = f"""{custom_prompt if custom_prompt else default_prompt}

{text}
"""
        
        # Generate summary
        response = model.generate_content(prompt)
        
        # Extract and return the summary
        summary = response.text if response.text else "Gemini API could not generate a summary."
        
        return {'gemini_summary': summary}
        
    except Exception as e:
        return {'gemini_summary': f"Error generating Gemini summary: {str(e)}"}