# app/langchain_logic.py (Corrected Version)

import os
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
# CORRECTED IMPORT: We need PromptTemplate now
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from .models import LearningModule

def load_prompt_from_file(file_path):
    """Reads and returns the content of a text/markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

@st.cache_resource(show_spinner="Indexing document...")
def get_retriever(_docs):
    """Creates a FAISS vector store and retriever from document chunks."""
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(_docs, embeddings)
    return vector_store.as_retriever(search_kwargs={"k": 10})

def get_llm(provider, model_name):
    """Initializes and returns the selected LLM object."""
    if provider == "OpenAI":
        return ChatOpenAI(model=model_name, temperature=0.1)
    elif provider == "Google":
        if not os.environ.get("GOOGLE_API_KEY"):
            st.error("Please add your GOOGLE_API_KEY to the .env file.")
            st.stop()
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.1)
    return None

def get_learning_module_chain(llm, retriever):
    """
    Creates the complete RAG chain for generating a LearningModule.
    This function now uses the more explicit PromptTemplate to avoid errors.
    """
    parser = PydanticOutputParser(pydantic_object=LearningModule)
    prompt_template_str = load_prompt_from_file('app/prompts/learning_module_prompt.md')

    # --- START OF THE FIX ---
    # Instead of ChatPromptTemplate.from_template, we use the more explicit
    # PromptTemplate class to ensure all variables are correctly registered.
    prompt = PromptTemplate(
        template=prompt_template_str,
        # Explicitly declare the variables the RAG chain will provide
        input_variables=["context", "input"],
        # Pre-fill the format instructions, so they don't need to be passed in later
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    # --- END OF THE FIX ---

    # For debugging, you can uncomment the line below to see the prompt's variables
    # print("DEBUG: Prompt Input Variables:", prompt.input_variables)

    document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)
    
    return rag_chain, parser