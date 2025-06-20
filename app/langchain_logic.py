# app/langchain_logic.py (New Version)

import os
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Import the new, more complex Pydantic model
from .models import LearningModule

# --- Helper function to load prompt from a file ---
def load_prompt_from_file(file_path):
    """Reads and returns the content of a text/markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

@st.cache_resource(show_spinner="Indexing document...")
def get_retriever(_docs):
    """Creates a FAISS vector store and retriever from document chunks."""
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(_docs, embeddings)
    return vector_store.as_retriever(search_kwargs={"k": 10}) # Increased k for more context

def get_llm(provider, model_name):
    """Initializes and returns the selected LLM object."""
    if provider == "OpenAI":
        # For complex JSON, a more capable model is recommended.
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
    This function now loads the prompt from an external file.
    """
    # 1. Define the parser for our target structure
    parser = PydanticOutputParser(pydantic_object=LearningModule)

    # 2. Load the prompt template from the .md file
    prompt_template_str = load_prompt_from_file('app/prompts/learning_module_prompt.md')
    
    # 3. Create the prompt object, injecting the format instructions
    prompt = ChatPromptTemplate.from_template(prompt_template_str).partial(
        format_instructions=parser.get_format_instructions()
    )
    
    # 4. Create the RAG chain
    document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)
    
    # Return both the chain and the parser, as the app will need the parser later
    return rag_chain, parser