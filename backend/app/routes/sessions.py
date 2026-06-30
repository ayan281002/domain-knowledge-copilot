from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.corpus import Corpus
from app.models.user import User
from app.schemas.chat import MessageRead, SessionCreate, SessionRead

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionRead])
def list_sessions(corpus_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id, Corpus.user_id == user.id).first()
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing corpus")
    return (
        db.query(ChatSession)
        .filter(ChatSession.corpus_id == corpus_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )


@router.post("", response_model=SessionRead)
def create_session(payload: SessionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    corpus = db.query(Corpus).filter(Corpus.id == payload.corpus_id, Corpus.user_id == user.id).first()
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing corpus")

    title = payload.title or f"Session for {corpus.name}"
    session = ChatSession(corpus_id=payload.corpus_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = (
        db.query(ChatSession)
        .join(Corpus, Corpus.id == ChatSession.corpus_id)
        .filter(ChatSession.id == session_id, Corpus.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing session")
    return session


@router.get("/{session_id}/messages", response_model=list[MessageRead])
def get_session_messages(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = (
        db.query(ChatSession)
        .join(Corpus, Corpus.id == ChatSession.corpus_id)
        .filter(ChatSession.id == session_id, Corpus.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing session")

    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = (
        db.query(ChatSession)
        .join(Corpus, Corpus.id == ChatSession.corpus_id)
        .filter(ChatSession.id == session_id, Corpus.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing session")

    db.delete(session)
    db.commit()
    return Response(status_code=204)
