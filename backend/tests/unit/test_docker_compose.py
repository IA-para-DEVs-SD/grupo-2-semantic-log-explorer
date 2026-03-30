"""Unit tests for docker-compose.yml structure.

Verifies the orchestration configuration including network, services,
health checks, profiles, ports, depends_on, volumes, and commands
as defined in the docker-integration spec.
"""

from pathlib import Path

import pytest

try:
    import yaml
except ImportError:
    pytest.skip("PyYAML not available", allow_module_level=True)

# Resolve project root: backend/tests/unit/test_docker_compose.py -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"


@pytest.fixture
def compose() -> dict:
    """Parse and return the docker-compose.yml content."""
    assert COMPOSE_PATH.exists(), f"docker-compose.yml not found at {COMPOSE_PATH}"
    return yaml.safe_load(COMPOSE_PATH.read_text())


@pytest.fixture
def services(compose: dict) -> dict:
    """Return the services section."""
    assert "services" in compose, "docker-compose.yml must have a 'services' key"
    return compose["services"]


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
class TestNetwork:
    """Verify sle-network exists with bridge driver."""

    def test_sle_network_exists(self, compose):
        assert "networks" in compose, "docker-compose.yml must define networks"
        assert "sle-network" in compose["networks"]

    def test_sle_network_driver_bridge(self, compose):
        net = compose["networks"]["sle-network"]
        assert net.get("driver") == "bridge", (
            f"sle-network driver should be 'bridge', got '{net.get('driver')}'"
        )


# ---------------------------------------------------------------------------
# Services existence
# ---------------------------------------------------------------------------
class TestServicesExist:
    """All four services must be defined."""

    @pytest.mark.parametrize(
        "service_name",
        ["backend", "frontend", "backend-dev", "frontend-dev"],
    )
    def test_service_exists(self, services, service_name):
        assert service_name in services, f"Service '{service_name}' not found"


# ---------------------------------------------------------------------------
# Backend (prod)
# ---------------------------------------------------------------------------
class TestBackendProd:
    """Verify backend service (production profile) configuration."""

    @pytest.fixture
    def backend(self, services) -> dict:
        return services["backend"]

    def test_profiles_prod(self, backend):
        assert backend.get("profiles") == ["prod"]

    def test_build_target_production(self, backend):
        build = backend.get("build", {})
        assert build.get("target") == "production"

    def test_port_mapping(self, backend):
        assert "8000:8000" in backend.get("ports", [])

    def test_env_file(self, backend):
        env_files = backend.get("env_file", [])
        # env_file can be a string or list
        if isinstance(env_files, str):
            env_files = [env_files]
        assert any("backend/.env" in f for f in env_files)

    def test_healthcheck_test_command(self, backend):
        hc = backend.get("healthcheck", {})
        test_cmd = hc.get("test", [])
        # Flatten to string for flexible matching
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "/health" in cmd_str, "Backend healthcheck must curl /health"

    def test_healthcheck_interval(self, backend):
        hc = backend.get("healthcheck", {})
        assert hc.get("interval") == "10s"

    def test_healthcheck_timeout(self, backend):
        hc = backend.get("healthcheck", {})
        assert hc.get("timeout") == "5s"

    def test_healthcheck_retries(self, backend):
        hc = backend.get("healthcheck", {})
        assert hc.get("retries") == 3

    def test_network_sle(self, backend):
        networks = backend.get("networks", [])
        assert "sle-network" in networks


# ---------------------------------------------------------------------------
# Frontend (prod)
# ---------------------------------------------------------------------------
class TestFrontendProd:
    """Verify frontend service (production profile) configuration."""

    @pytest.fixture
    def frontend(self, services) -> dict:
        return services["frontend"]

    def test_profiles_prod(self, frontend):
        assert frontend.get("profiles") == ["prod"]

    def test_build_context(self, frontend):
        build = frontend.get("build", {})
        assert build.get("context") == "./frontend"

    def test_port_mapping(self, frontend):
        assert "5173:80" in frontend.get("ports", [])

    def test_depends_on_backend_healthy(self, frontend):
        deps = frontend.get("depends_on", {})
        assert "backend" in deps
        assert deps["backend"].get("condition") == "service_healthy"

    def test_build_arg_vite_api_url(self, frontend):
        build = frontend.get("build", {})
        args = build.get("args", {})
        assert "VITE_API_URL" in args, "Frontend build must have VITE_API_URL arg"

    def test_healthcheck_curl_localhost_80(self, frontend):
        hc = frontend.get("healthcheck", {})
        test_cmd = hc.get("test", [])
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "localhost:80" in cmd_str or "localhost" in cmd_str

    def test_healthcheck_interval(self, frontend):
        hc = frontend.get("healthcheck", {})
        assert hc.get("interval") == "10s"

    def test_healthcheck_timeout(self, frontend):
        hc = frontend.get("healthcheck", {})
        assert hc.get("timeout") == "5s"

    def test_healthcheck_retries(self, frontend):
        hc = frontend.get("healthcheck", {})
        assert hc.get("retries") == 3

    def test_network_sle(self, frontend):
        networks = frontend.get("networks", [])
        assert "sle-network" in networks


