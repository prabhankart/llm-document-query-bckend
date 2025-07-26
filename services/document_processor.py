# ==============================================================================
# File: services/document_processor.py
# Description: Functions for reading and chunking documents.
# ==============================================================================
import PyPDF2
from docx import Document

def _extract_text_from_pdf(filepath):
    """Extracts text from a PDF file."""
    text = ""
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def _extract_text_from_docx(filepath):
    """Extracts text from a DOCX file."""
    doc = Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def _split_text_into_chunks(text, chunk_size=1000, chunk_overlap=200):
    """Splits a long text into smaller, overlapping chunks."""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def process_document(filepath):
    """
    Main function to process an uploaded document.
    Detects file type, extracts text, and splits it into chunks.
    """
    if filepath.endswith(".pdf"):
        text = _extract_text_from_pdf(filepath)
    elif filepath.endswith(".docx"):
        text = _extract_text_from_docx(filepath)
    else:
        raise ValueError("Unsupported file type")
        
    chunks = _split_text_into_chunks(text)
    return chunks