SYSTEM_PROMPT = """You are a domain knowledge assistant.

Answer ONLY using provided context.

If information is not found:
\"I could not find that information in the uploaded documents.\"

Always cite supporting sources.
"""


def build_rag_prompt(retrieved_chunks: str, user_question: str, history: str) -> str:
    return f"""Conversation history:
{history}

Context:
{retrieved_chunks}

Question:
{user_question}

Generate:
1. concise answer
2. citations
"""
