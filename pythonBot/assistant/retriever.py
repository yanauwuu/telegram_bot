from __future__ import annotations

import re


def get_words(text: str) -> set[str]:
    """
    Достает слова из текста.

    :param text: строка
    :return: множество слов
    """
    text = text.lower()
    words = re.findall(r"[a-zа-яё0-9]+", text)

    return set(words)


def count_score(question: str, chunk: str) -> float:
    """
    Считает, насколько кусок текста похож на вопрос.

    :param question: вопрос пользователя
    :param chunk: кусок текста
    :return: число похожести
    """
    question_words = get_words(question)
    chunk_words = get_words(chunk)

    if not question_words:
        return 0

    same_words = question_words & chunk_words

    return len(same_words) / len(question_words)


def find_chunks(
    question: str,
    chunks: list[str],
    top_k: int = 3,
) -> list[str]:
    """
    Ищет самые подходящие куски текста.

    :param question: вопрос пользователя
    :param chunks: все куски базы знаний
    :param top_k: сколько кусков вернуть
    :return: список подходящих кусков
    """
    scored = []

    for chunk in chunks:
        score = count_score(question, chunk)
        scored.append((score, chunk))

    scored.sort(reverse=True, key=lambda item: item[0])

    result = []

    for score, chunk in scored[:top_k]:
        if score > 0:
            result.append(chunk)

    return result
