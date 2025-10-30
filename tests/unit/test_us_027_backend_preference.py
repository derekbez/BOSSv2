import pytest

# Deprecated: Backend preference tests removed due to Textual-only screen backend.
pytestmark = pytest.mark.skip("Deprecated: backend preferences and Pillow have been removed.")

def test_deprecated_backend_preference():
    assert True
