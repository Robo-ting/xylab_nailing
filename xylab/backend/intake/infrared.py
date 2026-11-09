"""红外探伤接口。没有硬件时走桩，返回沿板长的内部缺陷位置。"""
from __future__ import annotations

import os
from typing import Any, Protocol


class InfraredPort(Protocol):
    """以后换成真实红外探伤仪：输入板长和钉位，输出缺陷的板面坐标。"""

    def scan(self, length_mm: float, stations: list[dict[str, Any]], simulate: bool) -> list[dict[str, Any]]:
        ...


class StubInfrared:
    """无设备时的接口桩。simulate 为真时在板长 40% 处给一处内部空洞，便于把链路跑通。"""

    mode = "stub"

    def scan(self, length_mm: float, stations: list[dict[str, Any]], simulate: bool) -> list[dict[str, Any]]:
        if not simulate or length_mm <= 0:
            return []
        return [
            {
                "id": "ir-1",
                "x_mm": round(length_mm * 0.4, 1),
                "y_mm": 0.0,
                "kind": "internal_void",
                "confidence": 0.62,
                "note": "桩数据：内部空洞。接入探伤仪后由设备坐标替换。",
            }
        ]


class HttpInfrared:
    """INTAKE_IR_URL 指向探伤仪网关时使用。约定 POST JSON，返回 hits 列表。"""

    mode = "hardware"

    def __init__(self, url: str):
        self.url = url

    def scan(self, length_mm: float, stations: list[dict[str, Any]], simulate: bool) -> list[dict[str, Any]]:
        import json
        import urllib.request

        body = json.dumps(
            {"length_mm": length_mm, "stations": [{"id": s["id"], "x_mm": s["x_mm"]} for s in stations], "simulate": simulate}
        ).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        hits = data.get("hits") if isinstance(data, dict) else None
        if not isinstance(hits, list):
            raise RuntimeError("红外接口没有返回 hits")
        return hits


def get_infrared() -> InfraredPort:
    url = os.environ.get("INTAKE_IR_URL", "").strip()
    if url:
        return HttpInfrared(url)
    return StubInfrared()
