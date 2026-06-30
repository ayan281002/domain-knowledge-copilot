from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.corpus import Corpus
from app.models.user import User
from app.schemas.corpus import CorpusCreate, CorpusRead
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/corpora", tags=["corpora"])


@router.post("", response_model=CorpusRead)
def create_corpus(payload: CorpusCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    corpus = Corpus(user_id=user.id, name=payload.name, description=payload.description)
    db.add(corpus)
    db.commit()
    db.refresh(corpus)
    return corpus


@router.get("", response_model=list[CorpusRead])
def list_corpora(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Corpus).filter(Corpus.user_id == user.id).order_by(Corpus.created_at.desc()).all()


@router.get("/{corpus_id}", response_model=CorpusRead)
def get_corpus(corpus_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id, Corpus.user_id == user.id).first()
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing corpus")
    return corpus


@router.delete("/{corpus_id}", status_code=204)
def delete_corpus(corpus_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id, Corpus.user_id == user.id).first()
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing corpus")

    RetrievalService().delete_corpus(corpus_id)
    db.delete(corpus)
    db.commit()
    return Response(status_code=204)
