LLM Document Query System - Backend
This is the Python (Flask) backend for the document query system. It provides two main API endpoints: /upload for processing documents and /query for answering user questions based on the uploaded content.

Technology Stack
Python: Core programming language.

Flask: A lightweight web framework for the API server.

MongoDB Atlas: Used as the vector database to store document embeddings and perform semantic search.

Google Gemini API: Used for both generating embeddings and for the final question-answering generation.

LangChain: Used for utility functions like text splitting.

Setup Instructions
1. Prerequisites
Python 3.8+ installed.

A MongoDB Atlas account (the free tier is sufficient).

A Google AI API Key.

2. Set Up MongoDB Atlas
Create a new project and a new free M0 cluster in MongoDB Atlas.

In your new cluster, create a new database named llm_doc_retrieval and a new collection named document_chunks.

Crucially, you must create a Vector Search Index on the document_chunks collection.

Go to the "Vector Search" tab for your collection.

Click "Create Vector Index".

Choose the "JSON Editor" configuration method.

Give the index a name: vector_search_index.

Paste the following JSON configuration:

{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine"
    }
  ]
}


Get your database connection string.

Go to the "Database" section, click "Connect" on your cluster.

Choose "Drivers".

Select "Python" and the latest version.

Copy the connection string. It will look like mongodb+srv://<username>:<password>@.... Replace <password> with your actual database user password.

3. Project Installation
Create your project folder (llm-query-backend) and place all the provided files in the correct locations.

Create an uploads folder inside your main project directory. This is where files will be temporarily stored during processing.

Set Environment Variables:

You must set your MongoDB connection string and your Google API key as environment variables. How you do this depends on your operating system.

For Windows (Command Prompt):

setx MONGO_URI "your_mongodb_connection_string"
setx GOOGLE_API_KEY "your_google_api_key"


(You will need to close and reopen your terminal for this to take effect)

For macOS/Linux:

export MONGO_URI="your_mongodb_connection_string"
export GOOGLE_API_KEY="your_google_api_key"


(To make this permanent, add these lines to your ~/.bashrc, ~/.zshrc, or shell profile file)

Install Python Libraries:

Open a terminal in your project folder.

It's highly recommended to use a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`


Install all required packages from the requirements.txt file:

pip install -r requirements.txt


4. Running the Server
With your terminal still in the project folder (and the virtual environment activated), run the Flask application:

python app.py


The server will start, usually on http://localhost:8000. It is now ready to receive requests from your React frontend.