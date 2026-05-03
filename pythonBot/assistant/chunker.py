from __future__ import annotations


def make_chunks(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[str]:
    """
    Делит большой текст на куски.

    :param text: исходный текст
    :param chunk_size: размер одного куска
    :param overlap: сколько символов повторять между кусками
    :return: список кусков текста
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks
