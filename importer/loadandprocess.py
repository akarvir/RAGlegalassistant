import os
from dotenv import load_dotenv
import tempfile
from langchain_community.document_loaders import (
    PyPDFLoader, 
    PyMuPDFLoader, 
    PDFMinerLoader,
    PyPDFium2Loader
)
from langchain_community.vectorstores.pgvector import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

load_dotenv()

docs_dir = os.path.abspath("./source_docs")
print(f"Loading documents from: {docs_dir}")

# Get list of PDF files
pdf_files = []
for root, _, files in os.walk(docs_dir):
    for file in files:
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(root, file))

print(f"Found {len(pdf_files)} PDF files")

# Try different loaders on each PDF
all_docs = []
for pdf_file in pdf_files:
    print(f"\nProcessing: {pdf_file}")
    best_content = ""
    best_loader_name = "None"
    
    # Try PyPDFLoader
    try:
        loader = PyPDFLoader(pdf_file)
        docs = loader.load()
        content = " ".join([doc.page_content for doc in docs])
        print(f"  PyPDFLoader extracted {len(content)} characters")
        if len(content) > len(best_content):
            best_content = content
            best_loader_name = "PyPDFLoader"
            best_docs = docs
    except Exception as e:
        print(f"  PyPDFLoader failed: {e}")
    
    # Try PyMuPDFLoader
    try:
        loader = PyMuPDFLoader(pdf_file)
        docs = loader.load()
        content = " ".join([doc.page_content for doc in docs])
        print(f"  PyMuPDFLoader extracted {len(content)} characters")
        if len(content) > len(best_content):
            best_content = content
            best_loader_name = "PyMuPDFLoader"
            best_docs = docs
    except Exception as e:
        print(f"  PyMuPDFLoader failed: {e}")
    
    # Try PDFMinerLoader
    try:
        loader = PDFMinerLoader(pdf_file)
        docs = loader.load()
        content = " ".join([doc.page_content for doc in docs])
        print(f"  PDFMinerLoader extracted {len(content)} characters")
        if len(content) > len(best_content):
            best_content = content
            best_loader_name = "PDFMinerLoader"
            best_docs = docs
    except Exception as e:
        print(f"  PDFMinerLoader failed: {e}")
    
    # Try PyPDFium2Loader
    try:
        loader = PyPDFium2Loader(pdf_file)
        docs = loader.load()
        content = " ".join([doc.page_content for doc in docs])
        print(f"  PyPDFium2Loader extracted {len(content)} characters")
        if len(content) > len(best_content):
            best_content = content
            best_loader_name = "PyPDFium2Loader"
            best_docs = docs
    except Exception as e:
        print(f"  PyPDFium2Loader failed: {e}")
    
    print(f"  Best loader: {best_loader_name} with {len(best_content)} characters")
    if len(best_content) > 100:  # Only add if meaningful content was found
        all_docs.extend(best_docs)
        print(f"  Content preview: {best_content[:200]}...")
    else:
        print("  CONTENT TOO SHORT - PDF MIGHT BE SCANNED OR EMPTY")

print(f"\nTotal documents extracted: {len(all_docs)}")

# Filter out documents with minimal content
min_content_length = 50
all_docs = [doc for doc in all_docs if len(doc.page_content.strip()) > min_content_length]
print(f"After filtering: {len(all_docs)} documents with substantial content")

if len(all_docs) == 0:
    print("No documents with extractable text found! Your PDFs might be scanned images.")
    print("Consider using an OCR tool to convert your PDFs to text first.")
    exit(1)

# Create embeddings and chunks
print("\nCreating embeddings...")
embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')

print("Splitting documents...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(all_docs)
print(f"Created {len(chunks)} chunks")

# Debug: Print some chunks
for i, chunk in enumerate(chunks[:2]):
    print(f"\nChunk {i+1} from {chunk.metadata.get('source', 'unknown')}:")
    print(f"Chunk length: {len(chunk.page_content)} characters")
    print(f"Chunk preview: {chunk.page_content[:200]}...")

# Store in vector database
print("\nStoring in vector database...")
PGVector.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="pdf_rag",
    connection_string=os.getenv("POSTGRES_URL"),
    pre_delete_collection=True,
)
print("Documents processed and stored successfully!")

