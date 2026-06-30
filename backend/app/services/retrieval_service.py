import json
from collections import defaultdict
from datetime import datetime

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.services.embedding_service import get_embedding_service


class RetrievalService:
    def __init__(self):
        self.settings = get_settings()
        self.embedder = None
        self.client = chromadb.PersistentClient(path=self.settings.chroma_path)
        self.reranker = None

    def _get_embedder(self):
        if self.embedder is None:
            self.embedder = get_embedding_service()
        return self.embedder

    def _get_reranker(self):
        if self.reranker is None:
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return self.reranker

    def _collection_name(self, corpus_id: int) -> str:
        return f"corpus_{corpus_id}"

    def get_collection(self, corpus_id: int):
        return self.client.get_or_create_collection(
            name=self._collection_name(corpus_id),
            metadata={"hnsw:space": "cosine"},
        )

    def _rrf(self, semantic_ids: list[str], bm25_ids: list[str], k: int = 60) -> dict[str, float]:
        scores = defaultdict(float)
        for rank, doc_id in enumerate(semantic_ids, start=1):
            scores[doc_id] += 1.0 / (k + rank)
        for rank, doc_id in enumerate(bm25_ids, start=1):
            scores[doc_id] += 1.0 / (k + rank)
        return scores

    def hybrid_retrieve(self, corpus_id: int, question: str) -> list[dict]:
        collection = self.get_collection(corpus_id)
        query_vector = self._get_embedder().embed_text(question)
        semantic = collection.query(
            query_embeddings=[query_vector],
            n_results=self.settings.top_k_semantic,
            include=["documents", "metadatas", "distances"],
        )

        docs = semantic.get("documents", [[]])[0]
        metas = semantic.get("metadatas", [[]])[0]
        distances = semantic.get("distances", [[]])[0]
        ids = semantic.get("ids", [[]])[0]

        if not docs:
            return []

        tokenized_docs = [d.lower().split() for d in docs]
        bm25 = BM25Okapi(tokenized_docs)
        bm25_scores = bm25.get_scores(question.lower().split())
        bm25_ranked = [x[0] for x in sorted(enumerate(bm25_scores), key=lambda y: y[1], reverse=True)]

        semantic_ranked_ids = ids
        bm25_ranked_ids = [ids[i] for i in bm25_ranked]
        fused = self._rrf(semantic_ranked_ids, bm25_ranked_ids)

        candidates = []
        for i, doc_id in enumerate(ids):
            candidates.append(
                {
                    "id": doc_id,
                    "text": docs[i],
                    "metadata": metas[i],
                    "semantic_distance": float(distances[i]),
                    "rrf_score": fused.get(doc_id, 0.0),
                }
            )

        candidates = sorted(candidates, key=lambda x: x["rrf_score"], reverse=True)
        pairs = [[question, c["text"]] for c in candidates[: self.settings.top_k_semantic]]
        rerank_scores = self._get_reranker().predict(pairs)

        for i, score in enumerate(rerank_scores):
            candidates[i]["rerank_score"] = float(score)

        top = sorted(candidates[: len(rerank_scores)], key=lambda x: x["rerank_score"], reverse=True)
        return top[: self.settings.top_k_final]

    def upsert_chunks(self, corpus_id: int, chunks: list[dict]):
        collection = self.get_collection(corpus_id)
        texts = [c["text"] for c in chunks]
        embeddings = self._get_embedder().embed_texts(texts)
        collection.upsert(
            ids=[c["chunk_id"] for c in chunks],
            documents=texts,
            metadatas=[
                {
                    "source_file": c["source_file"],
                    "page_number": c["page_number"] if c["page_number"] is not None else -1,
                    "chunk_id": c["chunk_id"],
                    "corpus_id": corpus_id,
                    "upload_timestamp": datetime.utcnow().isoformat(),
                }
                for c in chunks
            ],
            embeddings=embeddings,
        )

    def delete_corpus(self, corpus_id: int):
        try:
            self.client.delete_collection(self._collection_name(corpus_id))
        except Exception:
            return


def serialize_citations(chunks: list[dict]) -> str:
    citations = [
        {
            "source_file": c["metadata"].get("source_file", "unknown"),
            "page": None if c["metadata"].get("page_number", -1) == -1 else c["metadata"].get("page_number"),
            "chunk_id": c["metadata"].get("chunk_id", ""),
            "excerpt": c["text"][:400],
        }
        for c in chunks
    ]
    return json.dumps(citations)
