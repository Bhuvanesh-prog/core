"""Tests for Renault sensors."""
from unittest.mock import patch

import pytest
from renault_api.kamereon import exceptions

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.const import ATTR_ICON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from . import (
    check_device_registry,
    get_no_data_icon,
    setup_renault_integration_vehicle,
    setup_renault_integration_vehicle_with_no_data,
    setup_renault_integration_vehicle_with_side_effect,
)
from .const import DYNAMIC_ATTRIBUTES, FIXED_ATTRIBUTES, MOCK_VEHICLES

from tests.common import mock_device_registry, mock_registry


@pytest.mark.parametrize("vehicle_type", MOCK_VEHICLES.keys())
async def test_device_trackers(hass: HomeAssistant, vehicle_type: str):
    """Test for Renault device trackers."""

    entity_registry = mock_registry(hass)
    device_registry = mock_device_registry(hass)

    with patch("homeassistant.components.renault.PLATFORMS", [DEVICE_TRACKER_DOMAIN]):
        await setup_renault_integration_vehicle(hass, vehicle_type)
        await hass.async_block_till_done()

    mock_vehicle = MOCK_VEHICLES[vehicle_type]
    check_device_registry(device_registry, mock_vehicle["expected_device"])

    expected_entities = mock_vehicle[DEVICE_TRACKER_DOMAIN]
    assert len(entity_registry.entities) == len(expected_entities)
    for expected_entity in expected_entities:
        entity_id = expected_entity["entity_id"]
        registry_entry = entity_registry.entities.get(entity_id)
        assert registry_entry is not None
        assert registry_entry.unique_id == expected_entity["unique_id"]
        state = hass.states.get(entity_id)
        assert state.state == expected_entity["result"]
        for attr in FIXED_ATTRIBUTES + DYNAMIC_ATTRIBUTES:
            assert state.attributes.get(attr) == expected_entity.get(attr)


@pytest.mark.parametrize("vehicle_type", MOCK_VEHICLES.keys())
async def test_device_tracker_empty(hass: HomeAssistant, vehicle_type: str):
    """Test for Renault device trackers with empty data from Renault."""

    entity_registry = mock_registry(hass)
    device_registry = mock_device_registry(hass)

    with patch("homeassistant.components.renault.PLATFORMS", [DEVICE_TRACKER_DOMAIN]):
        await setup_renault_integration_vehicle_with_no_data(hass, vehicle_type)
        await hass.async_block_till_done()

    mock_vehicle = MOCK_VEHICLES[vehicle_type]
    check_device_registry(device_registry, mock_vehicle["expected_device"])

    expected_entities = mock_vehicle[DEVICE_TRACKER_DOMAIN]
    assert len(entity_registry.entities) == len(expected_entities)
    for expected_entity in expected_entities:
        entity_id = expected_entity["entity_id"]
        registry_entry = entity_registry.entities.get(entity_id)
        assert registry_entry is not None
        assert registry_entry.unique_id == expected_entity["unique_id"]
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNKNOWN
        for attr in FIXED_ATTRIBUTES:
            assert state.attributes.get(attr) == expected_entity.get(attr)
        # Check dynamic attributes:
        assert state.attributes.get(ATTR_ICON) == get_no_data_icon(expected_entity)


@pytest.mark.parametrize("vehicle_type", MOCK_VEHICLES.keys())
async def test_device_tracker_errors(hass: HomeAssistant, vehicle_type: str):
    """Test for Renault device trackers with temporary failure."""

    entity_registry = mock_registry(hass)
    device_registry = mock_device_registry(hass)

    invalid_upstream_exception = exceptions.InvalidUpstreamException(
        "err.tech.500",
        "Invalid response from the upstream server (The request sent to the GDC is erroneous) ; 502 Bad Gateway",
    )

    with patch("homeassistant.components.renault.PLATFORMS", [DEVICE_TRACKER_DOMAIN]):
        await setup_renault_integration_vehicle_with_side_effect(
            hass, vehicle_type, invalid_upstream_exception
        )
        await hass.async_block_till_done()

    mock_vehicle = MOCK_VEHICLES[vehicle_type]
    check_device_registry(device_registry, mock_vehicle["expected_device"])

    expected_entities = mock_vehicle[DEVICE_TRACKER_DOMAIN]
    assert len(entity_registry.entities) == len(expected_entities)
    for expected_entity in expected_entities:
        entity_id = expected_entity["entity_id"]
        registry_entry = entity_registry.entities.get(entity_id)
        assert registry_entry is not None
        assert registry_entry.unique_id == expected_entity["unique_id"]
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE
        for attr in FIXED_ATTRIBUTES:
            assert state.attributes.get(attr) == expected_entity.get(attr)
        # Check dynamic attributes:
        assert state.attributes.get(ATTR_ICON) == get_no_data_icon(expected_entity)


async def test_device_tracker_access_denied(hass: HomeAssistant):
    """Test for Renault device trackers with access denied failure."""

    entity_registry = mock_registry(hass)
    device_registry = mock_device_registry(hass)

    vehicle_type = "zoe_40"
    access_denied_exception = exceptions.AccessDeniedException(
        "err.func.403",
        "Access is denied for this resource",
    )

    with patch("homeassistant.components.renault.PLATFORMS", [DEVICE_TRACKER_DOMAIN]):
        await setup_renault_integration_vehicle_with_side_effect(
            hass, vehicle_type, access_denied_exception
        )
        await hass.async_block_till_done()

    mock_vehicle = MOCK_VEHICLES[vehicle_type]
    check_device_registry(device_registry, mock_vehicle["expected_device"])

    assert len(entity_registry.entities) == 0


async def test_device_tracker_not_supported(hass: HomeAssistant):
    """Test for Renault device trackers with not supported failure."""

    entity_registry = mock_registry(hass)
    device_registry = mock_device_registry(hass)

    vehicle_type = "zoe_40"
    not_supported_exception = exceptions.NotSupportedException(
        "err.tech.501",
        "This feature is not technically supported by this gateway",
    )

    with patch("homeassistant.components.renault.PLATFORMS", [DEVICE_TRACKER_DOMAIN]):
        await setup_renault_integration_vehicle_with_side_effect(
            hass, vehicle_type, not_supported_exception
        )
        await hass.async_block_till_done()

    mock_vehicle = MOCK_VEHICLES[vehicle_type]
    check_device_registry(device_registry, mock_vehicle["expected_device"])

    assert len(entity_registry.entities) == 0
