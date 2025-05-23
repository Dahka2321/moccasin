import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Generator, List

import pytest
from typing_extensions import Final

import moccasin.constants.vars as vars
from moccasin.commands.wallet import save_to_keystores
from moccasin.config import Config, _set_global_config
from moccasin.constants.vars import DEPENDENCIES_FOLDER
from tests.constants import (
    ANVIL1_KEYSTORE_NAME,
    ANVIL1_KEYSTORE_PASSWORD,
    ANVIL1_PRIVATE_KEY,
    ANVIL_STORED_STATE_PATH,
    COMPLEX_PROJECT_PATH,
    INSTALL_PROJECT_PATH,
    INSTALLATION_FULL_DEPENDENCIES_TOML,
    INSTALLATION_NO_DEPENDENCIES_TOML,
    INSTALLATION_STARTING_TOML,
    INSTALLATION_WITH_GH_TOML,
    INSTALLATION_WITH_PIP_TOML,
    NO_CONFIG_PROJECT_PATH,
    PURGE_PROJECT_PATH,
    PURGE_STARTING_TOML,
    TESTS_CONFIG_PROJECT_PATH,
)
from tests.utils.anvil import ANVIL_URL, AnvilProcess


# ------------------------------------------------------------------
#                         BASIC FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def session_monkeypatch():
    monkeypatch = pytest.MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()


@pytest.fixture(scope="session")
def moccasin_home_folder(session_monkeypatch) -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        session_monkeypatch.setenv("MOCCASIN_DEFAULT_FOLDER", temp_dir)
        session_monkeypatch.setattr(vars, "MOCCASIN_DEFAULT_FOLDER", Path(temp_dir))
        yield Path(temp_dir)


@pytest.fixture(scope="session")
def anvil_keystore(session_monkeypatch, moccasin_home_folder):
    keystore_path = moccasin_home_folder.joinpath("keystores")
    save_to_keystores(
        ANVIL1_KEYSTORE_NAME,
        ANVIL1_PRIVATE_KEY,
        password=ANVIL1_KEYSTORE_PASSWORD,
        keystores_path=Path(keystore_path),
    )
    session_monkeypatch.setenv("MOCCASIN_KEYSTORE_PATH", str(keystore_path))
    session_monkeypatch.setattr(vars, "MOCCASIN_KEYSTORE_PATH", keystore_path)
    with tempfile.NamedTemporaryFile(mode="w") as temp_file:
        temp_file_path = Path(temp_file.name)
        session_monkeypatch.setenv("ANVIL1_PASSWORD_FILE", str(temp_file_path))
        temp_file.write(ANVIL1_KEYSTORE_PASSWORD)
        temp_file.flush()
        yield Path(keystore_path)


@pytest.fixture(scope="session")
def set_fake_chain_rpc(session_monkeypatch):
    session_monkeypatch.setenv("FAKE_CHAIN_RPC_URL", ANVIL_URL)
    yield


@pytest.fixture(scope="session")
def mox_path():
    return os.path.join(os.path.dirname(sys.executable), "mox")


@pytest.fixture(scope="function")
def custom_moccasin_keystore_path(session_monkeypatch, moccasin_home_folder):
    """Set a custom keystore path for testing wallet `keystore-location`."""
    custom_path = moccasin_home_folder.joinpath("custom_keystore")
    session_monkeypatch.setenv("MOCCASIN_KEYSTORE_PATH", str(custom_path))
    yield Path(custom_path)


# ------------------------------------------------------------------
#                    COMPLEX PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def complex_temp_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        if Path(COMPLEX_PROJECT_PATH.joinpath(".deployments.db")).exists():
            os.remove(COMPLEX_PROJECT_PATH.joinpath(".deployments.db"))
        shutil.copytree(
            COMPLEX_PROJECT_PATH, os.path.join(temp_dir), dirs_exist_ok=True
        )
        yield Path(temp_dir)


@pytest.fixture(scope="module")
def complex_project_config(complex_temp_path) -> Config:
    test_db_path = os.path.join(complex_temp_path, ".deployments.db")

    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    config = _set_global_config(complex_temp_path)
    return config


@pytest.fixture(scope="module")
def complex_out_folder(complex_project_config) -> Config:
    return complex_project_config.out_folder


# REVIEW: Do we need these if we are using a temp dir?
@pytest.fixture
def complex_cleanup_coverage(complex_temp_path):
    yield
    coverage_file = complex_temp_path.joinpath(".coverage")
    if os.path.exists(coverage_file):
        os.remove(coverage_file)


@pytest.fixture
def complex_cleanup_out_folder(complex_temp_path, complex_out_folder):
    yield
    created_folder_path = complex_temp_path.joinpath(complex_out_folder)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


@pytest.fixture
def complex_cleanup_dependencies_folder(complex_temp_path):
    yield
    created_folder_path = complex_temp_path.joinpath(DEPENDENCIES_FOLDER)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


