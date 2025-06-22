import os
import re
import urllib.parse
import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import List, Literal, Optional

# --- Step 1: Load environment variables and initialize OpenAI client ---
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# Load API key from .env file
load_dotenv()

# Initialize the client
try:
    client = OpenAI()
except Exception as e:
    messagebox.showerror("Initialization Error", f"Failed to initialize OpenAI client.\nPlease check your .env file and OPENAI_API_KEY.\n\nDetails: {e}")
    exit()


# ==============================================================================
# PYDANTIC MODELS (Unified Section Model)
# ==============================================================================

class NestedBlock(BaseModel):
    type: str
    title: str
    content_list: List[str]

class IframeDetails(BaseModel):
    assignmentId: str
    subIds: str
    height: str
    questions: List[str]

class Section(BaseModel):
    """A single, unified model for all section types."""
    type: Literal["info", "keywords", "general_education", "iframe_question", "audio"]
    title: str
    content: Optional[str] = None
    nested_block: Optional[NestedBlock] = None
    items: Optional[List[str]] = None
    iframe_details: Optional[IframeDetails] = None
    block_type: Optional[str] = None
    audio_url: Optional[str] = None
    source_text: Optional[str] = None
    source_url: Optional[str] = None
    nested_quote_title: Optional[str] = None
    nested_quote_iframe_details: Optional[IframeDetails] = None

class WarningBlock(BaseModel):
    title: str
    content: str

class TeacherMaterial(BaseModel):
    title: str
    warning_block: Optional[WarningBlock] = None # Make this optional to prevent validation errors

class AbuNewsDocument(BaseModel):
    """The root model, now using a list of the single, unified Section model."""
    title: str
    sections: List[Section]
    teacher_material: Optional[TeacherMaterial] = None


# ==============================================================================
# MARKDOWN PARSER (v6 - Final Robustness Fix)
# ==============================================================================

def build_iframe_url(details: IframeDetails) -> str:
    base_url = "https://allgemeinbildung.github.io/textbox/answers.html?"
    params = {'assignmentId': details.assignmentId, 'subIds': details.subIds}
    for i, q in enumerate(details.questions):
        params[f'question{i+1}'] = q
    return base_url + urllib.parse.urlencode(params)

def generate_markdown(data: AbuNewsDocument) -> str:
    """Generates clean markdown with correct spacing and list formatting."""
    md_blocks = [f"# {data.title}"]

    for section in data.sections:
        block_parts = []
        if section.type == 'info':
            block_parts.append(f">[!{section.type}] {section.title}")
            if section.content:
                for line in section.content.strip().split('\n'):
                    block_parts.append(f"> {line.strip()}")
            if section.nested_block:
                block_parts.append(f">")
                block_parts.append(f">>[!{section.nested_block.type}] {section.nested_block.title}")
                for item in section.nested_block.content_list:
                    block_parts.append(f">> - {item.strip()}")
            md_blocks.append("\n".join(block_parts))

        elif section.type in ['keywords', 'general_education']:
            block_parts.append(f"#### {section.title}")
            if section.items:
                cleaned_items = [re.sub(r'[\[\]]', '', item).strip() for item in section.items]
                links = [f"[[{item}]]" for item in cleaned_items]
                block_parts.append(", ".join(links))
            md_blocks.append("\n".join(block_parts))

        elif section.type == 'iframe_question':
            block_parts.append(f">[!question] {section.title}")
            if section.iframe_details:
                iframe_url = build_iframe_url(section.iframe_details)
                iframe_tag = (f'<iframe src="{iframe_url}" style="border:0px #ffffff none;" '
                              f'name="myiFrame" scrolling="yes" frameborder="1" marginheight="0px" '
                              f'marginwidth="0px" height="{section.iframe_details.height}" '
                              'width="100%" allowfullscreen></iframe>')
                block_parts.append(iframe_tag)
            md_blocks.append("\n".join(block_parts))

        elif section.type == 'audio':
            block_type = section.block_type if section.block_type and section.block_type.lower() != 'none' else 'hint'
            source_text = section.source_text if section.source_text and section.source_text.lower() != 'none' else 'Quelle'
            source_url = section.source_url if section.source_url and section.source_url.lower() != 'none' else '#'
            
            block_parts.append(f">[!{block_type}] {section.title} ><audio controls><source src=\"{section.audio_url}\"></audio>")
            block_parts.append(f">Quelle: [{source_text}]({source_url})")

            if section.nested_quote_title and section.nested_quote_iframe_details:
                block_parts.append(f">")
                block_parts.append(f">>[!quote] {section.nested_quote_title}")
                nested_iframe_url = build_iframe_url(section.nested_quote_iframe_details)
                nested_iframe_tag = (f'>> <iframe src="{nested_iframe_url}" style="border:0px #ffffff none;" '
                                     f'name="myiFrame" scrolling="yes" frameborder="1" marginheight="0px" '
                                     f'marginwidth="0px" height="{section.nested_quote_iframe_details.height}" '
                                     'width="100%" allowfullscreen></iframe>')
                block_parts.append(nested_iframe_tag)
            md_blocks.append("\n".join(block_parts))

    # Handle Teacher Material section
    if data.teacher_material:
        md_blocks.append("%-%-%-")
        # Add the safety check for the warning_block itself
        if data.teacher_material.warning_block:
            tm = data.teacher_material
            tm_block_parts = [f"# {tm.title}"]
            tm_block_parts.append(f">[!warning] {tm.warning_block.title}")
            if tm.warning_block.content:
                for line in tm.warning_block.content.strip().split('\n'):
                    tm_block_parts.append(f"> {line.strip()}")
            md_blocks.append("\n".join(tm_block_parts))
        
    return "\n\n".join(md_blocks)