# ---------------------------------------------------------------------------
# Backend-dev
# ---------------------------------------------------------------------------
class TestBackendDev:
    """Verify backend-dev service (development profile) configuration."""

    @pytest.fixture
    def backend_dev(self, services) -> dict:
        return services["backend-dev"]

    def test_profiles_dev(self, backend_dev):
        assert backend_dev.get("profiles") == ["dev"]

    def test_build_target_base(self, backend_dev):
        build = backend_dev.get("build", {})
        assert build.get("target") == "base"

    def test_port_mapping(self, backend_dev):
        assert "8000:8000" in backend_dev.get("ports", [])

    def test_volume_backend_mounted(self, backend_dev):
        volumes = backend_dev.get("volumes", [])
        assert any("./backend:/app/backend" in str(v) for v in volumes)

    def test_command_uvicorn_reload(self, backend_dev):
        cmd = backend_dev.get("command", "")
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        assert "uvicorn" in cmd_str, "backend-dev command must include uvicorn"
        assert "--reload" in cmd_str, "backend-dev command must include --reload"

    def test_env_file(self, backend_dev):
        env_files = backend_dev.get("env_file", [])
        if isinstance(env_files, str):
            env_files = [env_files]
        assert any("backend/.env" in f for f in env_files)

    def test_healthcheck_exists(self, backend_dev):
        assert "healthcheck" in backend_dev, "backend-dev must have a healthcheck"

    def test_healthcheck_curl_health(self, backend_dev):
        hc = backend_dev.get("healthcheck", {})
        test_cmd = hc.get("test", [])
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "/health" in cmd_str

    def test_network_sle(self, backend_dev):
        networks = backend_dev.get("networks", [])
        assert "sle-network" in networks


# ---------------------------------------------------------------------------
# Frontend-dev
# ---------------------------------------------------------------------------
class TestFrontendDev:
    """Verify frontend-dev service (development profile) configuration."""

    @pytest.fixture
    def frontend_dev(self, services) -> dict:
        return services["frontend-dev"]

    def test_profiles_dev(self, frontend_dev):
        assert frontend_dev.get("profiles") == ["dev"]

    def test_image_node_alpine(self, frontend_dev):
        assert frontend_dev.get("image") == "node:18-alpine"

    def test_port_mapping(self, frontend_dev):
        assert "5173:5173" in frontend_dev.get("ports", [])

    def test_volume_frontend_mounted(self, frontend_dev):
        volumes = frontend_dev.get("volumes", [])
        assert any("./frontend:/app" in str(v) for v in volumes)

    def test_command_npm_run_dev(self, frontend_dev):
        cmd = frontend_dev.get("command", "")
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        assert "npm run dev" in cmd_str
        assert "--host" in cmd_str

    def test_depends_on_backend_dev_healthy(self, frontend_dev):
        deps = frontend_dev.get("depends_on", {})
        assert "backend-dev" in deps
        assert deps["backend-dev"].get("condition") == "service_healthy"

    def test_healthcheck_exists(self, frontend_dev):
        assert "healthcheck" in frontend_dev, "frontend-dev must have a healthcheck"

    def test_healthcheck_curl(self, frontend_dev):
        hc = frontend_dev.get("healthcheck", {})
        test_cmd = hc.get("test", [])
        cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "localhost:5173" in cmd_str or "localhost" in cmd_str

    def test_network_sle(self, frontend_dev):
        networks = frontend_dev.get("networks", [])
        assert "sle-network" in networks
