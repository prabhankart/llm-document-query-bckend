import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import services.document_processor as doc_processor
import services.vector_store as vector_store
import services.llm_service as llm_service

# --- Configuration ---
# Using a class for configuration makes it cleaner and easier to manage.
class Config:
    # Define a temporary folder for uploads.
    # WARNING: On hosting platforms like Render or Heroku, this filesystem is "ephemeral".
    # This means any files you save here will be DELETED when the server restarts or sleeps.
    # This approach is okay for processing a file immediately, but not for long-term storage.
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    
    # --- IMPORTANT FOR DEPLOYMENT ---
    # Get the frontend URL from an environment variable for CORS.
    # This is much more secure than allowing all origins ('*').
    # For local development, you can set this to 'http://localhost:3000'.
    # In production (on Netlify/Vercel), you'll set this to your live frontend URL.
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

app = Flask(__name__)
app.config.from_object(Config)

# --- CORS (Cross-Origin Resource Sharing) Setup ---
# This is a critical security step. We are telling the backend to only accept
# API requests from our specific frontend application.
CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_URL"]}})

# --- Helper Function ---
def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- API Routes ---
# It's good practice to prefix all API routes with '/api/'.
@app.route('/api/upload', methods=['POST'])
def upload_file_route():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400
    
    file = request.files['file']
    generate_summary = request.form.get('generateSummary') == 'true'

    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
        
    if not file or not allowed_file(file.filename):
        return jsonify({"success": False, "error": "File type not allowed"}), 400

    filepath = None  # Initialize filepath to None
    try:
        filename = secure_filename(file.filename)
        # Ensure the temporary upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # --- NOTE ON STATE ---
        # Your vector_store seems to be in-memory. This means every time the server
        # restarts or you redeploy, the entire index of the document will be LOST.
        # For a production app, you should use a persistent vector database like
        # Pinecone, Weaviate, or a cloud database with vector capabilities.
        
        print("Processing document...")
        text_chunks = doc_processor.process_document(filepath)
        if not text_chunks:
            return jsonify({"success": False, "error": "Could not extract text from document."}), 500

        vector_store.add_chunks_to_store(text_chunks)
        print("Document processed and stored in memory.")

        summary = None
        if generate_summary:
            print("Generating initial summary...")
            summary = llm_service.generate_summary(text_chunks)
        
        print("Generating sample questions...")
        sample_questions = llm_service.generate_sample_questions(text_chunks)

        return jsonify({
            "success": True, 
            "message": "File processed successfully",
            "summary": summary,
            "sampleQuestions": sample_questions 
        }), 200
    
    except Exception as e:
        # Log the full error for debugging
        print(f"An error occurred: {e}")
        return jsonify({"success": False, "error": "An internal server error occurred."}), 500

    finally:
        # --- CRITICAL CLEANUP STEP ---
        # Always remove the uploaded file from the temporary directory
        # after you are done with it.
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up temporary file: {filepath}")


@app.route('/api/query', methods=['POST'])
def handle_query_route():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"success": False, "error": "Query not provided"}), 400
    
    query = data['query']
    try:
        context_chunks = vector_store.find_relevant_chunks(query)
        if not context_chunks:
            # Return a structured response even if no context is found
            return jsonify({
                "success": True,
                "decision": "Cannot Determine",
                "amount": "N/A",
                "justification": ["Could not find relevant information in the uploaded document."]
            })
            
        response_data = llm_service.generate_structured_response(query, context_chunks)
        return jsonify(response_data)
        
    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- Main Entry Point for Running the App ---
if __name__ == '__main__':
    # Get port from environment variable for deployment platforms like Render.
    # Default to 8000 for local development.
    port = int(os.environ.get("PORT", 8000))
    
    # Debug mode should be OFF in a production environment.
    # You can set an environment variable like FLASK_DEBUG=1 to enable it.
    is_debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ['true', '1']
    
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)