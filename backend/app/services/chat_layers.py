import re

from app.schemas.chat import ChatLayers


def split_answer_layers(answer: str) -> ChatLayers:
    text = (answer or "").strip()
    if not text:
        return ChatLayers(
            executive_summary="No briefing produced. Inspect the Technical Manager trace.",
            deep_dive="",
        )
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    lead = paragraphs[0]
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", lead) if part.strip()]
    summary = " ".join(sentences[:2]).strip()
    if len(summary) > 360:
        summary = summary[:357].rstrip() + "…"
    leftover = " ".join(sentences[2:]).strip()
    deep_parts = []
    if leftover:
        deep_parts.append(leftover)
    deep_parts.extend(paragraphs[1:])
    deep_dive = "\n\n".join(deep_parts).strip()
    if not deep_dive:
        deep_dive = text
    return ChatLayers(executive_summary=summary, deep_dive=deep_dive)
