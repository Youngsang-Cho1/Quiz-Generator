from pdf2image import convert_from_bytes
import pytesseract
import fitz
from schemas import PageText, ExtractResult


def is_garbage_text(text: str) -> bool:
    """텍스트 품질이 낮은지 판단하는 함수"""
    if not text:
        return True
    if len(text.strip()) < 100:
        return True

    tokens = text.split()
    if not tokens:
        return True

    num_alpha = sum(1 for t in tokens if any(c.isalpha() for c in t))
    if num_alpha / len(tokens) < 0.5:
        return True
    
    return False


def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = 30) -> ExtractResult:
    """PDF에서 텍스트 레이어를 추출 (품질이 낮으면 OCR로 전환)"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_number = min(len(doc), max_pages)

    pages = []
    total_chars = 0

    for i in range(page_number):
        page = doc.load_page(i)
        text = (page.get_text('text') or '').strip()
        total_chars += len(text)
        pages.append(PageText(page=i + 1, text=text, source="text_layer"))

    doc.close()

    joined = '\n\n'.join(p.text for p in pages)
    if is_garbage_text(joined):
        return ocr_pdf_bytes(pdf_bytes, max_pages=max_pages)

    return ExtractResult(pages=pages, total_chars=total_chars, used_ocr=False)


def ocr_pdf_bytes(pdf_bytes: bytes, max_pages: int = 30, lang: str = 'eng+kor') -> ExtractResult:
    """PDF를 이미지로 변환 후 OCR 수행"""
    images = convert_from_bytes(
        pdf_bytes,
        dpi=300,
        fmt='jpeg',
        first_page=1,
        thread_count=2,
        use_cropbox=True,
        strict=False
    )
    pages: list[PageText] = []
    total_chars = 0
    
    for idx, img in enumerate(images[:max_pages]):
        text = pytesseract.image_to_string(img, lang=lang).strip()

        try:
            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            confidence = sum(confidences) / len(confidences) if confidences else None
        except Exception as e:
            confidence = None
            print(f"Error in OCR data extraction: {e}")

        total_chars += len(text)

        pages.append(
            PageText(
                page=idx + 1,
                text=text,
                source='ocr',
                confidence=confidence,
            )
        )
    
    return ExtractResult(
        pages=pages,
        total_chars=sum(len(p.text) for p in pages),
        used_ocr=True
    )
