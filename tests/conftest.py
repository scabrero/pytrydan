from pathlib import Path
from typing import Any

import orjson
import respx
from httpx import Response

from pytrydan import Trydan
from pytrydan.const import KEYWORDS


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    with open(_fixtures_dir() / name) as read_in:
        return read_in.read()


def _load_json_fixture(case_endpoint: str) -> dict[str, Any]:
    return orjson.loads(_load_fixture(case_endpoint))


def _mock_missing_realtime_keyword_reads(
    data: dict[str, Any], values: dict[str, Any] | None = None
) -> None:
    """Mock read endpoints for keywords missing from RealTimeData."""
    keyword_values = {
        "ChargeMode": 2,
        "LightLED": 75,
        "LogoLED": 25,
        "VoltageInstallation": 230,
    }
    if values is not None:
        keyword_values.update(values)

    for keyword in KEYWORDS.difference(data):
        value = keyword_values[keyword]
        respx.get(f"/read/{keyword}").mock(return_value=Response(200, text=str(value)))


async def _get_mock_trydan(update: bool = True):  # type: ignore[no-untyped-def]
    """Return a mock Trydan."""
    trydan = Trydan("127.0.0.1")
    return trydan
