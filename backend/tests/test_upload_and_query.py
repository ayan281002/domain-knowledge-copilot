from io import BytesIO

from app.routes import query as query_route


class DummyIndex:
    def store_upload(self, corpus_id, upload_file):
        return "dummy.txt"

    def index(self, corpus_id, filepath, original_name):
        return 3


class DummyLLM:
    def rewrite_query(self, question):
        return question

    def ask(self, prompt):
        return "This is an answer from context"

    def parse_answer_and_citations(self, raw):
        return raw, [{"source_file": "doc.txt", "page": 1, "chunk_id": "c1", "excerpt": "chunk excerpt"}]


class DummyRetrieval:
    def hybrid_retrieve(self, corpus_id, question):
        return [
            {
                "text": "Kubernetes security uses RBAC.",
                "metadata": {"source_file": "doc.txt", "page_number": 1, "chunk_id": "c1"},
                "semantic_distance": 0.1,
                "rrf_score": 1.0,
                "rerank_score": 3.5,
            }
        ]


def test_upload_endpoint(client, auth_token, monkeypatch):
    headers = {"Authorization": f"Bearer {auth_token}"}
    c = client.post("/corpora", json={"name": "Docs"}, headers=headers).json()

    monkeypatch.setattr(query_route, "IndexingService", lambda: DummyIndex())

    file_data = BytesIO(b"hello world")
    response = client.post(
        f"/corpora/{c['id']}/upload",
        files={"file": ("test.txt", file_data, "text/plain")},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["chunks_created"] == 3


def test_query_endpoint_and_chat_history(client, auth_token, monkeypatch):
    headers = {"Authorization": f"Bearer {auth_token}"}
    corpus = client.post("/corpora", json={"name": "Docs"}, headers=headers).json()

    monkeypatch.setattr(query_route, "LLMService", lambda: DummyLLM())
    monkeypatch.setattr(query_route, "RetrievalService", lambda: DummyRetrieval())

    response = client.post(
        f"/corpora/{corpus['id']}/query",
        json={"question": "What about security?"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"]
    assert data["citations"]

    messages = client.get(f"/sessions/{data['session_id']}/messages", headers=headers)
    assert messages.status_code == 200
    assert len(messages.json()) == 2
