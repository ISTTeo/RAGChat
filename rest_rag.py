import argparse
import requests
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from typing import List, Optional, Any
from langchain_core.callbacks import CallbackManagerForLLMRun
import bs4, os

from langchain_core.language_models.llms import LLM
from pydantic import Field

class LocalLLM(LLM):
    api_url: str = Field(..., description="URL of the local model API")

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        response = requests.post(f"{self.api_url}/generate", json={"prompt": prompt})
        if response.status_code == 200:
            return response.json()['generated_text']
        else:
            raise Exception(f"API request failed: {response.text}")

    @property
    def _llm_type(self) -> str:
        return "local_llm"

def load_url_content(url):
    return WebBaseLoader(
        web_paths=(url,),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        ),
    )

def load_pdf_file_content(file):
    _, file_extension = os.path.splitext(file)
    if file_extension.lower() in ['.pdf']:
        return PyPDFLoader(file)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

    
def load_and_process_document(loader):
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

    def format_docs(docs):
        return "\n\n".join(f"Context {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs))

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

def main():
    parser = argparse.ArgumentParser(description="RAG Chain Script")
    parser.add_argument("--model", default="microsoft/Phi-3-mini-4k-instruct", help="Model ID")
    parser.add_argument("--question", required=True, help="Question to answer")
    parser.add_argument("--url", default="https://lilianweng.github.io/posts/2023-06-23-agent/", help="URL to process")
    parser.add_argument("--file",  help="File to process")
    parser.add_argument("--gpu", type=int, default=0, help="GPU ID to use")
    parser.add_argument("--api_url", default="http://localhost:5000", help="URL of the local model API")
    parser.add_argument("--num_contexts", type=int, default=4, help="Number of contexts to retrieve")
    args = parser.parse_args()

    # Initialize the model
    llm = LocalLLM(api_url=args.api_url)  # Pass api_url as a named argument

    if(args.file):
        loader = load_pdf_file_content(args.file)
        splits = load_and_process_document(loader)
    else:
        loader = load_url_content(args.url)
        splits = load_and_process_document(loader)
    vectorstore = create_vectorstore(splits)
    retriever = vectorstore.as_retriever()
    rag_chain = create_multi_context_rag_chain(llm, retriever, args.num_contexts)
    print(f"Sending question: {args.question}")
    response = rag_chain.invoke({"input": args.question})
    print(response['answer'])

if __name__ == "__main__":
    main()