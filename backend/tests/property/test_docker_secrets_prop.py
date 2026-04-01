"""Property-based test for absence of sensitive values in Docker instructions.

# Feature: docker-integration, Property 1

For any ENV or ARG instruction with a default value in the Backend Dockerfile,
the value must not contain API keys, passwords, or tokens. Specifically, no
instruction should contain values matching credential patterns (e.g., long
alphanumeric strings, prefixes like sk-, AIza, etc.).

**Validates: Requirements 5.3**
"""

import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DOCKERFILE = PROJECT_ROOT / "Dockerfile"
FRONTEND_DOCKERFILE = PROJECT_ROOT / "frontend" / "Dockerfile"


# ---------------------------------------------------------------------------
# Sensitive value detector
# ---------------------------------------------------------------------------

# Known secret prefixes (case-sensitive where appropriate)
_SECRET_PREFIXES = (
    "sk-",  # OpenAI / Stripe secret keys
    "sk_live_",  # Stripe live keys
    "sk_test_",  # Stripe test keys
    "AIza",  # Google API keys
    "ghp_",  # GitHub personal access tokens
    "gho_",  # GitHub OAuth tokens
    "ghs_",  # GitHub server tokens
    "github_pat_",  # GitHub fine-grained PATs
    "xoxb-",  # Slack bot tokens
    "xoxp-",  # Slack user tokens
    "AKIA",  # AWS access key IDs
    "eyJ",  # JWT tokens (base64 of '{"')
)

# Patterns that look like secrets
_SECRET_PATTERNS = [
    re.compile(r"^[A-Za-z0-9+/=_-]{32,}$"),  # Long base64-like strings
    re.compile(r"^[0-9a-f]{32,}$"),  # Long hex strings (MD5+)
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
]


def looks_like_secret(value: str) -> bool:
    """Return True if *value* resembles a hardcoded credential.

    Detection heuristics:
    1. Starts with a known secret prefix (sk-, AIza, ghp_, AKIA, …)
    2. Is a long alphanumeric/base64 string (≥ 32 chars)
    3. Contains keywords like 'password', 'secret', 'token', 'api_key'
    """
    stripped = value.strip().strip('"').strip("'")

    if not stripped:
        return False

    # Check known prefixes
    for prefix in _SECRET_PREFIXES:
        if stripped.startswith(prefix):
            return True

    # Check regex patterns
    for pattern in _SECRET_PATTERNS:
        if pattern.search(stripped):
            return True

    return False


def _parse_env_arg_values(dockerfile_content: str) -> list[tuple[str, str]]:
    """Extract (instruction, value) pairs from ENV and ARG lines with defaults.

    Returns tuples like ("ENV", "some_value") or ("ARG", "default_value").
    Only includes instructions that have an explicit default value.
    """
    results: list[tuple[str, str]] = []

    for line in dockerfile_content.splitlines():
        stripped = line.strip()

        # ARG VAR_NAME=default_value
        arg_match = re.match(r"^ARG\s+\w+=(.+)$", stripped)
        if arg_match:
            results.append(("ARG", arg_match.group(1).strip()))
            continue

        # ENV VAR_NAME=value  or  ENV VAR_NAME value
        env_match = re.match(r"^ENV\s+\w+=(.+)$", stripped)
        if env_match:
            results.append(("ENV", env_match.group(1).strip()))
            continue

        env_match2 = re.match(r"^ENV\s+\w+\s+(.+)$", stripped)
        if env_match2:
            results.append(("ENV", env_match2.group(1).strip()))

    return results


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Strategy: strings that look like real secrets
_secret_prefix_strategy = st.sampled_from(list(_SECRET_PREFIXES))
_alphanum_tail = st.from_regex(r"[A-Za-z0-9]{20,40}", fullmatch=True)

_secret_with_prefix = st.builds(
    lambda prefix, tail: prefix + tail,
    prefix=_secret_prefix_strategy,
    tail=_alphanum_tail,
)

_long_alphanum_secret = st.from_regex(r"[A-Za-z0-9+/=_-]{32,60}", fullmatch=True)

_keyword_secret = st.builds(
    lambda kw, val: f"{kw}_{val}",
    kw=st.sampled_from(["password", "secret", "token", "api_key", "apiKey"]),
    val=st.from_regex(r"[a-zA-Z0-9]{4,12}", fullmatch=True),
)

_secret_strategy = st.one_of(
    _secret_with_prefix,
    _long_alphanum_secret,
    _keyword_secret,
)

# Strategy: safe values that should NOT be flagged
_safe_value_strategy = st.one_of(
    st.sampled_from(
        [
            "/app",
            "/api",
            "8000",
            "80",
            "production",
            "development",
            "true",
            "false",
            "log_chunks",
            ".log,.txt,.json",
            "50",
            "utf-8",
            "INFO",
            "DEBUG",
        ]
    ),
    st.from_regex(r"[a-z]{1,10}", fullmatch=True),
    st.from_regex(r"[0-9]{1,5}", fullmatch=True),
    st.from_regex(r"/[a-z]{1,8}", fullmatch=True),
)


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(secret=_secret_strategy)
def test_detector_flags_secret_values(secret: str) -> None:
    """Feature: docker-integration, Property 1

    The sensitive-value detector must flag any string that matches known
    credential patterns (prefixed keys, long alphanumeric strings, keyword
    secrets).

    **Validates: Requirements 5.3**
    """
    assert looks_like_secret(secret), (
        f"Detector failed to flag a secret-like value: {secret!r}"
    )


@settings(max_examples=100)
@given(safe=_safe_value_strategy)
def test_detector_allows_safe_values(safe: str) -> None:
    """Feature: docker-integration, Property 1

    The sensitive-value detector must NOT flag short, simple configuration
    values (paths, ports, booleans, short lowercase words).

    **Validates: Requirements 5.3**
    """
    assert not looks_like_secret(safe), (
        f"Detector incorrectly flagged a safe value as secret: {safe!r}"
    )


def test_backend_dockerfile_has_no_secrets() -> None:
    """Feature: docker-integration, Property 1

    The actual Backend Dockerfile must not contain any ENV or ARG instruction
    whose default value looks like a hardcoded credential.

    **Validates: Requirements 5.3**
    """
    assert BACKEND_DOCKERFILE.exists(), (
        f"Backend Dockerfile not found: {BACKEND_DOCKERFILE}"
    )
    content = BACKEND_DOCKERFILE.read_text()
    pairs = _parse_env_arg_values(content)

    for instruction, value in pairs:
        assert not looks_like_secret(value), (
            f"Backend Dockerfile contains a potentially sensitive value in "
            f"{instruction} instruction: {value!r}"
        )


def test_frontend_dockerfile_has_no_secrets() -> None:
    """Feature: docker-integration, Property 1

    The actual Frontend Dockerfile must not contain any ENV or ARG instruction
    whose default value looks like a hardcoded credential.

    **Validates: Requirements 5.3**
    """
    assert FRONTEND_DOCKERFILE.exists(), (
        f"Frontend Dockerfile not found: {FRONTEND_DOCKERFILE}"
    )
    content = FRONTEND_DOCKERFILE.read_text()
    pairs = _parse_env_arg_values(content)

    for instruction, value in pairs:
        assert not looks_like_secret(value), (
            f"Frontend Dockerfile contains a potentially sensitive value in "
            f"{instruction} instruction: {value!r}"
        )
