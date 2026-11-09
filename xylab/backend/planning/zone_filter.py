# -*- coding: utf-8 -*-
"""多边形区域筛选。整帧检测之后，丢掉采样点全部落在区域外的框。

规则与 SentinelVision pipeline._filter_by_zone 一致：脚底中心、头顶中心、
左右中点、框中心，任一在多边形内则保留。不足 3 个顶点时不筛选。
"""
from __future__ import annotations

from typing import Any

import numpy as np


def _cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("需要安装 opencv-python") from exc
    return cv2


def scale_polygon(
    zone: np.ndarray,
    src_w: int,
    src_h: int,
    dst_w: int,
    dst_h: int,
) -> np.ndarray:
    """按宽、高分别缩放顶点，并夹到目标画面内。"""
    if src_w <= 0 or src_h <= 0:
        return zone
    out = zone.astype(np.float32).copy()
    out[:, 0] *= dst_w / float(src_w)
    out[:, 1] *= dst_h / float(src_h)
    out[:, 0] = np.clip(out[:, 0], 0, max(0, dst_w - 1))
    out[:, 1] = np.clip(out[:, 1], 0, max(0, dst_h - 1))
    return out.round().astype(np.int32)


def _hits(bbox: list[float], zone: np.ndarray) -> bool:
    cv2 = _cv2()
    x1, y1, x2, y2 = [float(v) for v in bbox]
    samples = (
        ((x1 + x2) / 2.0, y2),
        ((x1 + x2) / 2.0, y1),
        (x1, (y1 + y2) / 2.0),
        (x2, (y1 + y2) / 2.0),
        ((x1 + x2) / 2.0, (y1 + y2) / 2.0),
    )
    contour = np.asarray(zone, dtype=np.float32).reshape(-1, 1, 2)
    for px, py in samples:
        if cv2.pointPolygonTest(contour, (float(px), float(py)), False) >= 0:
            return True
    return False


def filter_defects(
    defects: list[dict[str, Any]],
    zone: np.ndarray | None,
) -> tuple[list[dict[str, Any]], int]:
    """返回 (保留的缺陷, 丢掉的数量)。"""
    if zone is None or len(zone) < 3:
        return list(defects), 0
    kept: list[dict[str, Any]] = []
    dropped = 0
    for defect in defects:
        bbox = defect.get("bbox") or []
        if len(bbox) != 4 or _hits(bbox, zone):
            kept.append(defect)
        else:
            dropped += 1
    return kept, dropped
