import pytest
import respx
from httpx import Response

from pytrydan.const import KEYWORDS
from pytrydan.exceptions import (
    ChargeStateInvalid,
    TrydanCommunicationError,
    TrydanInvalidResponse,
)
from pytrydan.models.trydan import ChargeMode, ChargeState, TrydanData

from .conftest import (
    _get_mock_trydan,
    _load_json_fixture,
    _mock_missing_realtime_keyword_reads,
)


@pytest.mark.asyncio
@respx.mock
async def test_bad_status():
    respx.get("/RealTimeData").mock(return_value=Response(404, json={}))

    envoy = await _get_mock_trydan()
    with pytest.raises(TrydanInvalidResponse):
        data = await envoy.get_data()
        assert data is None

    respx.get("/RealTimeData").mock(return_value=Response(403, json={}))

    envoy = await _get_mock_trydan()
    with pytest.raises(TrydanCommunicationError):
        data = await envoy.get_data()
        assert data is None


@pytest.mark.asyncio
@respx.mock
async def test_status():
    realtime_data = _load_json_fixture("RealTimeData")
    respx.get("/RealTimeData").mock(return_value=Response(200, json=realtime_data))
    _mock_missing_realtime_keyword_reads(realtime_data)

    envoy = await _get_mock_trydan()
    data = await envoy.get_data()
    assert data is not None

    assert data.charge_state == 1
    assert data.ready_state == 1
    assert data.charge_power == 0
    assert data.charge_energy == 7.6
    assert data.slave_error == 0
    assert data.charge_time == 9979
    assert data.house_power == 0
    assert data.fv_power == 0
    assert data.paused == 0
    assert data.locked == 0
    assert data.timer == 1
    assert data.intensity == 16
    assert data.dynamic == 0
    assert data.min_intensity == 6
    assert data.max_intensity == 16
    assert data.pause_dynamic == 0
    assert data.voltage_installation == 230
    assert data.charge_mode == 2
    assert data.light_led == 75
    assert data.logo_led == 25
    assert data.firmware_version == "1.6.18"
    assert data.dynamic_power_mode == 2
    assert data.contracted_power == 4600


@pytest.mark.asyncio
@respx.mock
async def test_status_charging():
    realtime_data = _load_json_fixture("RealTimeData_Charging")
    respx.get("/RealTimeData").mock(return_value=Response(200, json=realtime_data))
    _mock_missing_realtime_keyword_reads(realtime_data)

    envoy = await _get_mock_trydan()
    data = await envoy.get_data()
    assert data is not None

    assert data.charge_state == 2
    assert data.ready_state == 0
    assert data.charge_power == 2664
    assert data.charge_energy == 0.07
    assert data.slave_error == 0
    assert data.charge_time == 105
    assert data.house_power == 0
    assert data.fv_power == 0
    assert data.paused == 0
    assert data.locked == 0
    assert data.timer == 1
    assert data.intensity == 12
    assert data.dynamic == 0
    assert data.min_intensity == 6
    assert data.max_intensity == 16
    assert data.pause_dynamic == 0
    assert data.voltage_installation == 230
    assert data.charge_mode == 2
    assert data.light_led == 75
    assert data.logo_led == 25
    assert data.firmware_version == "1.6.18"
    assert data.dynamic_power_mode == 2
    assert data.contracted_power == 4600


@pytest.mark.asyncio
@respx.mock
async def test_status_reads_missing_realtime_data_keywords():
    realtime_data = _load_json_fixture("RealTimeData")
    respx.get("/RealTimeData").mock(return_value=Response(200, json=realtime_data))
    _mock_missing_realtime_keyword_reads(
        realtime_data,
        {
            "ChargeMode": 1,
            "LightLED": 0,
            "LogoLED": 100,
            "VoltageInstallation": 240,
        },
    )

    envoy = await _get_mock_trydan()
    data = await envoy.get_data()

    assert data.charge_mode == ChargeMode.THREEPHASIC
    assert data.light_led == 0
    assert data.logo_led == 100
    assert data.voltage_installation == 240


@pytest.mark.asyncio
@respx.mock
async def test_status_ignores_unavailable_realtime_data_keywords():
    realtime_data = _load_json_fixture("RealTimeData")
    respx.get("/RealTimeData").mock(return_value=Response(200, json=realtime_data))
    for keyword in KEYWORDS.difference(realtime_data):
        respx.get(f"/read/{keyword}").mock(return_value=Response(404, json={}))

    envoy = await _get_mock_trydan()
    data = await envoy.get_data()

    assert data.charge_mode is None
    assert data.light_led is None
    assert data.logo_led is None
    assert data.voltage_installation is None


def test_charge_state_vendor_values():
    data = _load_json_fixture("RealTimeData")

    assert (
        TrydanData.from_api({**data, "ChargeState": 0}).charge_state
        == ChargeState.NOT_CONNECTED
    )
    assert (
        TrydanData.from_api({**data, "ChargeState": 1}).charge_state
        == ChargeState.CONNECTED_NOT_CHARGING
    )
    assert (
        TrydanData.from_api({**data, "ChargeState": 2}).charge_state
        == ChargeState.CONNECTED_CHARGING
    )
    with pytest.raises(ChargeStateInvalid):
        TrydanData.from_api({**data, "ChargeState": 3})
    assert (
        TrydanData.from_api({**data, "ChargeState": 4}).charge_state
        == ChargeState.SYSTEM_FAILURE_OR_LEAK_DETECTED
    )
    assert ChargeState.PILOT_SHORT == ChargeState.SYSTEM_FAILURE_OR_LEAK_DETECTED
    assert (
        TrydanData.from_api({**data, "ChargeState": 5}).charge_state
        == ChargeState.CONTROL_PILOT_OR_GROUND_FAILURE
    )
    assert ChargeState.GENERAL_FAULT == ChargeState.CONTROL_PILOT_OR_GROUND_FAILURE
    assert (
        TrydanData.from_api({**data, "ChargeState": 6}).charge_state
        == ChargeState.VENTILATION_REQUIRED
    )
    assert ChargeState.VENTILATION == ChargeState.VENTILATION_REQUIRED


def test_charge_mode_when_available():
    data = _load_json_fixture("RealTimeData")

    assert (
        TrydanData.from_api({**data, "ChargeMode": 0}).charge_mode
        == ChargeMode.MONOPHASIC
    )
    assert (
        TrydanData.from_api({**data, "ChargeMode": 1}).charge_mode
        == ChargeMode.THREEPHASIC
    )
    assert (
        TrydanData.from_api({**data, "ChargeMode": 2}).charge_mode == ChargeMode.MIXED
    )


def test_charge_mode_when_absent():
    data = _load_json_fixture("RealTimeData")

    assert TrydanData.from_api(data).charge_mode is None


def test_led_values_when_available():
    data = _load_json_fixture("RealTimeData")
    trydan_data = TrydanData.from_api({**data, "LightLED": 75, "LogoLED": 25})

    assert trydan_data.light_led == 75
    assert trydan_data.logo_led == 25


def test_led_values_when_absent():
    data = _load_json_fixture("RealTimeData")
    trydan_data = TrydanData.from_api(data)

    assert trydan_data.light_led is None
    assert trydan_data.logo_led is None
