import os
from dotenv import load_dotenv
from src.rag.indexer import index_code_files

load_dotenv()

vectordb = index_code_files("./sample_code")

results = vectordb.similarity_search("security issues with password", k=2)

for doc in results:
    print("---")
    print(doc.page_content)