# app.py
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
from flask_cors import CORS  # Add this import
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

def create_multi_context_rag_chain(llm, retriever, num_contexts):
    template = """<|system|>
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.<|end|>
<|user|>
Question: {input}
Contexts:
{context}<|end|>
<|assistant|>"""
    prompt = PromptTemplate.from_template(template)

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

@app.route('/api/process', methods=['POST'])
def process_document():
    print(request.values)
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        print(file)
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        splits = load_and_process_document(file_path)
        print(splits)
        vectorstore = create_vectorstore(splits)
        retriever = vectorstore.as_retriever()
        
        llm = LocalLLM(api_url="http://localhost:5000")
        rag_chain = create_multi_context_rag_chain(llm, retriever, num_contexts=4)
        
        question = request.form.get('question')
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        response = rag_chain.invoke({"input": question})
        
        os.remove(file_path)  # Clean up the uploaded file
        
        return jsonify({"answer": response['answer']})
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=5001)