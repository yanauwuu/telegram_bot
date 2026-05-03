from __future__ import annotations


def make_prompt(
    question: str,
    context_chunks: list[str],
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    Собирает промпт для LLM.

    :param question: вопрос пользователя
    :param context_chunks: найденные куски текста
    :param history: история диалога
    :return: готовый промпт
    """
    context = "\n\n".join(context_chunks)
    history_text = ""

    if history is not None:
        for message in history[-6:]:
            role = message.get("role", "")
            text = message.get("text", "")
            history_text += f"{role}: {text}\n"

    prompt = f"""
Ты AI-ассистент для анализа технических инцидентов.

Отвечай простым языком.
Используй только контекст ниже.
Если информации не хватает, честно скажи, что данных недостаточно.
Не выдумывай факты.

История диалога:
{history_text}

Контекст:
{context}

Вопрос пользователя:
{question}

Ответ:
"""

    return prompt.strip()
