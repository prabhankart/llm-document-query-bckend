import os
import json
import google.generativeai as genai

# --- Configuration ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# --- IMPROVED FUNCTION TO GENERATE SAMPLE QUESTIONS ---
def generate_sample_questions(text_chunks):
    """
    Generates three relevant sample questions based on the document content.
    """
    context = "\n---\n".join(text_chunks[:4]) # Use a bit more context for questions

    # This new prompt is more explicit and gives the AI a clear example.
    prompt = f"""
    Based on the document context below, generate exactly three relevant and insightful questions a user might ask.

    **Instructions:**
    1.  Read the context carefully to understand the main topics.
    2.  Create three distinct questions that probe key information within the text.
    3.  Your response **MUST** be a valid JSON array containing three strings. Do not include any other text or formatting.

    **Example Format:**
    ["What is the policy's effective date?", "Are cosmetic treatments covered?", "What is the waiting period for a hernia?"]

    ---
    **Document Context:**
    "{context}"
    ---
    **Your JSON Response (a single JSON array of 3 strings):**
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        # Clean the response to ensure it's valid JSON
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        questions = json.loads(clean_response)
        
        # Final check to ensure it's a list of 3 strings
        if isinstance(questions, list) and len(questions) == 3 and all(isinstance(q, str) for q in questions):
            return questions
        else:
            raise ValueError("LLM did not return a valid list of 3 strings.")

    except Exception as e:
        print(f"Error generating dynamic sample questions: {e}. Using fallback.")
        # Return static questions only as a last resort
        return [
            "What is the main purpose of this document?",
            "Are there any specific deadlines mentioned?",
            "Who are the key parties involved?"
        ]


def generate_summary(text_chunks):
    """
    Generates a brief summary from the first few chunks of a document.
    """
    summary_context = "\n---\n".join(text_chunks[:3])
    prompt = f"""
    You are a helpful assistant. Provide a brief, neutral summary of the following document excerpt in one or two sentences.
    ---
    **Document Excerpt:**
    "{summary_context}"
    ---
    **Your Summary:**
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Could not generate a summary for this document."


def generate_structured_response(query, context_chunks):
    """
    Generates a structured JSON response from the LLM based on a query and context.
    """
    context = "\n---\n".join(context_chunks)
    prompt = f"""
    You are an expert analysis agent. Your task is to answer a user's query based *only* on the provided document excerpts.
    Your response **MUST** be a valid JSON object with the exact structure:
    {{
      "decision": "Approved" | "Rejected" | "Cannot Determine",
      "amount": "N/A" | "The calculated amount",
      "justification": ["A list of strings, where each string is a direct quote or a summary of the clause(s) from the context that justifies your decision."]
    }}
    If the context does not contain enough information, set "decision" to "Cannot Determine".
    ---
    **User Query:** "{query}"
    ---
    **Document Excerpts (Context):** "{context}"
    ---
    **Your JSON Response:**
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    try:
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_response)
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return {
            "decision": "Error",
            "amount": "N/A",
            "justification": ["The AI model returned an invalid response."]
        }