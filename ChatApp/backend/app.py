from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from pydantic import Field
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variable to store the vectorstore
global_vectorstore = None

class LocalLLM(LLM):
    api_url: str = Field(..., description="URL of the local model API")

    def _call(self, prompt: str, **kwargs):
        response = requests.post(f"{self.api_url}/generate", json={"prompt": prompt})
        if response.status_code == 200:
            return response.json()['generated_text']
        else:
            raise Exception(f"API request failed: {response.text}")

    @property
    def _llm_type(self) -> str:
        return "local_llm"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_and_process_document(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_documents(docs)

def create_vectorstore(splits):
    embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    return Chroma.from_documents(splits, embedding=embeddings_model)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global global_vectorstore
    print("Uploading file")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        splits = load_and_process_document(file_path)
        global_vectorstore = create_vectorstore(splits)
        
        os.remove(file_path)  # Clean up the uploaded file
        print("File Uploaded!")
        print(f"Vectorstore: {global_vectorstore}")

        return jsonify({"message": "File processed successfully"}), 200
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/query', methods=['POST'])
def query_document():
    global global_vectorstore
    print("Querying")
    data = request.json
    print(data)

    if not data or 'question' not in data:
        return jsonify({"error": "No question provided"}), 400
    
    question = data['question']
    print(f"Vectorstore: {global_vectorstore}")

    if global_vectorstore is None:
        print("No vectorstore found")
        return jsonify({"error": "No document has been uploaded yet"}), 400
    
    retriever = global_vectorstore.as_retriever()
    
    # Retrieve relevant contexts
    contexts = retriever.get_relevant_documents(question)
    
    # Format contexts for response
    formatted_contexts = [{"page": ctx.metadata.get('page', 'Unknown'), "content": ctx.page_content} for ctx in contexts]
    
    print(formatted_contexts)
    return jsonify({"contexts": formatted_contexts}), 200

@app.route('/api/answer', methods=['POST'])
def answer_question():
    data = request.json
    if not data or 'question' not in data or 'contexts' not in data:
        return jsonify({"error": "Missing question or contexts"}), 400
    
    question = data['question']
    contexts = data['contexts']
    
    
    llm = LocalLLM(api_url="http://localhost:5000")
    
    template = """<|system|>
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.<|end|>
<|user|>
Question: {input}
Context:
{context}<|end|>
<|assistant|>"""
    prompt = PromptTemplate.from_template(template)
    
    # Combine contexts into a single string
    combined_context = "\n".join([ctx['content'] for ctx in contexts])
    
    formated_prompt = prompt.format(input=question, context=combined_context)
    print(formated_prompt)
    # Generate answer
    response = llm(formated_prompt)
    
    return jsonify({"answer": response}), 200

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=5001)