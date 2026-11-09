# -*- coding: utf-8 -*-
"""图片像素坐标系下的规则钉位规划（与浏览器 KD-tree pipeline 隔离）。"""
from __future__ import annotations

from typing import Any


def plan_nails(
    image_width: int,
    image_height: int,
    defects: list[dict[str, Any]],
    edge_margin_px: float,
    knot_margin_px: float,
    nail_spacing_px: float,
    nailable_region: list[int] | None = None,
) -> dict[str, Any]:
    spacing = max(8.0, float(nail_spacing_px))
    edge = max(0.0, float(edge_margin_px))
    knot_m = max(0.0, float(knot_margin_px))

    forbidden: list[list[int]] = []
    for d in defects:
        if d.get("type") != "dead_knot":
            continue
        bbox = d.get("bbox") or []
        if len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [float(v) for v in bbox]
        fx1 = max(0, int(x1 - knot_m))
        fy1 = max(0, int(y1 - knot_m))
        fx2 = min(image_width, int(x2 + knot_m))
        fy2 = min(image_height, int(y2 + knot_m))
        forbidden.append([fx1, fy1, fx2, fy2])

    if nailable_region and len(nailable_region) == 4:
        nx1, ny1, nx2, ny2 = [int(v) for v in nailable_region]
        x_lo = max(0, nx1 + int(edge))
        x_hi = min(image_width, nx2 - int(edge))
        y_lo = max(0, ny1 + int(edge))
        y_hi = min(image_height, ny2 - int(edge))
    else:
        x_lo = int(edge)
        x_hi = image_width - int(edge)
        y_lo = int(edge)
        y_hi = image_height - int(edge)

    points: list[dict[str, Any]] = []
    nid = 1
    y = float(y_lo)
    while y <= y_hi:
        x = float(x_lo)
        while x <= x_hi:
            if not _inside_any(x, y, forbidden):
                points.append({"id": nid, "x": round(x, 1), "y": round(y, 1)})
                nid += 1
            x += spacing
        y += spacing

    return {"forbidden_regions": forbidden, "nail_points": points}


def _inside_any(x: float, y: float, regions: list[list[int]]) -> bool:
    for x1, y1, x2, y2 in regions:
        if x1 <= x <= x2 and y1 <= y <= y2:
            return True
    return False
