"""PII sanitization module.

Masks sensitive data (CPF, e-mail, passwords) in log text using regex
before any downstream processing (embeddings, LLM calls).
"""

import re

# CPF: 000.000.000-00
_CPF_PATTERN = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")

# E-mail: user@domain.tld
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Passwords: common log patterns like password=..., senha=..., pwd=...
# Captures the key and replaces only the value portion.
_PASSWORD_PATTERN = re.compile(
    r"(?i)((?:password|passwd|pwd|senha|secret|token)\s*[=:]\s*)"
    r"(\S+)"
)

_CPF_MARKER = "[CPF_MASCARADO]"
_EMAIL_MARKER = "[EMAIL_MASCARADO]"
_PASSWORD_MARKER = "[SENHA_MASCARADA]"

# Prompt injection patterns — attempts to override system instructions
_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)"),
    re.compile(r"(?i)you\s+are\s+now\s+"),
    re.compile(r"(?i)disregard\s+(all\s+)?(previous|above|prior)"),
    re.compile(r"(?i)forget\s+(all\s+)?(previous|above|prior)\s+(instructions?|context)"),
    re.compile(r"(?i)new\s+instructions?:"),
    re.compile(r"(?i)system\s*prompt:"),
    re.compile(r"(?i)act\s+as\s+(if\s+you\s+are|a)\s+"),
    re.compile(r"(?i)pretend\s+(you\s+are|to\s+be)\s+"),
]


def sanitize_pii(text: str) -> str:
    """Replace PII patterns in *text* with safe markers.

    Order matters: passwords are replaced first to avoid partial matches
    when a password value happens to contain an e-mail or CPF.
    """
    text = _PASSWORD_PATTERN.sub(rf"\1{_PASSWORD_MARKER}", text)
    text = _CPF_PATTERN.sub(_CPF_MARKER, text)
    text = _EMAIL_PATTERN.sub(_EMAIL_MARKER, text)
    return text


def sanitize_prompt_injection(text: str) -> str:
    """Remove prompt injection attempts from user input.

    Strips known patterns that attempt to override system instructions
    or change the LLM's behavior.

    Args:
        text: Raw user input.

    Returns:
        Sanitized text with injection patterns removed.
    """
    for pattern in _PROMPT_INJECTION_PATTERNS:
        text = pattern.sub("[BLOCKED]", text)
    return text
