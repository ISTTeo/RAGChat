from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import TokenTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from pydantic import Field
import requests
from tqdm import tqdm
from transformers import AutoTokenizer

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

global_vectorstore = None
global_uploaded_filenames = []

def initialize_vectorstore():
    global global_vectorstore
    print("Initializing VectorStore")
    embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    global_vectorstore = Chroma(embedding_function=embeddings_model, persist_directory="./chroma_db")
    print("VectorStore OK")

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
    text_splitter = TokenTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    for i, split in enumerate(splits):
        split.metadata['source'] = os.path.basename(file_path)
        
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    token_counts = [len(tokenizer.encode(split.page_content)) for split in splits]
    
    print(f"Total splits: {len(splits)}")
    print(f"Average split size: {sum(len(split.page_content) for split in splits) / len(splits):.2f} characters")
    print(f"Average token count: {sum(token_counts) / len(token_counts):.2f}")
    print(f"Token count range: {min(token_counts)} - {max(token_counts)}")
    
    return splits

def add_documents_with_progress(vectorstore, splits):
    total_splits = len(splits)
    for i, split in enumerate(tqdm(splits, desc="Adding documents", unit="split")):
        vectorstore.add_documents([split])
        yield i + 1, total_splits

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global global_vectorstore, global_uploaded_filenames

    if not request.files:
        return jsonify({"error": "No file part"}), 400

    def generate():
        for filename, file in request.files.items():
            if file.filename == '':
                yield json.dumps({"error": "No selected file"}) + '\n'
                return
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if filename not in global_uploaded_filenames:
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    splits = load_and_process_document(file_path)
                    
                    for current, total in add_documents_with_progress(global_vectorstore, splits):
                        progress = (current / total) * 100
                        yield json.dumps({"progress": progress, "status": "processing"}) + '\n'
                    
                    os.remove(file_path)
                    global_uploaded_filenames.append(filename)
                    print(f"File {filename} uploaded and added to vectorstore!")
                
        yield json.dumps({"message": "All files processed and added to vectorstore successfully", "status": "complete"}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/json')

@app.route('/api/query', methods=['POST'])
def query_document():
    global global_vectorstore
    data = request.json
    print("Querying:", data)

    if not data or 'question' not in data:
        return jsonify({"error": "No question provided"}), 400
    
    question = data['question']

    if global_vectorstore is None:
        print("No vectorstore found")
        return jsonify({"error": "Vectorstore not initialized"}), 500
    
    retriever = global_vectorstore.as_retriever()
    contexts = retriever.get_relevant_documents(question)
    
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    formatted_contexts = [
        {
            "page": ctx.metadata.get('page', 'Unknown'),
            "content": ctx.page_content,
            "token_count": len(tokenizer.encode(ctx.page_content))
        } for ctx in contexts
    ]
    
    return jsonify({"contexts": formatted_contexts}), 200

@app.route('/api/answer', methods=['POST'])
def answer_question():
    data = request.json
    if not data or 'question' not in data or 'contexts' not in data:
        return jsonify({"error": "Missing question or contexts"}), 400
    
    question = data['question']
    contexts = data['contexts']
    
    llm = LocalLLM(api_url="http://localhost:5000")
    
    template = """
        <|system|>
            You are an assistant for question-answering tasks. 
            Use the following pieces of retrieved context to answer the question. 
            If you don't know the answer, just say that you don't know. 
            Kkeep the answer concise.
        <|end|>
        <|user|>
            Question: {input}
            Context:
            {context}
        <|end|>
        <|assistant|>"""

    prompt = PromptTemplate.from_template(template)
    combined_context = "\n".join([ctx['content'] for ctx in contexts])
    formatted_prompt = prompt.format(input=question, context=combined_context)
    
    print("Formatted prompt:", formatted_prompt)
    response = llm(formatted_prompt)
    
    return jsonify({"answer": response}), 200

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    initialize_vectorstore()
    app.run(debug=True, port=5001)