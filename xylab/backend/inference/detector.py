# -*- coding: utf-8 -*-
"""缺陷检测接口。Demo 阶段为固定人工标注，非自动识别。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from PIL import Image

DEMO_IMAGE_SIZE = (1024, 768)

# 参考图 1024×768 木板可钉区域，原图像素 [x1, y1, x2, y2]
DEMO_NAILABLE_REGION = [109, 280, 877, 530]

# 参考图 1024×768 人工预标注节疤，原图像素 [x1, y1, x2, y2]
DEMO_FIXED_DEFECTS: list[dict[str, Any]] = [
    {
        "id": "knot_001",
        "type": "dead_knot",
        "confidence": 0.88,
        "bbox": [515, 395, 570, 445],
    },
    {
        "id": "knot_002",
        "type": "dead_knot",
        "confidence": 0.81,
        "bbox": [570, 420, 630, 485],
    },
]


def _demo_scale(size: tuple[int, int]) -> tuple[float, float] | None:
    """按参考图宽高独立缩放，适配同木板不同裁切比例。"""
    w, h = size
    ref_w, ref_h = DEMO_IMAGE_SIZE
    if w <= 0 or h <= 0:
        return None
    return w / ref_w, h / ref_h


def get_demo_plan_scale(size: tuple[int, int]) -> float | None:
    """规划边距/钉距随分辨率等比放大，避免大图钉位过密。"""
    scale = _demo_scale(size)
    if scale is None:
        return None
    sx, sy = scale
    return (sx + sy) / 2.0


def _scale_xyxy(box: list[int], sx: float, sy: float) -> list[int]:
    x1, y1, x2, y2 = box
    return [int(round(x1 * sx)), int(round(y1 * sy)), int(round(x2 * sx)), int(round(y2 * sy))]


def get_demo_nailable_region(size: tuple[int, int]) -> list[int] | None:
    scale = _demo_scale(size)
    if scale is None:
        return None
    sx, sy = scale
    return _scale_xyxy(DEMO_NAILABLE_REGION, sx, sy)


def get_demo_defects(size: tuple[int, int]) -> list[dict[str, Any]]:
    scale = _demo_scale(size)
    if scale is None:
        return []
    sx, sy = scale
    out: list[dict[str, Any]] = []
    for d in DEMO_FIXED_DEFECTS:
        out.append(
            {
                "id": d["id"],
                "type": d["type"],
                "confidence": d["confidence"],
                "bbox": _scale_xyxy(d["bbox"], sx, sy),
            }
        )
    return out


class Detector(ABC):
    detection_mode: str = "mock"

    @abstractmethod
    def detect(self, image: Image.Image) -> list[dict[str, Any]]:
        """返回原始图片像素坐标系下的缺陷列表。bbox 为 [x1, y1, x2, y2]。"""


class DemoFixedDetector(Detector):
    """固定木板图人工标注；同比例大图按参考分辨率等比映射。"""

    detection_mode = "demo_fixed"

    def detect(self, image: Image.Image) -> list[dict[str, Any]]:
        return get_demo_defects(image.size)


def get_detector() -> Detector:
    return DemoFixedDetector()
