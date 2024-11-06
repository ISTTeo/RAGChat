import os
import torch
import argparse
from langchain_huggingface.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import bs4
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

def load_model(model_id, gpu_id):
    device = f'cuda:{gpu_id}' if torch.cuda.is_available() else 'cpu'
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    pipe = pipeline("text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=1024)
    return HuggingFacePipeline(pipeline=pipe)

def load_and_process_document(url):
    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        ),
    )
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_documents(docs)

def create_vectorstore(splits):
    embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    return Chroma.from_documents(splits, embedding=embeddings_model)

def create_rag_chain(llm, retriever):
    template = """<|system|>
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.<|end|>
<|user|>
Question: {input}
Context: {context}<|end|>
<|assistant|>"""
    prompt = PromptTemplate.from_template(template)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

def parse_assistant_phi_response(model_response: str):
    return model_response.split("<|assistant|>")[-1]

def main():
    parser = argparse.ArgumentParser(description="RAG Chain Script")
    parser.add_argument("--model", default="microsoft/Phi-3-mini-4k-instruct", help="Model ID")
    parser.add_argument("--question", required=True, help="Question to answer")
    parser.add_argument("--url", default="https://lilianweng.github.io/posts/2023-06-23-agent/", help="URL to process")
    parser.add_argument("--gpu", type=int, default=0, help="GPU ID to use")
    args = parser.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)

    llm = load_model(args.model, args.gpu)
    splits = load_and_process_document(args.url)
    vectorstore = create_vectorstore(splits)
    retriever = vectorstore.as_retriever()
    rag_chain = create_rag_chain(llm, retriever)

    response = rag_chain.invoke({"input": args.question})
    print(parse_assistant_phi_response(response['answer']))

if __name__ == "__main__":
    main()