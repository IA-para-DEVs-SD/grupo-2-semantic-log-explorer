"""Unit tests for Nginx configuration.

Verifies the nginx.conf at ./frontend/nginx.conf has the correct
configuration for production: listen port, root directory, API proxy,
proxy headers, and SPA fallback as defined in the docker-integration spec.
"""

import re
from pathlib import Path

import pytest

# Resolve project root: backend/tests/unit/test_nginx_conf.py -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
NGINX_CONF_PATH = PROJECT_ROOT / "frontend" / "nginx.conf"


@pytest.fixture
def nginx_content() -> str:
    """Read and return the nginx.conf content."""
    assert NGINX_CONF_PATH.exists(), f"nginx.conf not found at {NGINX_CONF_PATH}"
    return NGINX_CONF_PATH.read_text()


class TestNginxListenPort:
    """Verify Nginx listens on port 80."""

    def test_listen_80_configured(self, nginx_content: str):
        assert re.search(r"listen\s+80\s*;", nginx_content), (
            "nginx.conf must configure 'listen 80'"
        )


class TestNginxRoot:
    """Verify Nginx root directory is set correctly."""

    def test_root_is_nginx_html(self, nginx_content: str):
        assert re.search(r"root\s+/usr/share/nginx/html\s*;", nginx_content), (
            "nginx.conf must set root to /usr/share/nginx/html"
        )


class TestNginxApiProxy:
    """Verify the /api location block with proxy_pass to backend."""

    def test_location_api_block_exists(self, nginx_content: str):
        assert re.search(r"location\s+/api\s*\{", nginx_content), (
            "nginx.conf must have a 'location /api' block"
        )

    def test_proxy_pass_to_backend(self, nginx_content: str):
        assert re.search(r"proxy_pass\s+http://backend:8000\s*;", nginx_content), (
            "nginx.conf must proxy_pass to http://backend:8000"
        )


class TestNginxProxyHeaders:
    """Verify proxy headers are set in the /api location block."""

    def test_proxy_header_host(self, nginx_content: str):
        assert re.search(r"proxy_set_header\s+Host\s+\$host\s*;", nginx_content), (
            "nginx.conf must set proxy header Host"
        )

    def test_proxy_header_x_real_ip(self, nginx_content: str):
        assert re.search(
            r"proxy_set_header\s+X-Real-IP\s+\$remote_addr\s*;", nginx_content
        ), "nginx.conf must set proxy header X-Real-IP"

    def test_proxy_header_x_forwarded_for(self, nginx_content: str):
        assert re.search(
            r"proxy_set_header\s+X-Forwarded-For\s+\$proxy_add_x_forwarded_for\s*;",
            nginx_content,
        ), "nginx.conf must set proxy header X-Forwarded-For"

    def test_proxy_header_x_forwarded_proto(self, nginx_content: str):
        assert re.search(
            r"proxy_set_header\s+X-Forwarded-Proto\s+\$scheme\s*;", nginx_content
        ), "nginx.conf must set proxy header X-Forwarded-Proto"


class TestNginxSpaFallback:
    """Verify the default location block with SPA fallback to index.html."""

    def test_location_root_block_exists(self, nginx_content: str):
        assert re.search(r"location\s+/\s*\{", nginx_content), (
            "nginx.conf must have a 'location /' block"
        )

    def test_try_files_fallback_to_index(self, nginx_content: str):
        assert re.search(
            r"try_files\s+\$uri\s+\$uri/\s+/index\.html\s*;", nginx_content
        ), "nginx.conf must have try_files with fallback to /index.html for SPA support"
