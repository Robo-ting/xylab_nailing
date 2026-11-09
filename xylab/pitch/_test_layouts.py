# -*- coding: utf-8 -*-
"""Round 5: reshape the image-quality gate chain, which is 31 cm tall as authored.

The original draws one action node per failed gate, making the vertical spine 12
nodes deep. Variants collapse the repeated "adjust and re-capture" actions into a
single shared node and/or split the gate chain into two rows.
"""
import base64
import sys
import time
from pathlib import Path

import requests
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(r"D:\论文\机械臂大论文\docs\_layout_tests")
OUT.mkdir(parents=True, exist_ok=True)

PALETTE = """
    classDef stage fill:#E8F1FF,stroke:#2563EB,stroke-width:1px,color:#1E3A8A;
    classDef gate fill:#FFF7ED,stroke:#EA580C,stroke-width:1px,color:#9A3412;
    classDef exec fill:#ECFDF5,stroke:#059669,stroke-width:1px,color:#065F46;
    classDef alert fill:#FEF2F2,stroke:#DC2626,stroke-width:1px,color:#991B1B;
"""

# A: single shared re-capture node, straight TB spine
VAR_A = """flowchart TB
    A["采集板面图像帧"] --> B{"清晰度是否达标"}
    B -- "是" --> C{"曝光是否正常"}
    C -- "是" --> D{"缺陷成像尺寸是否足够"}
    D -- "是" --> E{"掩码是否完整"}
    E -- "是" --> F{"反光是否可控"}
    F -- "是" --> G["判定为合格帧"]
    G --> H["进入缺陷分割与决策"]
    B -- "否" --> R["调整采集条件<br/>补光 / 静止 / 变焦 / 移位后重采"]
    C -- "否" --> R
    D -- "否" --> R
    E -- "否" --> R
    F -- "否" --> U["返回 UNKNOWN<br/>禁止判为无缺陷"]
    R -. "重采" .-> A
    U --> V["写入人工复核队列"]
""" + PALETTE + """
    class A,G,H,R stage;
    class B,C,D,E,F gate;
    class U,V alert;
"""

# B: gates split into two LR rows inside subgraphs
VAR_B = """flowchart TB
    A["采集板面图像帧"]
    subgraph Q1["成像基础质量"]
        direction LR
        B{"清晰度<br/>是否达标"} --> C{"曝光<br/>是否正常"} --> D{"缺陷成像<br/>尺寸是否足够"}
    end
    subgraph Q2["目标可判性"]
        direction LR
        E{"掩码<br/>是否完整"} --> F{"反光<br/>是否可控"}
    end
    A --> Q1 --> Q2
    F -- "是" --> G["判定为合格帧"] --> H["进入缺陷分割与决策"]
    B -. "否" .-> R["调整采集条件<br/>补光 / 静止 / 变焦 / 移位后重采"]
    C -. "否" .-> R
    D -. "否" .-> R
    E -. "否" .-> R
    F -. "否" .-> U["返回 UNKNOWN<br/>禁止判为无缺陷"]
    U --> V["写入人工复核队列"]
""" + PALETTE + """
    class A,G,H,R stage;
    class B,C,D,E,F gate;
    class U,V alert;
    style Q1 fill:#F8FAFC,stroke:#94A3B8,color:#1E3A8A;
    style Q2 fill:#F8FAFC,stroke:#94A3B8,color:#1E3A8A;
"""

# C: gate chain laid out left-to-right with shared failure sinks below
VAR_C = """flowchart LR
    A["采集板面<br/>图像帧"] --> B{"清晰度"} --> C{"曝光"} --> D{"缺陷<br/>成像尺寸"} --> E{"掩码<br/>完整度"} --> F{"反光<br/>可控性"} --> G["判定为<br/>合格帧"] --> H["进入缺陷<br/>分割与决策"]
    B -. "否" .-> R["调整采集条件<br/>补光 / 静止 / 变焦 / 移位后重采"]
    C -. "否" .-> R
    D -. "否" .-> R
    E -. "否" .-> R
    F -. "否" .-> U["返回 UNKNOWN<br/>禁止判为无缺陷"]
    R -. "重采" .-> A
    U --> V["写入人工<br/>复核队列"]
""" + PALETTE + """
    class A,G,H,R stage;
    class B,C,D,E,F gate;
    class U,V alert;
"""

CANDIDATES = {"qg_A_sharedR": VAR_A, "qg_B_tworows": VAR_B, "qg_C_lr": VAR_C}
TARGET_LO, TARGET_HI = 0.70, 1.80


def fetch(code: str, name: str):
    enc = base64.urlsafe_b64encode(code.encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/img/{enc}?type=png&width=2600&bgColor=FFFFFF"
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 200 and len(r.content) > 2000:
                p = OUT / f"{name}.png"
                p.write_bytes(r.content)
                with Image.open(p) as im:
                    w, h = im.size
                ratio = w / h
                verdict = "FITS" if TARGET_LO <= ratio <= TARGET_HI else ("too tall" if ratio < TARGET_LO else "too wide")
                print(f"  {name:16s} {w}x{h}  ratio={ratio:5.2f}  @15.4cm -> {15.4 / ratio:5.1f}cm  [{verdict}]")
                return
            print(f"  {name:16s} HTTP {r.status_code}  {r.text[:80]!r}")
        except Exception as exc:
            print(f"  {name:16s} {type(exc).__name__}")
        time.sleep(3 * (attempt + 1))


for name, code in CANDIDATES.items():
    fetch(code, name)
print(f"\nimages -> {OUT}")
