import gradio as gr
from extractors import extract_text_from_pdf_bytes
from quiz import generate_quiz


def ui_extract(pdf_file):
    """Gradio UI용 텍스트 추출 함수"""
    if pdf_file is None:
        return "please upload a pdf file", ""
    file_path = pdf_file if isinstance(pdf_file, str) else pdf_file.name
    if not file_path:
        return "no file path", ""

    with open(pdf_file, "rb") as f:
        pdf_bytes = f.read()

    res = extract_text_from_pdf_bytes(pdf_bytes)
    page_list = []
    
    meta = f'pages={len(res.pages)}, total_chars={res.total_chars}, used_ocr={res.used_ocr}'

    for page in res.pages:
        # each page is a PageText object from an ExtractResult object
        if page.text:
            confidence_str = f'confidence: {page.confidence}' if page.confidence else ''
            s = f'[page {page.page}, | {page.source}, {confidence_str}]: \n {page.text}'
            page_list.append(s)
    joined = '\n\n'.join(page_list)

    return meta, joined


def ui_quiz(text, max_items):
    """Gradio UI용 퀴즈 생성 함수"""
    qr = generate_quiz(text, int(max_items))
    return qr.model_dump()  # switch the basemodel obj to JSON


def create_gradio_demo():
    """Gradio UI 생성"""
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

    return demo
