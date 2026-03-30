"""Property test directory conftest — auto-applies the ``property`` marker."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add ``@pytest.mark.property`` to every test collected from ``tests/property/``."""
    property_marker = pytest.mark.property
    for item in items:
        if "/tests/property/" in str(item.fspath) or "\\tests\\property\\" in str(
            item.fspath
        ):
            if "property" not in {m.name for m in item.iter_markers()}:
                item.add_marker(property_marker)
