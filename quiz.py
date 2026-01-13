from schemas import QuizItem, QuizResult


def generate_quiz(text: str, max_items: int = 12) -> QuizResult:
    """텍스트에서 퀴즈 생성 (MVP 버전)"""
    # 아주 간단한 문장 분리 (MVP)
    candidates = []
    for block in text.splitlines():
        s = block.strip()
        if len(s) >= 30:
            candidates.append(s)

    items: list[QuizItem] = []
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
