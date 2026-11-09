"""选优机定级接口。

选优机按整板缺陷把板分成 优选、一等、二等、等外。
这里先用可替换的规则兜底；设置 INTAKE_AI_URL 后，同一份数据包交给外部 AI，AI 无响应再退回规则。
"""
from __future__ import annotations

import os
from typing import Any


GRADES = ("优选", "一等", "二等", "等外")


def _nearest_station(x_mm: float, stations: list[dict[str, Any]]) -> tuple[float, dict[str, Any] | None]:
    best = 1e12
    hit = None
    for station in stations:
        dist = abs(float(station["x_mm"]) - x_mm)
        if dist < best:
            best = dist
            hit = station
    return best, hit


def rule_grade(packet: dict[str, Any]) -> dict[str, Any]:
    """选优机规则兜底，不调用模型。"""
    stations = packet.get("stations") or []
    ir_hits = packet.get("ir") or []
    reasons: list[str] = []
    if not stations:
        return _result("等外", 0, ["没有钉位，选优机无法定级"], "rule")

    severe = False
    for hit in ir_hits:
        dist, station = _nearest_station(float(hit.get("x_mm") or 0), stations)
        if dist <= 40:
            severe = True
            label = station["id"] if station else "钉位"
            reasons.append(f"红外缺陷距{label} {dist:.0f} mm")

    saw_dead = False
    saw_mild = False
    for station in stations:
        kinds = {str(d.get("type")) for d in station.get("defects") or []}
        if kinds & {"decay", "crack", "knot_dead"}:
            saw_dead = True
            reasons.append(f"{station['id']} 照片见到 " + "、".join(sorted(kinds)))
        elif kinds & {"knot_live", "wormhole", "nail_exposed", "nail_rusted"}:
            saw_mild = True
            reasons.append(f"{station['id']} 照片见到 " + "、".join(sorted(kinds)))

    if severe:
        grade, score = "等外", 25
    elif saw_dead:
        grade, score = "二等", 55
    elif saw_mild or ir_hits:
        grade, score = "一等", 75
    else:
        grade, score = "优选", 92
        reasons.append("钉位照片和红外都没有压到缺陷")
    return _result(grade, score, reasons, "rule")


def try_ai_grade(packet: dict[str, Any]) -> dict[str, Any] | None:
    """外部 AI。未配置地址时返回 None，由规则兜底。"""
    url = os.environ.get("INTAKE_AI_URL", "").strip()
    if not url:
        return None
    import json
    import urllib.request

    body = json.dumps({"task": "board_grade", "reference": "选优机", "packet": packet}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode())
    if not isinstance(data, dict) or data.get("grade") not in GRADES:
        raise RuntimeError("AI 定级结果缺少 grade")
    return _result(str(data["grade"]), int(data.get("score") or 0), list(data.get("reasons") or []), "ai")


def ir_block_reasons(packet: dict[str, Any]) -> list[str]:
    """红外缺陷贴着钉位时，照片等级不能高于等外。"""
    stations = packet.get("stations") or []
    reasons: list[str] = []
    for hit in packet.get("ir") or []:
        dist, station = _nearest_station(float(hit.get("x_mm") or 0), stations)
        if dist <= 40:
            label = station["id"] if station else "钉位"
            reasons.append(f"红外缺陷距{label} {dist:.0f} mm")
    return reasons


def visual_grade(packet: dict[str, Any], image_bytes: bytes) -> dict[str, Any]:
    """把缺陷图和榉木分等标准交给视觉模型。"""
    from intake.advisor import ask_qwen
    from intake.grade_standard import SCORE, build_grade_prompt, parse_grade

    text = ask_qwen(image_bytes, build_grade_prompt(packet))
    grade = parse_grade(text)
    if grade is None:
        raise RuntimeError("模型没有给出优选、一等、二等、等外中的一个")
    reasons = [text]
    blocked = ir_block_reasons(packet)
    if blocked and grade != "等外":
        grade = "等外"
        reasons.extend(blocked)
        reasons.append("红外缺陷贴着钉位，照片等级降为等外")
    result = _result(grade, SCORE[grade], reasons, "qwen")
    result["reference"] = "榉木 · GB/T 4817"
    return result


def grade_board(packet: dict[str, Any]) -> dict[str, Any]:
    try:
        ai = try_ai_grade(packet)
    except Exception as exc:
        fallback = rule_grade(packet)
        fallback["ai_error"] = str(exc)
        return fallback
    if ai is not None:
        return ai
    return rule_grade(packet)


def _result(grade: str, score: int, reasons: list[str], grader: str) -> dict[str, Any]:
    return {
        "grade": grade,
        "score": max(0, min(100, score)),
        "reasons": reasons,
        "grader": grader,
        "reference": "选优机",
    }
