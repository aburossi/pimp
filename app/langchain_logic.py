# app/langchain_logic.py

import os
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Use our new, highly detailed Pydantic model
from .models import FullLearningUnit

def load_knowledge_file(file_path):
    """Reads a knowledge file and returns its content as a single string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Knowledge file not found at {file_path}")
        return ""

def get_learning_module_chain(llm, retriever):
    """
    Creates the complete RAG chain for generating a FullLearningUnit.
    This version loads multiple knowledge files into the prompt.
    """
    parser = PydanticOutputParser(pydantic_object=FullLearningUnit)
    
    # 1. Load the main prompt template
    main_prompt_template = load_knowledge_file('app/prompts/learning_module_prompt.md')
    
    # 2. Load the content from all knowledge files
    schluesselbegriffe_list = load_knowledge_file('app/prompts/schluesselbegriffe.txt')
    themen_list = load_knowledge_file('app/prompts/themen.txt')
    aspekte_list = load_knowledge_file('app/prompts/aspekte_der_allgemeinbildung.txt')
    chapters_list = load_knowledge_file('app/prompts/chapters.txt')
    
    # 3. Inject the knowledge lists into the main prompt template
    # This creates the final, complete "mega-prompt"
    final_prompt_str = main_prompt_template.format(
        schluesselbegriffe_list=schluesselbegriffe_list,
        themen_list=themen_list,
        aspekte_list=aspekte_list,
        chapters_list=chapters_list,
        # We still need to leave the other placeholders for the chain to fill
        context="{context}",
        input="{input}",
        format_instructions="{format_instructions}"
    )

    prompt = PromptTemplate(
        template=final_prompt_str,
        input_variables=["context", "input"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)
    
    return rag_chain, parser

# Keep the other functions (get_retriever, get_llm) as they are.
# ... (get_retriever and get_llm functions remain the same) ...
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