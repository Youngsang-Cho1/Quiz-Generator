from typing import List, Optional, Literal
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import gradio as gr
import fitz

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

# logics (functions)

def extract_text_from_pdf_bytes(pdf_bytes : bytes, max_pages : int = 30):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf") # using pdf bytes within fitz
    page_number = min(len(doc), max_pages)

    pages = []
    total_chars = 0

    for i in range(page_number):
        page = doc.load_page(i)
        text = (page.get_text('text') or '').strip()
        total_chars += len(text)
        pages.append(PageText(page=i + 1, text=text, source="text_layer"))

    doc.close()
    return ExtractResult(pages=pages, total_chars=total_chars, used_ocr=False)


def generate_quiz(text: str, max_items: int = 12) -> QuizResult:
    # 아주 간단한 문장 분리 (MVP)
    candidates = []
    for block in text.splitlines():
        s = block.strip()
        if len(s) >= 30:
            candidates.append(s)

    items: List[QuizItem] = []
    for s in candidates[:max_items]:
        items.append(
            QuizItem(
                type="tf",
                question=f"참/거짓? {s}",
                answer="true",
                explanation="노트 원문을 그대로 사용한 문장이라 참(true)로 둔 MVP 문제.",
                evidence=[s],
            )
        )

    return QuizResult(items=items)

# APIs using the schema and functions

app = FastAPI(title = "personal Q")


@app.get('/health')
def health():
    return {"ok" : True}

@app.post('/api/parse_info')
async def parse_info(file : UploadFile = File(...)):
    if not (file.filename or '').lower().endswith('.pdf'):
        raise HTTPException(status_code = 400, detail='PDF only')
    
    pdf_bytes = await file.read()
    result = extract_text_from_pdf_bytes(pdf_bytes)
    return result

@app.post('/api/quiz')
async def quiz(req: QuizRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    return generate_quiz(req.text, req.max_items) 

# gradio demo

def ui_extract(pdf_file):
    if pdf_file is None:
        return "please upload a pdf file", ""

    with open(pdf_file, "rb") as f:
        pdf_bytes = f.read()

    res = extract_text_from_pdf_bytes(pdf_bytes)
    page_list = []
    
    meta = f'pages={len(res.pages)}, total_chars={res.total_chars}, used_ocr={res.used_ocr}'

    for page in res.pages:
        # each page is a PageText object from an ExtractResult object
        if page.text:
            s = f'[page {page.page}, | {page.source}]: \n {page.text}'
            page_list.append(s)
    joined = '\n\n'.join(page_list)

    return meta, joined

def ui_quiz(text, max_items):
    qr = generate_quiz(text, int(max_items))
    return qr.model_dump() # switch the basemodel obj to JSON 

with gr.Blocks(title="Quizzy") as demo:
    gr.Markdown("# Quizzy (Local)\nFastAPI(API) + Gradio(UI) 통합 MVP")

    pdf = gr.File(label="Upload PDF", file_types=[".pdf"])
    extract_btn = gr.Button("1) Extract Text")
    meta = gr.Textbox(label="Extraction meta", interactive=False)
    extracted = gr.Textbox(label="Extracted text", lines=18)

    extract_btn.click(ui_extract, inputs=[pdf], outputs=[meta, extracted])

    max_items = gr.Slider(4, 30, value=12, step=1, label="Max quiz items")
    quiz_btn = gr.Button("2) Generate Quiz")
    quiz_json = gr.JSON(label="Quiz JSON")

    quiz_btn.click(ui_quiz, inputs=[extracted, max_items], outputs=[quiz_json])


app = gr.mount_gradio_app(app, demo, path="/")







