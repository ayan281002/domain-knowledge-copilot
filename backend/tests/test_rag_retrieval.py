import json

from app.services.retrieval_service import serialize_citations


def test_serialize_citations():
    chunks = [
        {
            "text": "Example chunk text",
            "metadata": {"source_file": "report.pdf", "page_number": 3, "chunk_id": "abc123"},
        }
    ]
    raw = serialize_citations(chunks)
    data = json.loads(raw)
    assert data[0]["source_file"] == "report.pdf"
    assert data[0]["page"] == 3
    assert data[0]["chunk_id"] == "abc123"
