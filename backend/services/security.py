import re
import logging

logger = logging.getLogger(__name__)

# ── 1. Prompt Injection Detection ─────────────────────────────────────────────

# Patterns that indicate an attacker is trying to hijack the LLM
INJECTION_PATTERNS = [
    r"ignore (previous|all|above|prior) instructions",
    r"disregard (previous|all|above|prior) instructions",
    r"forget (everything|all|previous|above)",
    r"you are now",
    r"act as (a|an|if)",
    r"pretend (you are|to be)",
    r"new (role|persona|instructions|system prompt)",
    r"override (instructions|system|prompt)",
    r"system prompt",
    r"jailbreak",
    r"do anything now",
    r"dan mode",
    r"developer mode",
    r"<\|.*\|>",                  # token injection patterns
    r"\[INST\]",                  # llama instruction injection
    r"###\s*(instruction|system|prompt)",
    r"reveal (your|the) (prompt|instructions|system)",
    r"what (are|were) your instructions",
    r"print (your|the) system prompt",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_prompt_injection(text: str, source: str = "input") -> tuple[bool, str]:
    """
    Scan text for prompt injection patterns.

    Returns:
        (is_safe, reason) — True if safe, False + reason if attack detected
    """
    if not text:
        return True, ""

    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            reason = f"Prompt injection detected in {source}: matched pattern '{match.group()}'"
            logger.warning(f"🚨 SECURITY ALERT — {reason}")
            return False, reason

    return True, ""


# ── 2. Input Sanitization ─────────────────────────────────────────────────────

# Characters / sequences that should never appear in resume or job query text
DANGEROUS_PATTERNS = [
    r"<script.*?>.*?</script>",   # XSS script tags
    r"javascript:",               # JS URI scheme
    r"on\w+\s*=",                 # HTML event handlers (onclick=, onerror=, etc.)
    r"<iframe.*?>",               # iframe injection
    r"\\x[0-9a-fA-F]{2}",        # hex escape sequences
    r"\x00",                      # null bytes
]

DANGEROUS_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in DANGEROUS_PATTERNS]


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """
    Sanitize free-text input before it reaches the LLM.

    - Strip dangerous HTML/JS patterns
    - Remove null bytes
    - Truncate to max_length
    - Collapse excessive whitespace
    """
    if not text:
        return ""

    # Remove dangerous patterns
    for pattern in DANGEROUS_COMPILED:
        text = pattern.sub("", text)

    # Strip null bytes
    text = text.replace("\x00", "")

    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Truncate
    if len(text) > max_length:
        logger.warning(f"Input truncated from {len(text)} to {max_length} chars")
        text = text[:max_length]

    return text.strip()


def validate_job_query(query: str) -> tuple[bool, str]:
    """
    Validate a job search query string.
    Checks for injection + sanitizes.

    Returns:
        (is_valid, sanitized_query_or_error_message)
    """
    if not query:
        return True, ""

    # Check for injection
    is_safe, reason = detect_prompt_injection(query, source="job query")
    if not is_safe:
        return False, reason

    # Sanitize
    clean = sanitize_text(query, max_length=200)
    return True, clean


def validate_resume_text(text: str) -> tuple[bool, str]:
    """
    Validate extracted resume text before sending to LLM.
    Checks for injection + sanitizes.

    Returns:
        (is_valid, sanitized_text_or_error_message)
    """
    if not text:
        return False, "Resume text is empty"

    # Check for injection
    is_safe, reason = detect_prompt_injection(text, source="resume")
    if not is_safe:
        return False, reason

    # Sanitize
    clean = sanitize_text(text, max_length=10000)
    return True, clean

# ── 7. LLM Output Filter ──────────────────────────────────────────────────────

# PII patterns to detect in LLM output
PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL REDACTED]"),
    (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE REDACTED]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
    (r"\b4[0-9]{12}(?:[0-9]{3})?\b", "[CARD REDACTED]"),
    (r"\b(?:5[1-5][0-9]{14})\b", "[CARD REDACTED]"),
]

TOXIC_KEYWORDS = [
    "kill", "bomb", "attack", "exploit", "hack the",
    "destroy", "murder", "terrorist",
]

PII_COMPILED = [(re.compile(p, re.IGNORECASE), r) for p, r in PII_PATTERNS]


def filter_llm_output(text: str, source: str = "llm output") -> tuple[str, list[str]]:
    """
    Scan and clean LLM output for PII and toxic content.

    Returns:
        (cleaned_text, list_of_warnings)
    """
    if not text:
        return text, []

    warnings = []

    # Redact PII
    for pattern, replacement in PII_COMPILED:
        if pattern.search(text):
            warnings.append(f"PII detected and redacted in {source}")
            text = pattern.sub(replacement, text)

    # Flag toxic content
    text_lower = text.lower()
    for keyword in TOXIC_KEYWORDS:
        if keyword in text_lower:
            warnings.append(f"Toxic keyword '{keyword}' found in {source}")
            logger.warning(f"🚨 TOXIC CONTENT in {source}: keyword='{keyword}'")

    if warnings:
        logger.warning(f"LLM output filter triggered: {warnings}")

    return text, warnings