# ==============================================================================
# CORE LOGIC & UI (No changes needed here)
# ==============================================================================

def run_generation_process(system_prompt: str, user_prompt: str):
    """Handles the API call, parsing, and file saving."""
    try:
        response = client.responses.parse(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=AbuNewsDocument,
        )
        lesson_plan_data = response.output_parsed
        markdown_output = generate_markdown(lesson_plan_data)
        output_filename = "generated_lesson.md"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(markdown_output)
        messagebox.showinfo("Success", f"Markdown file '{output_filename}' was created successfully!")
    except Exception as e:
        messagebox.showerror("Generation Error", f"An error occurred:\n\n{e}")

def create_ui():
    """Sets up and runs the main Tkinter window."""
    def on_generate_click():
        system_prompt = system_prompt_text.get("1.0", tk.END).strip()
        user_prompt = user_prompt_text.get("1.0", tk.END).strip()
        if not system_prompt or not user_prompt:
            messagebox.showwarning("Input Missing", "Please provide both a system and a user prompt.")
            return
        status_label.config(text="Generating... Please wait.", fg="blue")
        generate_button.config(state=tk.DISABLED)
        window.update_idletasks()
        run_generation_process(system_prompt, user_prompt)
        status_label.config(text="Ready.", fg="green")
        generate_button.config(state=tk.NORMAL)

    window = tk.Tk()
    window.title("Markdown Lesson Generator (v6)")
    window.geometry("800x600")
    main_frame = tk.Frame(window, padx=10, pady=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    system_prompt_label = tk.Label(main_frame, text="System Prompt:", font=("Helvetica", 10, "bold"))
    system_prompt_label.pack(anchor="w")
    system_prompt_text = scrolledtext.ScrolledText(main_frame, height=10, wrap=tk.WORD)
    system_prompt_text.pack(fill=tk.X, expand=True, pady=(0, 10))
    system_prompt_text.insert(tk.END, "You are an expert curriculum developer for Swiss vocational education (Allgemeinbildung). Your task is to generate a complete, single-page lesson plan based on a news topic. You MUST structure your entire output strictly according to the provided JSON schema. Do not include markdown brackets like `[[` or `]]` in the string values for the 'items' field.")
    user_prompt_label = tk.Label(main_frame, text="User Prompt (Content):", font=("Helvetica", 10, "bold"))
    user_prompt_label.pack(anchor="w")
    user_prompt_text = scrolledtext.ScrolledText(main_frame, height=15, wrap=tk.WORD)
    user_prompt_text.pack(fill=tk.BOTH, expand=True)
    user_prompt_text.insert(tk.END, "Create a lesson plan about the topic: 'The political and social tensions in the USA stemming from conflicts between federal and state authorities, specifically regarding immigration policies and the use of the National Guard.'")
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.pack(fill=tk.X, pady=(10, 0))
    generate_button = tk.Button(bottom_frame, text="Generate Markdown", command=on_generate_click, font=("Helvetica", 12, "bold"))
    generate_button.pack(side=tk.RIGHT)
    status_label = tk.Label(bottom_frame, text="Ready.", fg="green", font=("Helvetica", 10))
    status_label.pack(side=tk.LEFT)
    window.mainloop()

if __name__ == "__main__":
    create_ui()