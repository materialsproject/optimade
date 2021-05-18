# pylint: disable=protected-access,pointless-statement,relative-beyond-top-level
import json
import os

from pathlib import Path


def test_env_variable():
    """Set OPTIMADE_DEBUG environment variable and check CONFIG picks up on it correctly"""
    from optimade.server.config import ServerConfig

    org_env_var = os.getenv("OPTIMADE_DEBUG")

    try:
        os.environ["OPTIMADE_DEBUG"] = "true"
        CONFIG = ServerConfig()
        assert CONFIG.debug

        os.environ.pop("OPTIMADE_DEBUG", None)
        CONFIG = ServerConfig()
        assert not CONFIG.debug
    finally:
        if org_env_var is not None:
            os.environ["OPTIMADE_DEBUG"] = org_env_var
        else:
            assert os.getenv("OPTIMADE_DEBUG") is None


def test_default_config_path(top_dir):
    """Make sure the default config path works
    Expected default config path: PATH/TO/USER/HOMEDIR/.optimade.json
    """
    from optimade.server.config import ServerConfig

    org_env_var = os.getenv("OPTIMADE_CONFIG_FILE")

    with open(top_dir.joinpath("tests/test_config.json"), "r") as config_file:
        config = json.load(config_file)

    different_base_url = "http://something_you_will_never_think_of.com"
    config["base_url"] = different_base_url

    # Try-finally to make sure we don't overwrite possible existing `.optimade.json`.
    # As well as restoring OPTIMADE_CONFIG_FILE environment variable
    default_config_file = Path.home().joinpath(".optimade.json")
    restore = False
    CONFIG = None
    if default_config_file.exists():
        restore = True
        with open(default_config_file, "rb") as original_file:
            original_file_content = original_file.read()
    try:
        # Unset OPTIMADE_CONFIG_FILE environment variable
        os.environ.pop("OPTIMADE_CONFIG_FILE", None)
        assert os.getenv("OPTIMADE_CONFIG_FILE") is None

        with open(default_config_file, "w") as default_file:
            json.dump(config, default_file)
        CONFIG = ServerConfig()
        assert CONFIG.base_url == different_base_url, (
            f"\nDumped file content:\n{config}.\n\nLoaded CONFIG:\n{CONFIG}",
        )
    finally:
        if CONFIG is not None:
            del CONFIG

        if restore:
            with open(default_config_file, "wb") as original_file:
                original_file.write(original_file_content)
        elif default_config_file.exists():
            os.remove(default_config_file)

        if org_env_var is None:
            assert os.getenv("OPTIMADE_CONFIG_FILE") is None
        else:
            os.environ["OPTIMADE_CONFIG_FILE"] = org_env_var


def test_debug_is_respected_when_off(both_clients):
    """Make sure traceback is toggleable according to debug mode - here OFF

    TODO: This should be moved to a separate test file that tests the exception handlers.
    """
    from optimade.server.config import CONFIG

    org_value = CONFIG.debug

    try:
        if CONFIG.debug:
            CONFIG.debug = False

        response = both_clients.get("/non/existent/path")
        assert (
            response.status_code == 404
        ), f"Request should have failed, but didn't: {response.json()}"

        response = response.json()
        assert "data" not in response
        assert "meta" in response

        assert f"_{CONFIG.provider.prefix}_traceback" not in response["meta"]
    finally:
        CONFIG.debug = org_value


def test_debug_is_respected_when_on(both_clients):
    """Make sure traceback is toggleable according to debug mode - here ON

    TODO: This should be moved to a separate test file that tests the exception handlers.
    """
    from optimade.server.config import CONFIG

    org_value = CONFIG.debug

    try:
        CONFIG.debug = True

        response = both_clients.get("/non/existent/path")
        assert (
            response.status_code == 404
        ), f"Request should have failed, but didn't: {response.json()}"

        response = response.json()
        assert "data" not in response
        assert "meta" in response

        assert f"_{CONFIG.provider.prefix}_traceback" in response["meta"]
    finally:
        CONFIG.debug = org_value


def test_yaml_config_file():
    """Test loading a YAML config file

    First, pass a correctly formatted YAML file that only includes a single YAML document.
    Secondly, pass a correctly formatted YAML file that includes two YAML docuements.

    Expectation: The second test should fail to load with a warning, loading the default settings
    instead. The first test should be fine.

    NOTE: Since pytest loads a JSON config file, there's no need to test that further.
    """
    import tempfile
    import pytest
    from optimade.server.config import ServerConfig

    yaml_content = """
---
aliases:
  references:
    last_modified: mtime
debug: true
provider_fields:
  references:
  - great_paper
...
"""
    extra_yaml_content = """
---
debug: true
...
"""
    org_env_var = os.getenv("OPTIMADE_CONFIG_FILE")

    try:
        with tempfile.NamedTemporaryFile("w+t", suffix=".yml") as config_file:
            config_file.write(yaml_content)
            config_file.seek(0, 0)  # Go to start of file

            os.environ["OPTIMADE_CONFIG_FILE"] = str(Path(config_file.name).resolve())
            CONFIG = ServerConfig()

        assert CONFIG.aliases == {
            "references": {"last_modified": "mtime"}
        }, f"Config: {CONFIG.aliases}"
        assert CONFIG.debug, f"Config: {CONFIG.debug}"
        assert CONFIG.provider_fields == {
            "references": ["great_paper"]
        }, f"Config: {CONFIG.provider_fields}"

        with tempfile.NamedTemporaryFile("w+t", suffix=".yml") as config_file:
            config_file.write(yaml_content + extra_yaml_content)
            config_file.seek(0, 0)  # Go to start of file

            os.environ["OPTIMADE_CONFIG_FILE"] = str(Path(config_file.name).resolve())
            with pytest.warns(UserWarning, match=r"^Unable to parse config file.*"):
                CONFIG = ServerConfig()

        assert CONFIG.aliases == {}, f"Config: {CONFIG.aliases}"
        assert not CONFIG.debug, f"Config: {CONFIG.debug}"
        assert CONFIG.provider_fields == {}, f"Config: {CONFIG.provider_fields}"

    finally:
        if org_env_var is not None:
            os.environ["OPTIMADE_CONFIG_FILE"] = org_env_var
        else:
            assert os.getenv("OPTIMADE_CONFIG_FILE") is None
