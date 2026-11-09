# -*- coding: utf-8 -*-
"""Audit the external-facing proposal: algorithm names must stay out, chosen items must stay in."""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

DOC = r"D:\论文\机械臂大论文\docs\XYLab-打钉系统方案-对外版.md"
text = open(DOC, encoding="utf-8").read()

ALGO_NAMES = [
    "YOLO", "KD-tree", "KDTree", "Sutherland", "Hodgman", "Laplacian", "Minkowski",
    "Kalman", "卡尔曼", "高斯", "形态学", "栅格", "单应", "张正友", "手眼",
    "实例分割", "结构元", "最近邻", "贪心", "ByteTrack", "MoveIt", "OMPL",
    "bge", "Qwen", "vLLM", "TensorRT", "PyTorch", "OpenCV", "mAP",
    "TBK", "FLP", "伪代码", "RAG", "LLM", "Skill", "决策矩阵",
]

MUST_KEEP = [
    "Eurocode 5", "EN 1995", "EN 1382", "EN 1380", "EN 26891", "EN 384", "GB/T 50005",
    "KR 210", "MV-CS050", "Mech-Eye", "PNOZmulti", "deTec4", "EtherCAT",
    "RTX 4000", "PostgreSQL", "RoboDK", "Chroma", "三倍以上",
]

print("=== 算法/模型名残留 ===")
found = False
for name in ALGO_NAMES:
    for m in re.finditer(re.escape(name.lower()), text.lower()):
        start = max(0, m.start() - 35)
        print(f"  [{name}] ...{text[start:m.end() + 35]}...")
        found = True
if not found:
    print("  无")

print("\n=== 按选择应保留的内容 ===")
for kw in MUST_KEEP:
    mark = "OK  " if kw.lower() in text.lower() else "MISS"
    print(f"  {mark} {kw}")

print("\n=== 试验数据绝对值检查（应为空）===")
for pat in [r"\d+\.\d+\s*kN", r"\d+\.\d+\s*kN/mm", r"COV", r"\d+\.\d+\s*%"]:
    hits = [m.group() for m in re.finditer(pat, text)]
    print(f"  {pat}: {hits if hits else '无'}")

print(f"\nchars: {len(text)} | tables: {text.count('|---')} | mermaid: {text.count('mermaid')}")
