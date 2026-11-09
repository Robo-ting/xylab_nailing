"""把缺陷图和提示词交给 Qwen-VL，请它说明最近的合规钉位。"""
from __future__ import annotations

import base64
import json
import os
import urllib.request
from typing import Any

DEFAULT_PROMPT = (
    "图中的红框是已经识别出的缺陷。请根据这些框和下面的规则，"
    "说明离当前钉位最近、仍然符合规范的可钉位置该怎么选。"
    "只讲选择逻辑，不要把红框以外的东西当成缺陷。"
    "规则：死节、裂缝、腐朽及其外扩范围不能落钉；"
    "钉位只能落在给定间距的整数倍上；"
    "若当前位置落在禁区内，沿板长选择最近的一格，并说明为什么选这一侧。"
)


def build_prompt(
    station: dict[str, Any],
    spacing_mm: float | None,
    user_prompt: str,
    length_mm: float | None = None,
    image_size: tuple[int, int] | None = None,
) -> str:
    defects = station.get("defects") or []
    x_mm = float(station.get("x_mm") or 0)
    lines = [
        f"当前钉位 {station.get('id')} 位于板长 {x_mm:g} mm。",
        f"钉位间距 {spacing_mm:g} mm。" if spacing_mm else "钉位间距未提供。",
        "已识别缺陷（红框，坐标为照片像素 [x, y, 宽, 高]）：",
    ]
    if not defects:
        lines.append("无。")
    for defect in defects:
        bbox = defect.get("bbox") or []
        lines.append(
            f"- {defect.get('type')} 置信度 {float(defect.get('confidence') or 0):.2f} 框 {bbox}"
        )
    if image_size and length_mm and length_mm > 0:
        width, height = image_size
        pixel_x = x_mm / float(length_mm) * width
        lines.append(
            f"照片尺寸 {width}×{height} 像素。板长 {length_mm:g} mm 按照片宽度线性对应，"
            f"当前钉位大约在照片横向 x={pixel_x:.0f}。"
        )
    lines.append(
        "框里的数字全是像素，不是毫米。先换算再和红框比较。"
        "当前像素若落在红框内，或离红框边缘不足 20 像素，当前位置就不合规，不能把它再写成推荐位置。"
        "推荐位置必须是间距的整数倍，并且换算回像素后要离开红框及其 20 像素外扩。说明选左还是选右。"
    )
    lines.append("")
    lines.append(user_prompt.strip() or DEFAULT_PROMPT)
    return "\n".join(lines)


def ask_qwen(image_bytes: bytes, prompt: str) -> str:
    url = os.environ.get("QWEN_VL_URL", "http://127.0.0.1:8011/analyze")
    payload = json.dumps(
        {
            "image_base64": base64.b64encode(image_bytes).decode("ascii"),
            "prompt": prompt,
        }
    ).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        raise RuntimeError(f"视觉模型没有返回结果: {exc}") from exc
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("视觉模型返回为空")
    return text.strip()
