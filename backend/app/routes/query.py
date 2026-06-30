import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.corpus import Corpus
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.rag.prompting import build_rag_prompt
from app.schemas.chat import QueryRequest, QueryResponse
from app.schemas.corpus import UploadResponse
from app.services.indexing_service import IndexingService
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService, serialize_citations

router = APIRouter(tags=["rag"])


def _get_or_create_session(db: Session, corpus_id: int, session_id: int | None) -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.corpus_id == corpus_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing session")
        return session

    session = ChatSession(corpus_id=corpus_id, title="New chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _history_window(db: Session, session_id: int, turns: int) -> str:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(turns * 2)
        .all()
    )
    lines = []
    for m in reversed(messages):
        role = "User" if m.role == "question" else "Assistant"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)


@router.post("/corpora/{corpus_id}/upload", response_model=UploadResponse)
def upload_document(
    corpus_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id, Corpus.user_id == user.id).first()
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing corpus")

    service = IndexingService()
    try:
        filepath = service.store_upload(corpus_id=corpus_id, upload_file=file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    chunks_created = service.index(corpus_id=corpus_id, filepath=filepath, original_name=file.filename or "uploaded")

    up = UploadedFile(corpus_id=corpus_id, filename=file.filename or "uploaded", filepath=filepath)
    db.add(up)
    db.commit()

    return UploadResponse(status="indexed", chunks_created=chunks_created, filename=file.filename or "uploaded")


@router.post("/corpora/{corpus_id}/query", response_model=QueryResponse)
def query_corpus(
    corpus_id: int,
    payload: QueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id, Corpus.user_id == user.id).first()
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing corpus")

    settings = get_settings()
    llm = LLMService()
    retrieval = RetrievalService()

    session = _get_or_create_session(db, corpus_id, payload.session_id)
    rewritten = llm.rewrite_query(payload.question)
    chunks = retrieval.hybrid_retrieve(corpus_id=corpus_id, question=rewritten)

    if not chunks:
        answer = "I could not find that information in the uploaded documents."
        citations = []
        retrieved_chunks = []
    else:
        history = _history_window(db, session.id, settings.history_turns)
        context = "\n\n".join(
            [
                f"[chunk_id={c['metadata'].get('chunk_id')}] [source={c['metadata'].get('source_file')}] "
                f"[page={c['metadata'].get('page_number')}]\n{c['text']}"
                for c in chunks
            ]
        )
        prompt = build_rag_prompt(retrieved_chunks=context, user_question=payload.question, history=history)
        answer_raw = llm.ask(prompt)
        answer, citations = llm.parse_answer_and_citations(answer_raw)

        if not citations:
            citations = json.loads(serialize_citations(chunks))

        retrieved_chunks = [
            {
                "text": c["text"],
                "metadata": c["metadata"],
                "semantic_distance": c.get("semantic_distance"),
                "rrf_score": c.get("rrf_score"),
                "rerank_score": c.get("rerank_score"),
            }
            for c in chunks
        ]

    db.add(ChatMessage(session_id=session.id, role="question", content=payload.question, citations_json=None))
    db.add(ChatMessage(session_id=session.id, role="answer", content=answer, citations_json=json.dumps(citations)))
    db.commit()

    return QueryResponse(answer=answer, citations=citations, retrieved_chunks=retrieved_chunks, session_id=session.id)
