"""Unit test directory conftest — auto-applies the ``unit`` marker."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add ``@pytest.mark.unit`` to every test collected from ``tests/unit/``."""
    unit_marker = pytest.mark.unit
    for item in items:
        if "/tests/unit/" in str(item.fspath) or "\\tests\\unit\\" in str(item.fspath):
            if "unit" not in {m.name for m in item.iter_markers()}:
                item.add_marker(unit_marker)
