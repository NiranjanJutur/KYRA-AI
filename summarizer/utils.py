import pdfplumber
from transformers import pipeline

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def get_bert_summary(text, max_length=150, min_length=50):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    # Split text into chunks if it's too long
    max_chunk_length = 1024
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    
    summaries = []
    for chunk in chunks:
        if len(chunk.strip()) > 100:  # Only summarize chunks with substantial content
            summary = summarizer(chunk, max_length=max_length, min_length=min_length,
                               do_sample=False)[0]['summary_text']
            summaries.append(summary)
    
    return ' '.join(summaries)

def get_gpt2_summary(text, max_length=150):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    # Use different parameters for GPT-2 style summary
    max_chunk_length = 1024
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    
    summaries = []
    for chunk in chunks:
        if len(chunk.strip()) > 100:
            summary = summarizer(chunk, max_length=max_length, min_length=30,
                               do_sample=True, top_k=50, top_p=0.95)[0]['summary_text']
            summaries.append(summary)
    
    return ' '.join(summaries)