import pytest
from app import app as dash_app


@pytest.fixture
def app():
    """Return the Dash app instance for use with dash_duo."""
    return dash_app
