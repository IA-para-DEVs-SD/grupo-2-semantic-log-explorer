"""Unit tests for Backend Dockerfile structure.

Verifies the multi-stage build structure of ./Dockerfile (project root),
ensuring it has the correct stages, base image, WORKDIR, EXPOSE, and
commands as defined in the docker-integration spec.
"""

import re
from pathlib import Path

import pytest

# Resolve project root: backend/tests/unit/test_docker_backend.py -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE_PATH = PROJECT_ROOT / "Dockerfile"


@pytest.fixture
def dockerfile_content() -> str:
    """Read and return the Backend Dockerfile content."""
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
    """Verify the Dockerfile has exactly 3 stages with correct names."""

    def test_has_exactly_three_stages(self, dockerfile_stages):
        assert len(dockerfile_stages) == 3, (
            f"Expected 3 stages, found {len(dockerfile_stages)}: "
            f"{[s['name'] for s in dockerfile_stages]}"
        )

    def test_stage_names(self, dockerfile_stages):
        names = [s["name"] for s in dockerfile_stages]
        assert names == ["base", "test", "production"]

    def test_stage_order(self, dockerfile_stages):
        """Stages must appear in order: base -> test -> production."""
        assert dockerfile_stages[0]["name"] == "base"
        assert dockerfile_stages[1]["name"] == "test"
        assert dockerfile_stages[2]["name"] == "production"


class TestBaseStage:
    """Verify the base stage configuration."""

    def test_base_image_is_python_slim(self, dockerfile_stages):
        base = dockerfile_stages[0]
        assert re.match(r"python:3\.1[0-9]-slim", base["image"]), (
            f"Base image should be python:3.1x-slim, got {base['image']}"
        )

    def test_workdir_is_app(self, dockerfile_stages):
        base = dockerfile_stages[0]
        workdir_lines = [l for l in base["lines"] if l.startswith("WORKDIR")]
        assert any("/app" in l for l in workdir_lines), (
            "Base stage must set WORKDIR to /app"
        )

    def test_uv_is_installed(self, dockerfile_stages):
        base = dockerfile_stages[0]
        base_text = "\n".join(base["lines"])
        assert "uv" in base_text.lower(), "Base stage must install UV"

    def test_uv_sync_is_called(self, dockerfile_stages):
        base = dockerfile_stages[0]
        base_text = "\n".join(base["lines"])
        assert "uv sync" in base_text, "Base stage must call 'uv sync'"


class TestTestStage:
    """Verify the test stage configuration."""

    def test_inherits_from_base(self, dockerfile_stages):
        test_stage = dockerfile_stages[1]
        assert test_stage["image"] == "base", (
            f"Test stage should inherit from 'base', got '{test_stage['image']}'"
        )

    def test_runs_uv_sync_group_test(self, dockerfile_stages):
        test_stage = dockerfile_stages[1]
        test_text = "\n".join(test_stage["lines"])
        assert "uv sync" in test_text and "--group test" in test_text, (
            "Test stage must run 'uv sync --group test'"
        )


class TestProductionStage:
    """Verify the production stage configuration."""

    def test_inherits_from_base(self, dockerfile_stages):
        prod = dockerfile_stages[2]
        assert prod["image"] == "base", (
            f"Production stage should inherit from 'base', got '{prod['image']}'"
        )

    def test_copies_source_code(self, dockerfile_stages):
        prod = dockerfile_stages[2]
        copy_lines = [l for l in prod["lines"] if l.startswith("COPY")]
        assert len(copy_lines) > 0, "Production stage must COPY source code"

    def test_expose_8000(self, dockerfile_stages):
        prod = dockerfile_stages[2]
        expose_lines = [l for l in prod["lines"] if l.startswith("EXPOSE")]
        assert any("8000" in l for l in expose_lines), (
            "Production stage must EXPOSE 8000"
        )

    def test_cmd_has_uvicorn(self, dockerfile_stages):
        prod = dockerfile_stages[2]
        cmd_lines = [l for l in prod["lines"] if l.startswith("CMD")]
        assert len(cmd_lines) == 1, "Production stage must have exactly one CMD"
        assert "uvicorn" in cmd_lines[0], "CMD must run uvicorn"

    def test_no_test_dependencies(self, dockerfile_stages):
        prod = dockerfile_stages[2]
        prod_text = "\n".join(prod["lines"])
        assert "--group test" not in prod_text, (
            "Production stage must NOT include test dependencies"
        )
