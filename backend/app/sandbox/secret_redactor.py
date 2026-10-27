"""
Secret Redactor — strips secrets, tokens, and credentials from terminal output
before it is streamed to the client or written to logs.
"""
import re
from typing import List, Tuple

# Patterns: (compiled_regex, replacement_label)
_REDACT_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # GitHub personal access tokens (classic + fine-grained)
    (re.compile(r"(ghp_|ghs_|gho_|github_pat_)[A-Za-z0-9_]{10,}"), "[REDACTED_GITHUB_TOKEN]"),
    # Generic Bearer tokens in headers
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-_\.=+/]{20,}"), r"\1[REDACTED]"),
    # OpenAI / Anthropic / Groq API keys
    (re.compile(r"(sk-(?:proj-|ant-|)[A-Za-z0-9\-_]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(gsk_[A-Za-z0-9_]{20,})"), "[REDACTED_GROQ_KEY]"),
    # AWS access/secret keys
    (re.compile(r"(?i)(aws_secret_access_key\s*[=:]\s*)[A-Za-z0-9/+=]{20,}"), r"\1[REDACTED]"),
    (re.compile(r"(AKIA[0-9A-Z]{16})"), "[REDACTED_AWS_KEY]"),
    # Generic password= assignments in URLs or config
    (re.compile(r"(?i)(password\s*[=:]\s*)\S+"), r"\1[REDACTED]"),
    # Database DSN credentials (postgres://user:pass@host)
    (re.compile(r"(?i)(://[^:@/\s]+:)[^@\s]+(@)"), r"\1[REDACTED]\2"),
    # .env VARIABLE=value patterns for common secrets
    (re.compile(r"(?im)^([A-Z_]*(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL)[A-Z_]*\s*=\s*)\S+"), r"\1[REDACTED]"),
]


def redact(text: str) -> str:
    """
    Apply all redaction patterns to text.
    Returns the sanitized string safe for client/log consumption.
    """
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_lines(lines: List[str]) -> List[str]:
    return [redact(line) for line in lines]
