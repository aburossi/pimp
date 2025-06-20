# app/models.py

from pydantic import BaseModel, Field
from typing import List, Optional

class Frontmatter(BaseModel):
    """Defines the metadata frontmatter for the markdown file."""
    topic: List[str] = Field(description='A list of 3-4 relevant keywords and 3 themes, formatted as "keyword1", "keyword2".')
    chapter: List[str] = Field(description='The chapter, and if applicable, a relevant chapter title, formatted as "chapter number title".')
    type: str = Field(default="news", description="The type of content, e.g., 'news', 'article'.")
    source: str = Field(default="ABUnews", description="The source of the content, which is always 'ABUnews'.")
    summary: str = Field(description="A one-sentence summary of the core message, with 2-3 key terms in **bold**.")

class LearningObjectives(BaseModel):
    """A block for the learning objectives."""
    introduction: str = Field(description="Two engaging introduction sentences for 15-20-year-old students, with 1-2 **bold** key terms per sentence.")
    objectives: List[str] = Field(description="Two bullet points stating clear learning goals based on the content.")
    keywords: List[str] = Field(description="A list of 3 relevant keywords from the provided list, formatted as '[[Keyword1]]'.")
    aspects: List[str] = Field(description="A list of all related 'Aspekte der Allgemeinbildung' from the provided list, formatted as '[[Aspekt1]]'.")

class InteractiveQuestionsBlock(BaseModel):
    """A block containing an iframe with questions."""
    title: str = Field(description="The title for this question block, e.g., 'Wählen Sie eine Frage und begründen Sie Ihre Antwort'.")
    assignment_id: str = Field(description="The unique identifier for the assignment, to be used in the iframe URL.")
    sub_id: str = Field(description="The sub-identifier for this question set, to be used in the iframe URL.")
    questions: List[str] = Field(description="A list of questions. Each item should contain the question text and the italicized follow-up question.")

class ImportanceBlock(BaseModel):
    """A block explaining the relevance of the topic."""
    points: List[str] = Field(description="A list of 3 bullet points explaining the topic's significance, with **bold keywords**.")

class MediaBlock(BaseModel):
    """A block for the media content and its comprehension questions."""
    audio_url: Optional[str] = Field(default=None, description="The URL for the MP3 file, if applicable.")
    source_url: str = Field(description="The original source URL of the content.")
    comprehension_questions: InteractiveQuestionsBlock = Field(description="An interactive block with 6-7 comprehension questions (Remembering, Understanding, Applying).")

class AnswersBlock(BaseModel):
    """A block containing the answers to the comprehension questions."""
    iframe_url: str = Field(description="The URL for the iframe that displays the answers.")

class SolutionSuggestions(BaseModel):
    """A block containing the suggested solutions for the teacher."""
    answer_key_name: str = Field(description="The identifier for the answer key.")
    solutions: List[str] = Field(description="A list of concise, correct answers for each of the comprehension questions.")

class WritingAssignment(BaseModel):
    """Defines a single writing assignment block."""
    text_type: str = Field(description="The type of text to be written, e.g., 'Stellungnahme'.")
    objective: str = Field(description="Two sentences explaining the goal of this writing assignment.")
    guidance_questions: InteractiveQuestionsBlock = Field(description="An interactive block with 5 step-by-step guiding questions.")

class DeepDiveLanguage(BaseModel):
    """The section for language practice with multiple writing assignments."""
    title: str = Field(default="Vertiefung Sprache")
    instruction: str = Field(description="The main instruction for the language deep dive section.")
    writing_assignments: List[WritingAssignment] = Field(description="A list of 3 different writing assignments.")

class FullLearningUnit(BaseModel):
    """The root model for the entire generated educational content."""
    frontmatter: Frontmatter
    title: str = Field(description="The main H1 title of the document, e.g., 'ABUnews - Zürcher Jugendkriminalität'.")
    objectives_block: LearningObjectives
    activation_questions: InteractiveQuestionsBlock
    importance_block: ImportanceBlock
    media_block: MediaBlock
    answers_block: AnswersBlock
    solution_suggestions: SolutionSuggestions
    language_deep_dive: DeepDiveLanguage