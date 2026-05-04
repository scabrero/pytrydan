import pytest
import respx
from httpx import Response

from pytrydan import ChargeMode, TrydanInvalidValue

from .conftest import _get_mock_trydan, _load_json_fixture


@pytest.mark.asyncio
@respx.mock
async def test_binary_sensors():
    respx.get("/RealTimeData").mock(
        return_value=Response(200, json=_load_json_fixture("RealTimeData"))
    )

    envoy = await _get_mock_trydan()

    envoy_data = await envoy.get_data()

    assert envoy_data is not None

    assert envoy.firmware_version == "1.6.18"

    assert envoy.connected is True
    assert envoy.charging is False
    assert envoy.ready is True

    respx.get("/write/Paused=1").mock(return_value=Response(200, text="OK"))
    assert await envoy.pause() is None

    respx.get("/write/Paused=0").mock(return_value=Response(200, text="OK"))
    assert await envoy.resume() is None

    respx.get("/write/Intensity=10").mock(return_value=Response(200, text="OK"))
    assert await envoy.intensity(10) is None

    with pytest.raises(TrydanInvalidValue) as e_info:
        await envoy.intensity(100)
    assert "Intensity must be between 6 and 32" == str(e_info.value)

    respx.get("/write/VoltageInstallation=230").mock(
        return_value=Response(200, text="OK")
    )
    assert await envoy.voltage_installation(230) is None

    with pytest.raises(TrydanInvalidValue) as e_info:
        await envoy.voltage_installation(0)
    assert "Installation Voltage must be positive" == str(e_info.value)

    respx.get("/write/ChargeMode=2").mock(return_value=Response(200, text="OK"))
    assert await envoy.charge_mode(ChargeMode.MIXED) is None

    with pytest.raises(TrydanInvalidValue) as e_info:
        await envoy.set_keyword("ChargeMode", 3)
    assert "Value 3 is not valid for keyword ChargeMode" == str(e_info.value)
