from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import requests
from tqdm import tqdm
import chromadb
from transformers import AutoTokenizer
from typing import Any
from pydantic import BaseModel, Field

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    PromptTemplate,
    Settings
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

global_index = None
global_uploaded_filenames = []
query_engine = None

class LocalLLM(CustomLLM, BaseModel):
    api_url: str = Field(description="URL of the local LLM API")
    context_window: int = Field(default=4096, description="Context window size")
    num_output: int = Field(default=256, description="Number of output tokens")
    name: str = Field(default="local_llm", description="Name of the local LLM")

    class Config:
        arbitrary_types_allowed = True

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.name,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        payload = {"prompt": prompt}
        response = requests.post(f"{self.api_url}/generate", json=payload)
        if response.status_code == 200:
            return CompletionResponse(text=response.json()['generated_text'])
        else:
            raise Exception(f"API request failed: {response.text}")

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        response = self.complete(prompt, **kwargs)
        yield response

def initialize_index():
    global global_index
    global query_engine
    db = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db.get_or_create_collection("quickstart")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-mpnet-base-v2")
    Settings.embed_model = embed_model
    global_index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    #global_llm = LocalLLM(api_url="http://localhost:5000")
    Settings.llm = LocalLLM(api_url="http://localhost:5000")
    query_engine = global_index.as_query_engine()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_and_process_document(file_path):
    reader = SimpleDirectoryReader(input_files=[file_path])
    docs = reader.load_data()
    parser = SimpleNodeParser.from_defaults(chunk_size=1000, chunk_overlap=100)
    nodes = parser.get_nodes_from_documents(docs)
    return nodes

def add_documents_with_progress(index, nodes):
    total_nodes = len(nodes)
    for i, node in enumerate(tqdm(nodes, desc="Adding documents", unit="node")):
        index.insert_nodes([node])
        yield i + 1, total_nodes

@app.route('/api/upload', methods=['POST'])
def upload_file():
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
                    nodes = load_and_process_document(file_path)
                    for current, total in add_documents_with_progress(global_index, nodes):
                        progress = (current / total) * 100
                        yield json.dumps({"progress": progress, "status": "processing"}) + '\n'
                    os.remove(file_path)
                    global_uploaded_filenames.append(filename)
        yield json.dumps({"message": "All files processed and added to index successfully", "status": "complete"}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/json')

@app.route('/api/query', methods=['POST'])
def query_document():
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    data = request.json
    if not data or 'question' not in data:
        return jsonify({"error": "No question provided"}), 400
    question = data['question']
    if global_index is None:
        return jsonify({"error": "Index not initialized"}), 500
    retriever = VectorIndexRetriever(index=global_index, similarity_top_k=10)
    nodes = retriever.retrieve(question)
    formatted_contexts = [{"page": node.metadata.get('page', 'Unknown'), "content": node.text, "token_count": len(tokenizer.encode(node.text))} for node in nodes]
    return jsonify({"contexts": formatted_contexts}), 200

@app.route('/api/answer', methods=['POST'])
def answer_question():
    global query_engine

    data = request.json
    if not data or 'question' not in data or 'contexts' not in data:
        return jsonify({"error": "Missing question or contexts"}), 400
    question = data['question']
    contexts = data['contexts']
    
    template = (
        "<|system|>\n"
        "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, just say that you don't know. Keep the answer concise."
        "<|end|>\n"
        "<|user|>\n"
        "Question: {query_str}\n"
        "Context:\n"
        "{context_str}"
        "<|end|>\n"
        "<|assistant|>"
    )
    prompt = PromptTemplate(template)
    combined_context = "\n".join([ctx['content'] for ctx in contexts])
    formatted_prompt = prompt.format(query_str=question, context_str=combined_context)
    
    # Use Settings.llm instead of global_llm
    #response = Settings.llm.complete(formatted_prompt)
    response = query_engine.query(formatted_prompt)
    
    print(dir(response))
    #return jsonify({"answer": response.text}), 200
    return jsonify({"answer": response}), 200

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    initialize_index()
    app.run(debug=True, port=5001)