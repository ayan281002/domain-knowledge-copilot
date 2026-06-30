class RAGError(Exception):
    pass


class IndexingError(RAGError):
    pass


class LLMError(RAGError):
    pass


class RetrievalError(RAGError):
    pass
