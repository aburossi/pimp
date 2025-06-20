# main_app.py

import streamlit as st
import os
import urllib.parse

# Import all modularized functions
from app.config import load_api_keys
from app.document_processor import load_and_split_document
from app.langchain_logic import get_retriever, get_llm, get_learning_module_chain

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


# --- START: REWRITTEN MARKDOWN RENDERER ---
def render_interactive_block(block):
    """Helper function to render an interactive questions block to an iframe string."""
    base_url = "https://allgemeinbildung.github.io/textbox/answers.html?"
    params = {
        'assignmentId': block.assignment_id,
        'subIds': block.sub_id
    }
    for i, q_text in enumerate(block.questions, 1):
        params[f'question{i}'] = q_text
    
    iframe_url = base_url + urllib.parse.urlencode(params)
    return f'><iframe src="{iframe_url}" style="border:0px #ffffff none;" name="myiFrame" scrolling="yes" frameborder="1" marginheight="0px" marginwidth="0px" height="450px" width="100%" allowfullscreen></iframe>\n'

def render_module_to_markdown(module):
    """
    Takes a FullLearningUnit object and converts it to a markdown string.
    This function is now aligned with the complex Pydantic model.
    """
    # 1. Frontmatter
    md_string = "---\n"
    md_string += f"topic: {module.frontmatter.topic}\n"
    md_string += f"chapter: {module.frontmatter.chapter}\n"
    md_string += f"type: {module.frontmatter.type}\n"
    md_string += f"source: {module.frontmatter.source}\n"
    md_string += f'summary: "{module.frontmatter.summary}"\n'
    md_string += "---\n"
    
    # 2. Main Title - CORRECTED to use 'title'
    md_string += f"# {module.title}\n"
    
    # 3. Objectives Block
    obj_block = module.objectives_block
    md_string += f"\n>[!info] Worum geht es?\n> {obj_block.introduction}\n"
    md_string += ">>[!success] Lernziele\n"
    for obj in obj_block.objectives:
        md_string += f">> - {obj}\n"
    md_string += f"\n>#### Schlüsselbegriffe\n> {', '.join(obj_block.keywords)}\n"
    md_string += f"\n>#### Aspekte der Allgemeinbildung\n> {', '.join(obj_block.aspects)}\n"

    # 4. Activation Questions
    act_block = module.activation_questions
    md_string += f"\n>[!question] {act_block.title}\n"
    md_string += render_interactive_block(act_block)

    # 5. Importance Block
    imp_block = module.importance_block
    md_string += f"\n>[!info] Warum ist das wichtig?\n"
    for point in imp_block.points:
        md_string += f"> - {point}\n"

    # 6. Media Block
    media = module.media_block
    if media.audio_url:
        md_string += f"\n>[!hint] **Radiobeitrag** \n><audio controls><source src=\"{media.audio_url}\"></audio>\n"
    md_string += f"> Quelle: [Originalquelle]({media.source_url})\n"
    md_string += ">>[!quote] Beantworten Sie folgende Verständnisfragen:\n"
    md_string += render_interactive_block(media.comprehension_questions)
    
    # 7. Answers Iframe
    md_string += f"\n>[!success]- Antworten\n"
    md_string += f'><iframe src="{module.answers_block.iframe_url}" style="border:0px #ffffff none;" name="myiFrame" scrolling="yes" frameborder="1" marginheight="0px" marginwidth="0px" height="400px" width="100%" allowfullscreen></iframe>\n'

    # 8. Teacher Materials
    solutions = module.solution_suggestions
    md_string += "\n%-%-%-\n\n# LP-MATERIAL\n"
    md_string += f'>[!warning] {solutions.answer_key_name} - Lösungsvorschläge\n'
    for i, sol in enumerate(solutions.solutions, 1):
        md_string += f"> {i}. **Antwort zu Frage {i}:** {sol}\n"
        
    # 9. Language Deep Dive
    deep_dive = module.language_deep_dive
    md_string += f"\n# {deep_dive.title}\n"
    md_string += f"\n>[!abstract] Auftrag\n> {deep_dive.instruction}\n"
    if media.audio_url:
        md_string += f'>>[!hint] **Radiobeitrag** \n>><audio controls><source src="{media.audio_url}"></audio>\n'
    
    md_string += "\n## Textsorten\n"
    for assign in deep_dive.writing_assignments:
        md_string += f"\n### {assign.text_type}\n"
        md_string += f'>[!info] **[[{assign.text_type}]]**\n> Ziel: {assign.objective}\n'
        md_string += f'>>[!note]- {assign.text_type} erfassen \n>>#### Schritt-für-Schritt Anleitung\n'
        md_string += render_interactive_block(assign.guidance_questions)
        md_string += f'>>\n>>[[{assign.text_type}#✔ Bewertung]]\n'

    return md_string
# --- END: REWRITTEN MARKDOWN RENDERER ---


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
                rag_chain, parser = get_learning_module_chain(llm, st.session_state.retriever)
                
                result = rag_chain.invoke({"input": topic})
                
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
        # CORRECTED to use 'title'
        file_name=f"{module_object.title.replace(' ', '_')}.md",
        mime="text/markdown"
    )

    with st.expander("Show Generated JSON Data"):
        st.json(module_object.model_dump_json(indent=2))