# ------------------------------------------------------------------
#                     INSTALLATION PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def installation_temp_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(
            INSTALL_PROJECT_PATH, os.path.join(temp_dir), dirs_exist_ok=True
        )
        yield Path(temp_dir)


@pytest.fixture(scope="module")
def installation_project_config(installation_temp_path) -> Config:
    test_db_path = os.path.join(installation_temp_path, ".deployments.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    return _set_global_config(installation_temp_path)


@pytest.fixture
def installation_cleanup_dependencies(installation_temp_path):
    yield
    created_folder_path = installation_temp_path.joinpath(DEPENDENCIES_FOLDER)
    with open(installation_temp_path.joinpath("moccasin.toml"), "w") as f:
        f.write(INSTALLATION_STARTING_TOML)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


@pytest.fixture
def installation_remove_dependencies(installation_temp_path):
    with open(installation_temp_path.joinpath("moccasin.toml"), "w") as f:
        f.write(INSTALLATION_NO_DEPENDENCIES_TOML)


@pytest.fixture
def installation_keep_pip_dependencies(installation_temp_path):
    with open(installation_temp_path.joinpath("moccasin.toml"), "w") as f:
        f.write(INSTALLATION_WITH_PIP_TOML)


@pytest.fixture
def installation_keep_gh_dependencies(installation_temp_path):
    with open(installation_temp_path.joinpath("moccasin.toml"), "w") as f:
        f.write(INSTALLATION_WITH_GH_TOML)


@pytest.fixture
def installation_keep_full_dependencies(installation_temp_path):
    with open(installation_temp_path.joinpath("moccasin.toml"), "w") as f:
        f.write(INSTALLATION_FULL_DEPENDENCIES_TOML)


# ------------------------------------------------------------------
#                         PURGE PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def purge_temp_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(PURGE_PROJECT_PATH, os.path.join(temp_dir), dirs_exist_ok=True)
        yield Path(temp_dir)


@pytest.fixture(scope="module")
def purge_project_config(purge_temp_path) -> Config:
    test_db_path = os.path.join(purge_temp_path, ".deployments.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    return _set_global_config(purge_temp_path)


@pytest.fixture
def purge_reset_dependencies(purge_temp_path):
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Copy the entire project directory to the temporary location
        shutil.copytree(
            purge_temp_path, temp_path / purge_temp_path.name, dirs_exist_ok=True
        )
        yield
        for item in (temp_path / purge_temp_path.name).iterdir():
            if item.is_dir():
                shutil.rmtree(purge_temp_path / item.name, ignore_errors=True)
                shutil.copytree(item, purge_temp_path / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, purge_temp_path / item.name)

        with open(purge_temp_path.joinpath("moccasin.toml"), "w") as f:
            f.write(PURGE_STARTING_TOML)


# ------------------------------------------------------------------
#                           NO CONFIG
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def no_config_temp_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(
            NO_CONFIG_PROJECT_PATH, os.path.join(temp_dir), dirs_exist_ok=True
        )
        yield Path(temp_dir)


@pytest.fixture(scope="module")
def no_config_config(no_config_temp_path) -> Config:
    test_db_path = os.path.join(no_config_temp_path, ".deployments.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    return _set_global_config(no_config_temp_path)


# ------------------------------------------------------------------
#                           TEST TEST
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def test_config_temp_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(
            TESTS_CONFIG_PROJECT_PATH, os.path.join(temp_dir), dirs_exist_ok=True
        )
        yield Path(temp_dir)


@pytest.fixture(scope="module")
def test_config_config(test_config_temp_path) -> Config:
    test_db_path = os.path.join(test_config_temp_path, ".deployments.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    return _set_global_config(test_config_temp_path)


# ------------------------------------------------------------------
#                             ANVIL
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def anvil_process():
    with AnvilProcess(args=["--load-state", str(ANVIL_STORED_STATE_PATH)]):
        yield


@pytest.fixture(scope="module")
def anvil(anvil_process, anvil_keystore):
    yield


@pytest.fixture(scope="module")
def anvil_two_no_state():
    with AnvilProcess(args=["-p", "8546"], port=8546):
        yield


# ------------------------------------------------------------------
#                         PYTEST HELPERS
# ------------------------------------------------------------------
NO_SKIP_OPTION: Final[str] = "--no-skip"


def pytest_addoption(parser):
    parser.addoption(
        NO_SKIP_OPTION,
        action="store_true",
        default=False,
        help="also run skipped tests",
    )


def pytest_collection_modifyitems(config, items: List[Any]):
    if config.getoption(NO_SKIP_OPTION):
        for test in items:
            test.own_markers = [
                marker
                for marker in test.own_markers
                if marker.name not in ("skip", "skipif")
            ]
