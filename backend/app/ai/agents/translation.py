from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.agents.supervisor import get_llm


TRANSLATION_SYSTEM_PROMPT = """You are a translation assistant for Indian law enforcement.
Translate the given text between English and Hindi (or other Indian languages as specified).
Maintain legal terminology accuracy. Output only the translation, nothing else."""


async def translate_text(text: str, source_lang: str = "en", target_lang: str = "hi") -> str:
    llm = get_llm()

    messages = [
        SystemMessage(content=TRANSLATION_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Translate the following from {source_lang} to {target_lang}:\n\n{text}"
        ),
    ]

    response = await llm.ainvoke(messages)
    return response.content.strip()
