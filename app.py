import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import services.document_processor as doc_processor
import services.vector_store as vector_store
import services.llm_service as llm_service

# --- Configuration ---
class Config:
    # IMPORTANT: Use the /tmp directory for Vercel's temporary filesystem
    UPLOAD_FOLDER = '/tmp/uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    # This variable will hold one or more frontend URLs, separated by commas
    FRONTEND_URLS = os.environ.get("FRONTEND_URLS", "http://localhost:3000")

app = Flask(__name__)
app.config.from_object(Config)

# --- CORS (Cross-Origin Resource Sharing) Setup ---
# This setup allows your backend to accept requests from the URLs you specify.
# It splits the comma-separated string from the environment variable into a list.
allowed_origins = [url.strip() for url in app.config["FRONTEND_URLS"].split(',')]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# --- Helper Function ---
def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- API Routes ---
# This is the entry point Vercel will use
@app.route('/')
def index():
    return "The Flask backend is running successfully!"

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

    filepath = None
    try:
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

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
        print(f"An error occurred: {e}")
        return jsonify({"success": False, "error": "An internal server error occurred."}), 500

    finally:
        # CRITICAL CLEANUP STEP
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

# This part is not needed for Vercel, but it's good to keep for local testing
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    is_debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ['true', '1']
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)