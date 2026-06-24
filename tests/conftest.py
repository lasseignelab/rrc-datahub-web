import os
import shutil

import pytest

from app import app as dash_app


def pytest_configure(config):
    """Add ChromeDriver to PATH via webdriver-manager if not already present.

    On CI (GitHub Actions), chromedriver is pre-installed so this is a no-op.
    On macOS dev machines it auto-downloads the matching version.
    """
    if not shutil.which("chromedriver"):
        try:
            from webdriver_manager.chrome import ChromeDriverManager

            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)
            os.environ["PATH"] = driver_dir + os.pathsep + os.environ.get("PATH", "")
        except Exception as exc:  # noqa: BLE001
            print(f"\nWarning: could not auto-install ChromeDriver: {exc}")


@pytest.fixture
def app():
    """Return the Dash app instance for use with dash_duo."""
    return dash_app
