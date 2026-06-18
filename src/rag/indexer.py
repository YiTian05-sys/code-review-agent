import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def index_code_files(directory: str, db_path: str = "./chroma_db"):
    documents = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.ts')):
                filepath = os.path.join(root, file)
                loader = TextLoader(filepath, encoding='utf-8')
                documents.extend(loader.load())
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    splits = splitter.split_documents(documents)
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vectordb = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=db_path
    )
    
    print(f"索引完成，共处理 {len(splits)} 个代码块")
    return vectordb