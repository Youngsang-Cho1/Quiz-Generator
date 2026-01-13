from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# pydantic schemas
SourceType = Literal['text_layer', 'ocr']

class PageText(BaseModel):
    page: int
    text: str
    source: SourceType
    confidence: Optional[float] = None

class ExtractResult(BaseModel):
    pages: List[PageText]
    total_chars: int
    used_ocr: bool

class QuizRequest(BaseModel):
    text: str
    max_items: int = 12

class QuizItem(BaseModel):
    type: Literal["tf", "mcq", "short"]
    question: str
    choices: Optional[List[str]] = None
    answer: str
    explanation: str
    evidence: List[str] = Field(default_factory=list)

class QuizResult(BaseModel):
    items: List[QuizItem]
