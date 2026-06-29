import re
from fastapi import HTTPException, status


INJECTION_PATTERNS = [
    r"(?i)(ignore|forget|disregard)\s+(previous|above|all)\s+(instructions|prompts)",
    r"(?i)you\s+are\s+now\s+",
    r"(?i)act\s+as\s+(if|a)\s+",
    r"(?i)system\s*:\s*",
]


def check_prompt_injection(text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def sanitize_input(text: str) -> str:
    if check_prompt_injection(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input contains potentially malicious content",
        )
    return text.strip()
