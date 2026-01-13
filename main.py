from fastapi import FastAPI, UploadFile, File, HTTPException
from extractors import extract_text_from_pdf_bytes
from quiz import generate_quiz
from schemas import QuizRequest
from ui import create_gradio_demo
import gradio as gr

# FastAPI 앱 생성
app = FastAPI(title="personal Q")


@app.get('/health')
def health():
    return {"ok": True}


@app.post('/api/parse_info')
async def parse_info(file: UploadFile = File(...)):
    """PDF 파일에서 텍스트 추출 API"""
    if not (file.filename or '').lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='PDF only')
    
    pdf_bytes = await file.read()
    result = extract_text_from_pdf_bytes(pdf_bytes)
    return result


@app.post('/api/quiz')
async def quiz(req: QuizRequest):
    """텍스트에서 퀴즈 생성 API"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    return generate_quiz(req.text, req.max_items)


# Gradio UI 마운트
demo = create_gradio_demo()
app = gr.mount_gradio_app(app, demo, path="/")
