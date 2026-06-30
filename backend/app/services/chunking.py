from dataclasses import dataclass


@dataclass
class TextChunk:
    chunk_id: str
    text: str
    page_number: int | None


def recursive_char_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text.strip():
        return []

    separators = ["\n\n", "\n", ". ", " "]
    chunks: list[str] = []

    def split_with_sep(content: str, sep_index: int = 0):
        if len(content) <= chunk_size:
            chunks.append(content.strip())
            return

        if sep_index >= len(separators):
            start = 0
            while start < len(content):
                end = min(start + chunk_size, len(content))
                chunks.append(content[start:end].strip())
                start = max(end - overlap, start + 1)
            return

        sep = separators[sep_index]
        parts = content.split(sep)
        current = ""
        for part in parts:
            candidate = f"{current}{sep if current else ''}{part}".strip()
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > chunk_size:
                    split_with_sep(part, sep_index + 1)
                    current = ""
                else:
                    current = part
        if current:
            chunks.append(current)

    split_with_sep(text)

    merged: list[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            merged.append(chunk)
            continue
        prev = merged[-1]
        joined = (prev[-overlap:] + " " + chunk).strip()
        if len(joined) <= chunk_size + overlap:
            merged[-1] = joined
        else:
            merged.append(chunk)

    return [c for c in merged if c]
