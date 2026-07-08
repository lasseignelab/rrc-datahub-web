# pylint: disable=import-error
import os
import shutil

import pytest  # type: ignore[import-untyped]
from app import app as dash_app
from selenium.webdriver.chrome.options import Options  # type: ignore[import-untyped]

def pytest_configure(config):
    if not shutil.which("chromedriver"):
        try:
            from webdriver_manager.chrome import ChromeDriverManager  # type: ignore

            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)
            os.environ["PATH"] = driver_dir + os.pathsep + os.environ.get("PATH", "")
        except Exception as exc:  # noqa: BLE001
            print(f"\nWarning: could not auto-install ChromeDriver: {exc}")


def pytest_setup_options():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    return options


@pytest.fixture
def app():
    return dash_app
