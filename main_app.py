# main_app.py (Corrected and Updated)

import streamlit as st
import os
import urllib.parse

# Import all modularized functions
from app.config import load_api_keys
from app.document_processor import load_and_split_document
from app.langchain_logic import get_retriever, get_llm, get_learning_module_chain # CORRECTED IMPORT
# We will create a new function in output_generator to handle the new model
# from app.output_generator import render_module_to_markdown 

# --- Load API keys at the very beginning ---
load_api_keys()

# --- Page Configuration ---
st.set_page_config(page_title="Pimp My Textbook", layout="wide", initial_sidebar_state="expanded")

# --- UI Title ---
st.title("📚 Pimp My Textbook: Learning Module Generator")
st.markdown("Laden Sie ein Lehrbuchkapitel oder ein Transkript hoch und generieren Sie ein komplettes, interaktives Lernmodul im Markdown-Format.")

# --- Session State Initialization ---
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'retriever' not in st.session_state:
    st.session_state.retriever = None

# --- A new helper function to render the markdown ---
# You can move this to output_generator.py for even cleaner code
def render_module_to_markdown(module):
    """Takes a LearningModule object and converts it to a markdown string."""
    md_string = f"# {module.main_title}\n"
    
    for block in module.blocks:
        md_string += f"\n>[!{block.block_type}] {block.title}\n"
        if block.content_html:
            md_string += f"> {block.content_html}\n"
        
        if block.is_interactive and block.interactive_questions:
            base_url = "https://allgemeinbildung.github.io/textbox/answers.html?"
            params = {
                'assignmentId': block.assignment_id,
                'subIds': block.sub_id
            }
            for i, q in enumerate(block.interactive_questions, 1):
                params[f'question{i}'] = q.question_text
            
            iframe_url = base_url + urllib.parse.urlencode(params)
            md_string += f'><iframe src="{iframe_url}" style="border:0px #ffffff none;" name="myiFrame" scrolling="yes" frameborder="1" marginheight="0px" marginwidth="0px" height="450px" width="100%" allowfullscreen></iframe>\n'

        if block.audio_url:
            md_string += f'>[!hint] **Radiobeitrag** ><audio controls><source src="{block.audio_url}"></audio>\n'
            if block.audio_source_url:
                md_string += f'> Quelle: [{block.audio_source_url}]({block.audio_source_url})\n'

    return md_string

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("1. File Upload")
    uploaded_file = st.file_uploader("Select textbook chapter", type=['pdf', 'txt', 'docx'], label_visibility="collapsed")
    
    if uploaded_file:
        docs = load_and_split_document(uploaded_file)
        if docs:
            st.session_state.retriever = get_retriever(docs)
            st.success(f"Indexed {len(docs)} document chunks.")
        else:
            st.session_state.retriever = None
    
    st.header("2. Model Selection")
    provider = st.selectbox("Provider", ["OpenAI", "Google"])
    
    model_name = ""
    if provider == "OpenAI":
        model_name = st.selectbox("Model", ["gpt-4o", "gpt-4.1"])
    elif provider == "Google":
        model_name = st.selectbox("Model", ["gemini-2.5-pro", "gemini-2.5-flash"])

# --- Main Interaction Area ---
st.header("3. Define Task")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    topic = st.text_area(
        "Describe the learning module you want to create",
        height=100,
        help="e.g., 'A module about the recent changes in youth crime in Zurich, including learning objectives, reflection questions, and comprehension questions based on the text.'"
    )
    
    generate_button = st.button("✨ Generate Learning Module", type="primary", use_container_width=True)

# --- Generation Logic ---
if generate_button:
    if st.session_state.retriever is None:
        st.warning("Please upload and process a document first (check sidebar).")
    elif not all([topic, model_name]):
        st.warning("Please ensure a model is selected and a topic is entered.")
    else:
        with st.spinner(f"Running module generation with '{model_name}'. The LLM is thinking..."):
            try:
                llm = get_llm(provider, model_name)
                # CORRECTED FUNCTION CALL: Use the new function and unpack the two return values
                rag_chain, parser = get_learning_module_chain(llm, st.session_state.retriever)
                
                result = rag_chain.invoke({"input": topic})
                
                # Use the returned parser to convert the raw string into our Pydantic object
                st.session_state.generated_content = parser.parse(result['answer'])
                st.success("Learning Module generated successfully!")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.exception(e) # This will print the full traceback for debugging
                st.session_state.generated_content = None

# --- Results Display ---
if st.session_state.generated_content:
    st.divider()
    st.header("Generated Learning Module")
    
    module_object = st.session_state.generated_content
    
    # Use our new render function to display the markdown
    markdown_output = render_module_to_markdown(module_object)
    
    st.markdown(markdown_output)
    
    st.divider()

    # --- Download and Raw Data Section ---
    st.header("Download & Data")

    st.download_button(
        label="Download as .md file",
        data=markdown_output,
        file_name=f"{module_object.main_title.replace(' ', '_')}.md",
        mime="text/markdown"
    )

    with st.expander("Show Generated JSON Data"):
        # The .json() method is deprecated, use .model_dump_json() instead
        st.json(module_object.model_dump_json(indent=2))