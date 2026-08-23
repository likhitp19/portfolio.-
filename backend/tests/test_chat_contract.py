from app.schemas.chat import ChatRequest


def test_send_chat_contract_matches_architecture():
    body = ChatRequest(message="hello", thread_id=None, year=2024, meeting_key=1)
    dumped = body.model_dump(exclude_none=True)
    assert dumped["message"] == "hello"
    assert dumped["year"] == 2024
    assert dumped["meeting_key"] == 1
    assert "thread_id" not in dumped
