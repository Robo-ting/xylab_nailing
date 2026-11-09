# -*- coding: utf-8 -*-
"""
备份：demo_fixed 改造前的 MockDetector 版本
时间：2026-08-29
说明：按图片宽高比例生成模拟死节框，detection_mode 为 mock
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from PIL import Image


class Detector(ABC):
    @abstractmethod
    def detect(self, image: Image.Image) -> list[dict[str, Any]]:
        """返回原始图片像素坐标系下的缺陷列表。bbox 为 [x1, y1, x2, y2]。"""


class MockDetector(Detector):
    """按图像宽高生成模拟死节框。输出不得当作真实检测结果。"""

    def detect(self, image: Image.Image) -> list[dict[str, Any]]:
        w, h = image.size
        # 相对位置，随任意分辨率变化，坐标仍为原图 px
        boxes = [
            ("knot_001", 0.88, 0.22, 0.18, 0.14, 0.16),
            ("knot_002", 0.81, 0.58, 0.28, 0.12, 0.14),
        ]
        defects: list[dict[str, Any]] = []
        for i, (did, conf, rx, ry, rw, rh) in enumerate(boxes):
            x1 = int(w * rx)
            y1 = int(h * ry)
            x2 = int(w * (rx + rw))
            y2 = int(h * (ry + rh))
            x1, x2 = max(0, min(x1, x2)), min(w - 1, max(x1, x2))
            y1, y2 = max(0, min(y1, y2)), min(h - 1, max(y1, y2))
            if x2 - x1 < 8 or y2 - y1 < 8:
                continue
            defects.append(
                {
                    "id": did,
                    "type": "dead_knot",
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                }
            )
        if not defects:
            defects.append(
                {
                    "id": "knot_001",
                    "type": "dead_knot",
                    "confidence": 0.80,
                    "bbox": [int(w * 0.3), int(h * 0.3), int(w * 0.45), int(h * 0.48)],
                }
            )
        return defects


def get_detector() -> Detector:
    """当前返回 MockDetector。替换实现时只改这里。"""
    return MockDetector()
