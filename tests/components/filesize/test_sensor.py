"""The tests for the filesize sensor."""
import os
from unittest.mock import patch

import pytest

from homeassistant import config as hass_config
from homeassistant.components.filesize import DOMAIN
from homeassistant.components.filesize.sensor import CONF_FILE_PATHS
from homeassistant.const import SERVICE_RELOAD
from homeassistant.setup import async_setup_component

TEST_DIR = os.path.join(os.path.dirname(__file__))
TEST_FILE = os.path.join(TEST_DIR, "mock_file_test_filesize.txt")


def create_file(path):
    """Create a test file."""
    with open(path, "w") as test_file:
        test_file.write("test")


@pytest.fixture(autouse=True)
def remove_file():
    """Remove test file."""
    yield
    if os.path.isfile(TEST_FILE):
        os.remove(TEST_FILE)


async def test_invalid_path(hass):
    """Test that an invalid path is caught."""
    config = {"sensor": {"platform": "filesize", CONF_FILE_PATHS: ["invalid_path"]}}
    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids("sensor")) == 0


async def test_valid_path(hass):
    """Test for a valid path."""
    create_file(TEST_FILE)
    config = {"sensor": {"platform": "filesize", CONF_FILE_PATHS: [TEST_FILE]}}
    hass.config.allowlist_external_dirs = {TEST_DIR}
    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids("sensor")) == 1
    state = hass.states.get("sensor.mock_file_test_filesize_txt")
    assert state.state == "0.0"
    assert state.attributes.get("bytes") == 4


async def test_reload(hass, tmpdir):
    """Verify we can reload filesize sensors."""
    testfile = f"{tmpdir}/file"
    await hass.async_add_executor_job(create_file, testfile)
    with patch.object(hass.config, "is_allowed_path", return_value=True):
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": {
                    "platform": "filesize",
                    "file_paths": [testfile],
                }
            },
        )
        await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1

    assert hass.states.get("sensor.file")

    yaml_path = os.path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "filesize/configuration.yaml",
    )
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path), patch.object(
        hass.config, "is_allowed_path", return_value=True
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert hass.states.get("sensor.file") is None


def _get_fixtures_base_path():
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
