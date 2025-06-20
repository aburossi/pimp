# app/models.py (New Version)

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# A type for the markdown callout styles
BlockType = Literal["info", "success", "question", "abstract", "hint", "quote"]

class InteractiveQuestion(BaseModel):
    """Defines a single question for an interactive iframe."""
    question_text: str = Field(description="The full, formatted text of the question, including markdown like **bold** or *italics*.")

class ContentBlock(BaseModel):
    """Represents a single block of content in the educational markdown file."""
    block_type: BlockType = Field(description="The type of the block, which determines the markdown callout (e.g., 'info', 'question').")
    title: str = Field(description="The title displayed in the callout header (e.g., 'Worum geht es?').")
    content_html: Optional[str] = Field(default=None, description="The main text content for the block, formatted as an HTML string to allow for spans and other styles.")
    audio_url: Optional[str] = Field(default=None, description="A URL to an audio file, if the block is a media block.")
    audio_source_url: Optional[str] = Field(default=None, description="The source URL for the audio credit.")
    # For the interactive iframes
    is_interactive: bool = Field(default=False, description="Set to true if this block should contain an interactive iframe.")
    assignment_id: Optional[str] = Field(default=None, description="The unique ID for the assignment, used in the iframe URL.")
    sub_id: Optional[str] = Field(default=None, description="The unique sub-id for the question set, used in the iframe URL.")
    interactive_questions: Optional[List[InteractiveQuestion]] = Field(default=None, description="A list of questions to be encoded into the iframe URL.")

class LearningModule(BaseModel):
    """The root model for a complete, structured educational module."""
    main_title: str = Field(description="The main H1 title of the entire learning module (e.g., 'ABUnews - Zürcher Jugendkriminalität').")
    blocks: List[ContentBlock] = Field(description="A list of content blocks that make up the body of the module.")