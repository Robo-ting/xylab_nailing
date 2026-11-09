"""榉木选优机的目视分等标准。只写照片能核对的项目。"""
from __future__ import annotations

from typing import Any

SPECIES = "榉木"

# 国标等级名是特等、一等、二等、三等。本机对外仍用优选、一等、二等、等外。
MACHINE_GRADES = ("优选", "一等", "二等", "等外")

SCORE = {"优选": 92, "一等": 75, "二等": 55, "等外": 25}

STANDARD = """
树种按榉木，属于阔叶材。不要按针叶材、松木来判。
分等框架用 GB/T 4817《阔叶树锯材》的特等、一等、二等、三等。
选优机只输出四个名称，对应关系固定：
优选 = 特等，一等 = 一等，二等 = 二等，等外 = 三等或达不到三等。
取最差的一条，不能把差的缺陷平均成更好的等级。

检量只看画面里那块木板的宽材面，桌面、阴影、年轮、边皮不要当成缺陷。
红框是已经标出的缺陷。节子尺寸用它和材面宽度的比例来估计。
阔叶材的活节不降等。看起来明显不足 15 mm 的节子不计数。
照片里看不出的翘曲、斜纹、钝棱不要猜。

判定：
- 宽材面上没有可计数的缺陷：优选。
- 只有活节，没有死节、腐朽、裂纹、虫眼：一等。
- 有死节，但没有腐朽、贯通裂纹、也没有成片虫眼：二等。
- 有腐朽、贯通裂纹，或虫眼密集成片：等外。
""".strip()


def build_grade_prompt(packet: dict[str, Any]) -> str:
    lines = [
        STANDARD,
        "",
        f"板长 {packet.get('length_mm')} mm，板宽 {packet.get('width_mm')} mm。",
        "各钉位已经看到的缺陷：",
    ]
    stations = packet.get("stations") or []
    if not stations:
        lines.append("无钉位。")
    for station in stations:
        defects = station.get("defects") or []
        if not defects:
            lines.append(f"- {station.get('id')} @ {station.get('x_mm')} mm：这张照片没有检出缺陷")
            continue
        for defect in defects:
            lines.append(
                f"- {station.get('id')} @ {station.get('x_mm')} mm："
                f"{defect.get('type')} 置信度 {float(defect.get('confidence') or 0):.2f} "
                f"框 {defect.get('bbox')}"
            )
    lines.append("")
    lines.append("第一行只写一个等级：优选、一等、二等、等外。")
    lines.append("后面用不超过 80 个字说明看到了什么缺陷，以及它对照上面哪一条。")
    return "\n".join(lines)


def parse_grade(text: str) -> str | None:
    head = text.strip().splitlines()[0] if text.strip() else ""
    for grade in ("等外", "二等", "一等", "优选"):
        if grade in head:
            return grade
    return None
