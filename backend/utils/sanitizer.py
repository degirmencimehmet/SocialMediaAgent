"""
Input sanitization — NFR-SEC-04
Strips prompt-injection patterns before injecting user text into LLM prompts.
"""
import re

# Patterns that attempt to hijack the LLM system prompt
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an)\s+\w+",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?instructions?",
    r"<\s*script",
    r"</?\s*[a-z]+[^>]*>",   # HTML tags
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def sanitize(text: str) -> str:
    """Remove or neutralize injection patterns. Returns cleaned text."""
    for pattern in _COMPILED:
        text = pattern.sub("[removed]", text)
    # Trim excess whitespace
    text = re.sub(r"\s{3,}", "  ", text).strip()
    return text


def is_safe(text: str) -> bool:
    """Return False if any injection pattern is detected."""
    for pattern in _COMPILED:
        if pattern.search(text):
            return False
    return True
