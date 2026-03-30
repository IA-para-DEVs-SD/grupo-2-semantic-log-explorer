"""Unit tests for Frontend Dockerfile structure.

Verifies the multi-stage build structure of ./frontend/Dockerfile,
ensuring it has the correct stages, base images, ARG, EXPOSE, and
commands as defined in the docker-integration spec.
"""

import re
from pathlib import Path

import pytest

# Resolve project root: backend/tests/unit/test_docker_frontend.py -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE_PATH = PROJECT_ROOT / "frontend" / "Dockerfile"


@pytest.fixture
def dockerfile_content() -> str:
    """Read and return the Frontend Dockerfile content."""
    assert DOCKERFILE_PATH.exists(), f"Dockerfile not found at {DOCKERFILE_PATH}"
    return DOCKERFILE_PATH.read_text()


@pytest.fixture
def dockerfile_stages(dockerfile_content: str) -> list[dict]:
    """Parse Dockerfile into a list of stage dicts with name and lines."""
    stages: list[dict] = []
    current_stage: dict | None = None

    for line in dockerfile_content.splitlines():
        stripped = line.strip()
        from_match = re.match(r"^FROM\s+(\S+)(?:\s+AS\s+(\S+))?", stripped, re.IGNORECASE)
        if from_match:
            current_stage = {
                "image": from_match.group(1),
                "name": from_match.group(2),
                "lines": [stripped],
            }
            stages.append(current_stage)
        elif current_stage is not None and stripped and not stripped.startswith("#"):
            current_stage["lines"].append(stripped)

    return stages


class TestDockerfileStages:
    """Verify the Dockerfile has exactly 2 stages with correct names."""

    def test_has_exactly_two_stages(self, dockerfile_stages):
        assert len(dockerfile_stages) == 2, (
            f"Expected 2 stages, found {len(dockerfile_stages)}: "
            f"{[s['name'] for s in dockerfile_stages]}"
        )

    def test_stage_names(self, dockerfile_stages):
        names = [s["name"] for s in dockerfile_stages]
        assert names == ["build", "production"]

    def test_stage_order(self, dockerfile_stages):
        """Stages must appear in order: build -> production."""
        assert dockerfile_stages[0]["name"] == "build"
        assert dockerfile_stages[1]["name"] == "production"


class TestBuildStage:
    """Verify the build stage configuration."""

    def test_build_image_is_node_alpine(self, dockerfile_stages):
        build = dockerfile_stages[0]
        assert build["image"] == "node:18-alpine", (
            f"Build stage image should be node:18-alpine, got {build['image']}"
        )

    def test_arg_vite_api_url_defined(self, dockerfile_content):
        assert re.search(r"^ARG\s+VITE_API_URL", dockerfile_content, re.MULTILINE), (
            "Build stage must define ARG VITE_API_URL"
        )

    def test_npm_ci_is_called(self, dockerfile_stages):
        build = dockerfile_stages[0]
        build_text = "\n".join(build["lines"])
        assert "npm ci" in build_text, "Build stage must call 'npm ci'"

    def test_npm_run_build_is_called(self, dockerfile_stages):
        build = dockerfile_stages[0]
        build_text = "\n".join(build["lines"])
        assert "npm run build" in build_text, "Build stage must call 'npm run build'"


class TestProductionStage:
    """Verify the production stage configuration."""

    def test_production_image_is_nginx_alpine(self, dockerfile_stages):
        prod = dockerfile_stages[1]
        assert prod["image"] == "nginx:alpine", (
            f"Production stage image should be nginx:alpine, got {prod['image']}"
        )

    def test_expose_80(self, dockerfile_stages):
        prod = dockerfile_stages[1]
        expose_lines = [l for l in prod["lines"] if l.startswith("EXPOSE")]
        assert any("80" in l for l in expose_lines), (
            "Production stage must EXPOSE 80"
        )

    def test_copies_assets_from_build_stage(self, dockerfile_stages):
        prod = dockerfile_stages[1]
        copy_lines = [l for l in prod["lines"] if l.startswith("COPY")]
        assert any(
            "--from=build" in l and "/usr/share/nginx/html" in l for l in copy_lines
        ), "Production stage must copy assets from build stage to /usr/share/nginx/html"

    def test_copies_nginx_conf(self, dockerfile_stages):
        prod = dockerfile_stages[1]
        copy_lines = [l for l in prod["lines"] if l.startswith("COPY")]
        assert any("nginx.conf" in l for l in copy_lines), (
            "Production stage must copy nginx.conf"
        )
