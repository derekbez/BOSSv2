"""
Fixtures for application services unit tests.
"""

import pytest
from unittest.mock import Mock
from boss.core import EventBus


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus for unit tests."""
    return Mock(spec=EventBus)
