# -*- coding: utf-8 -*-
"""Probe mermaid.ink rendering for Chinese labels; isolate which part triggers HTTP 400."""
import base64
import sys
import zlib
import json
from pathlib import Path

import requests
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

DOCS = Path(r"D:\论文\机械臂大论文\docs")

SIMPLE_ASCII = "graph LR\nA[test]-->B[ok]"
SIMPLE_CN = "graph LR\nA[构件上料]-->B[采集信息]"
FULL_CN = """flowchart LR
    A[构件上料到位]
    B[采集板面环境信息]
    D{成像条件<br/>是否满足判定}
    E[建立缺陷避让范围]
    K[生成待复核事件]
    A --> B --> D
    D -->|满足| E
    D -->|不满足| K
"""


def b64(graph: str) -> str:
    return base64.urlsafe_b64encode(graph.encode("utf-8")).decode("ascii")


def pako(graph: str) -> str:
    payload = json.dumps({"code": graph, "mermaid": {"theme": "default"}}).encode("utf-8")
    comp = zlib.compressobj(9, zlib.DEFLATED, 15)
    data = comp.compress(payload) + comp.flush()
    return "pako:" + base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def probe(label: str, path: str, save: str | None = None):
    url = f"https://mermaid.ink/img/{path}"
    try:
        r = requests.get(url, timeout=60)
    except Exception as e:
        print(f"{label:34s} EXC  {type(e).__name__} {str(e)[:80]}")
        return
    info = f"{label:34s} {r.status_code}  {len(r.content):>7d}B  {r.headers.get('content-type')}"
    if r.status_code != 200:
        info += f"  body={r.text[:90]!r}"
    print(info)
    if r.status_code == 200 and save:
        p = DOCS / save
        p.write_bytes(r.content)
        with Image.open(p) as im:
            print(f"{'':34s} -> {save} size={im.size} mode={im.mode}")


probe("ascii / plain b64", b64(SIMPLE_ASCII))
probe("cn / plain b64", b64(SIMPLE_CN), "_t_cn_plain.png")
probe("cn / b64 + type=png", b64(SIMPLE_CN) + "?type=png")
probe("full cn / plain b64", b64(FULL_CN), "_t_full_plain.png")
probe("full cn / pako", pako(FULL_CN), "_t_full_pako.png")
probe("full cn / pako + png&scale", pako(FULL_CN) + "?type=png&scale=3", "_t_full_pako_hi.png")
