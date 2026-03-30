"""Property-based test for Nginx reverse proxy routing of /api paths.

# Feature: docker-integration, Property 2

For any HTTP request whose path starts with /api, the Nginx configuration
must route it to the Backend service on port 8000 via proxy_pass. This
ensures that no /api route is ever treated as a static file.

**Validates: Requirement 7.2**
"""

import re
from pathlib import Path

from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
NGINX_CONF_PATH = PROJECT_ROOT / "frontend" / "nginx.conf"


# ---------------------------------------------------------------------------
# Nginx config parser helpers
# ---------------------------------------------------------------------------

def _parse_location_blocks(nginx_content: str) -> list[tuple[str, str]]:
    """Extract (pattern, body) pairs from ``location`` blocks.

    Returns a list of tuples where *pattern* is the location match string
    (e.g. ``/api``, ``/``) and *body* is the raw text inside the braces.
    Handles single-level nesting only (sufficient for typical nginx configs).
    """
    blocks: list[tuple[str, str]] = []
    # Match  location <pattern> { ... }
    for m in re.finditer(
        r"location\s+([^\{]+?)\s*\{", nginx_content
    ):
        pattern = m.group(1).strip()
        start = m.end()
        depth = 1
        pos = start
        while pos < len(nginx_content) and depth > 0:
            if nginx_content[pos] == "{":
                depth += 1
            elif nginx_content[pos] == "}":
                depth -= 1
            pos += 1
        body = nginx_content[start : pos - 1]
        blocks.append((pattern, body))
    return blocks


def _find_matching_block(
    blocks: list[tuple[str, str]], path: str
) -> tuple[str, str] | None:
    """Return the most specific location block that matches *path*.

    Implements simplified Nginx prefix-match semantics:
    - Exact / longest prefix match wins.
    - ``/api`` matches any path starting with ``/api``.
    - ``/`` matches everything (catch-all).
    """
    best: tuple[str, str] | None = None
    best_len = -1
    for pattern, body in blocks:
        # Prefix match
        if path.startswith(pattern) and len(pattern) > best_len:
            best = (pattern, body)
            best_len = len(pattern)
    return best


def _block_has_proxy_pass_to_backend(body: str) -> bool:
    """Return True if the block body contains a proxy_pass to backend:8000."""
    return bool(re.search(r"proxy_pass\s+http://backend:8000", body))


def _block_is_static_fallback(body: str) -> bool:
    """Return True if the block serves static files (try_files / root)."""
    return bool(re.search(r"try_files", body))


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Segments that could appear in a realistic API path
_path_segment = st.from_regex(r"[a-zA-Z0-9_-]{1,20}", fullmatch=True)

# /api, /api/, /api/anything, /api/v1/resource/123 …
_api_path_strategy = st.builds(
    lambda segments: "/api" + ("/" + "/".join(segments) if segments else ""),
    segments=st.lists(_path_segment, min_size=0, max_size=5),
)

# Paths with query strings: /api/resource?key=value
_api_path_with_query = st.builds(
    lambda base, key, val: f"{base}?{key}={val}",
    base=_api_path_strategy,
    key=st.from_regex(r"[a-z]{1,8}", fullmatch=True),
    val=st.from_regex(r"[a-zA-Z0-9]{1,12}", fullmatch=True),
)

# Combined strategy for all /api paths
_any_api_path = st.one_of(_api_path_strategy, _api_path_with_query)


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(path=_any_api_path)
def test_api_paths_routed_to_backend(path: str) -> None:
    """Feature: docker-integration, Property 2

    For any path starting with /api, the Nginx configuration must match it
    to a location block that proxies the request to backend:8000 — never
    to the static file handler.

    **Validates: Requirement 7.2**
    """
    assert NGINX_CONF_PATH.exists(), f"nginx.conf not found at {NGINX_CONF_PATH}"
    content = NGINX_CONF_PATH.read_text()
    blocks = _parse_location_blocks(content)

    # Strip query string for location matching (Nginx matches on path only)
    match_path = path.split("?")[0]

    matched = _find_matching_block(blocks, match_path)
    assert matched is not None, (
        f"No location block matches path {path!r}"
    )

    pattern, body = matched
    assert _block_has_proxy_pass_to_backend(body), (
        f"Path {path!r} matched location '{pattern}' which does NOT proxy "
        f"to backend:8000. All /api requests must be reverse-proxied."
    )
    assert not _block_is_static_fallback(body), (
        f"Path {path!r} matched location '{pattern}' which uses try_files "
        f"(static file serving). /api requests must never be served as "
        f"static files."
    )


@settings(max_examples=100)
@given(path=_any_api_path)
def test_api_location_is_more_specific_than_root(path: str) -> None:
    """Feature: docker-integration, Property 2

    The /api location block must always win over the catch-all / block
    for any path starting with /api, ensuring prefix-match specificity.

    **Validates: Requirement 7.2**
    """
    assert NGINX_CONF_PATH.exists(), f"nginx.conf not found at {NGINX_CONF_PATH}"
    content = NGINX_CONF_PATH.read_text()
    blocks = _parse_location_blocks(content)

    # There must be an /api block
    api_blocks = [(p, b) for p, b in blocks if p.strip() == "/api"]
    assert len(api_blocks) >= 1, (
        "nginx.conf must contain a 'location /api' block"
    )

    # The /api block must be longer prefix than /
    match_path = path.split("?")[0]
    matched = _find_matching_block(blocks, match_path)
    assert matched is not None
    pattern, _ = matched
    assert pattern.strip() != "/", (
        f"Path {path!r} incorrectly matched the catch-all '/' block "
        f"instead of the '/api' block."
    )
