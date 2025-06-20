# app/document_processor.py

import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

@st.cache_data(show_spinner="Processing document...")
def load_and_split_document(uploaded_file):
    """
    Loads an uploaded document, saves it temporarily, selects the appropriate loader,
    loads the content, and splits it into chunks for processing.
    
    Args:
        uploaded_file: The file uploaded via Streamlit's file_uploader.

    Returns:
        A list of Document objects (chunks) or None if an error occurs.
    """
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    temp_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    _, file_extension = os.path.splitext(temp_path)
    file_extension = file_extension.lower()

    if file_extension == '.pdf':
        loader = PyPDFLoader(temp_path)
    elif file_extension == '.txt':
        loader = TextLoader(temp_path, encoding='utf-8')
    elif file_extension == '.docx':
        loader = UnstructuredWordDocumentLoader(temp_path)
    else:
        st.error(f"Unsupported file type: '{file_extension}'")
        os.remove(temp_path)
        return None

    try:
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)
    finally:
        # Ensure the temporary file is deleted even if an error occurs
        try:
            os.remove(temp_path)
        except OSError as e:
            st.warning(f"Could not delete temporary file: {e}")

    return split_docs