"""Property-based test for Nginx SPA fallback on non-static routes.

# Feature: docker-integration, Property 3

For any URL that does not correspond to an existing static file in
``/usr/share/nginx/html``, the Nginx configuration must return
``index.html``.  This ensures that Vue Router works correctly with
client-side navigation.

**Validates: Requirement 7.3**
"""

import re
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
NGINX_CONF_PATH = PROJECT_ROOT / "frontend" / "nginx.conf"

# Common static-file extensions served directly by Nginx
_STATIC_EXTENSIONS = {
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
    ".json",
    ".webp",
    ".avif",
    ".html",
}


# ---------------------------------------------------------------------------
# Nginx config parser helpers (shared logic with test_nginx_proxy_prop)
# ---------------------------------------------------------------------------


def _parse_location_blocks(nginx_content: str) -> list[tuple[str, str]]:
    """Extract (pattern, body) pairs from ``location`` blocks."""
    blocks: list[tuple[str, str]] = []
    for m in re.finditer(r"location\s+([^\{]+?)\s*\{", nginx_content):
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
    """Return the most specific location block that matches *path*."""
    best: tuple[str, str] | None = None
    best_len = -1
    for pattern, body in blocks:
        if path.startswith(pattern) and len(pattern) > best_len:
            best = (pattern, body)
            best_len = len(pattern)
    return best


def _block_has_spa_fallback(body: str) -> bool:
    """Return True if the block contains a try_files directive that falls back to /index.html."""
    return bool(re.search(r"try_files\s+.*\s+/index\.html", body))


def _block_has_proxy_pass(body: str) -> bool:
    """Return True if the block contains a proxy_pass directive."""
    return bool(re.search(r"proxy_pass\s+", body))


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Path segments that look like Vue Router routes (no file extension)
_path_segment = st.from_regex(r"[a-z][a-z0-9-]{0,15}", fullmatch=True)

# Client-side SPA routes: /dashboard, /users/123, /settings/profile, etc.
_spa_route_strategy = st.builds(
    lambda segments: "/" + "/".join(segments),
    segments=st.lists(_path_segment, min_size=1, max_size=4),
)

# Paths with query strings: /dashboard?tab=overview
_spa_route_with_query = st.builds(
    lambda base, key, val: f"{base}?{key}={val}",
    base=_spa_route_strategy,
    key=st.from_regex(r"[a-z]{1,8}", fullmatch=True),
    val=st.from_regex(r"[a-zA-Z0-9]{1,12}", fullmatch=True),
)

# Paths with hash fragments: /dashboard#section
_spa_route_with_hash = st.builds(
    lambda base, frag: f"{base}#{frag}",
    base=_spa_route_strategy,
    frag=st.from_regex(r"[a-z]{1,10}", fullmatch=True),
)

# Combined strategy for all non-static, non-api SPA paths
_any_spa_route = st.one_of(
    _spa_route_strategy,
    _spa_route_with_query,
    _spa_route_with_hash,
)


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(path=_any_spa_route)
def test_non_static_routes_fallback_to_index_html(path: str) -> None:
    """Feature: docker-integration, Property 3

    For any URL that does not correspond to a static file and does not
    start with /api, the Nginx configuration must serve index.html via
    try_files fallback.  This is essential for Vue Router client-side
    navigation.

    **Validates: Requirement 7.3**
    """
    # Exclude /api paths — those are covered by Property 2
    match_path = path.split("?")[0].split("#")[0]
    assume(not match_path.startswith("/api"))

    # Ensure the path has no static file extension
    last_segment = match_path.rsplit("/", 1)[-1]
    assume(
        "." not in last_segment
        or not any(last_segment.endswith(ext) for ext in _STATIC_EXTENSIONS)
    )

    assert NGINX_CONF_PATH.exists(), f"nginx.conf not found at {NGINX_CONF_PATH}"
    content = NGINX_CONF_PATH.read_text()
    blocks = _parse_location_blocks(content)

    matched = _find_matching_block(blocks, match_path)
    assert matched is not None, f"No location block matches path {path!r}"

    pattern, body = matched
    assert _block_has_spa_fallback(body), (
        f"Path {path!r} matched location '{pattern}' which does NOT have "
        f"a try_files fallback to /index.html. All non-static routes must "
        f"fall back to index.html for SPA support."
    )
    assert not _block_has_proxy_pass(body), (
        f"Path {path!r} matched location '{pattern}' which has a proxy_pass "
        f"directive. Non-API routes should be handled by the SPA fallback, "
        f"not proxied to the backend."
    )


@settings(max_examples=100)
@given(path=_any_spa_route)
def test_catch_all_block_exists_with_try_files(path: str) -> None:
    """Feature: docker-integration, Property 3

    The catch-all ``location /`` block must exist and contain a try_files
    directive that falls back to /index.html, ensuring any unknown route
    is handled by the SPA.

    **Validates: Requirement 7.3**
    """
    match_path = path.split("?")[0].split("#")[0]
    assume(not match_path.startswith("/api"))

    assert NGINX_CONF_PATH.exists(), f"nginx.conf not found at {NGINX_CONF_PATH}"
    content = NGINX_CONF_PATH.read_text()
    blocks = _parse_location_blocks(content)

    # There must be a catch-all / block
    root_blocks = [(p, b) for p, b in blocks if p.strip() == "/"]
    assert len(root_blocks) >= 1, (
        "nginx.conf must contain a catch-all 'location /' block"
    )

    _, body = root_blocks[0]
    assert _block_has_spa_fallback(body), (
        "The catch-all 'location /' block must contain a try_files directive "
        "with fallback to /index.html for SPA routing support."
    )
