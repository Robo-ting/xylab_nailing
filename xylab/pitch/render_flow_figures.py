# -*- coding: utf-8 -*-
"""Render Word-ready flowchart PNGs (no mermaid source in the delivered docs)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["axes.unicode_minus"] = False
for _name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC"):
    if any(_name.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [_name, "DejaVu Sans"]
        break
else:
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]

OUT = Path(__file__).resolve().parent / "assets" / "proposal_flows"
OUT.mkdir(parents=True, exist_ok=True)

# palette aligned with the DSV mermaid classDefs
C = {
    "primary": ("#E8F1FF", "#2563EB", "#1E3A8A"),
    "process": ("#ECFDF5", "#059669", "#065F46"),
    "decision": ("#FFF7ED", "#EA580C", "#9A3412"),
    "result": ("#FEF2F2", "#DC2626", "#991B1B"),
    "stage": ("#F8FAFC", "#94A3B8", "#1E3A8A"),
}


def box(ax, x, y, w, h, text, kind="process", fs=9.5):
    fill, edge, tc = C[kind]
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.08",
        linewidth=1.4,
        facecolor=fill,
        edgecolor=edge,
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, zorder=3, linespacing=1.25)
    return (x, y)


def diamond(ax, x, y, w, h, text, fs=8.8):
    fill, edge, tc = C["decision"]
    xs = [x, x + w / 2, x, x - w / 2]
    ys = [y + h / 2, y, y - h / 2, y]
    ax.fill(xs, ys, facecolor=fill, edgecolor=edge, linewidth=1.4, zorder=2)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, zorder=3, linespacing=1.2)
    return (x, y)


def arrow(ax, a, b, text="", rad=0.0):
    ax.annotate(
        "",
        xy=b,
        xytext=a,
        arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.15, connectionstyle=f"arc3,rad={rad}"),
        zorder=1,
    )
    if text:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        ax.text(mx, my + 0.12, text, ha="center", va="bottom", fontsize=7.5, color="#334155")


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("FIG", path)
    return path


def fig_internal_arch():
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    ax.set_title("总体算法架构：感知 — AI 决策 — 执行", fontsize=13, color="#0F172A", pad=8)

    def band(y0, y1, title, color):
        ax.add_patch(FancyBboxPatch((0.25, y0), 11.5, y1 - y0, boxstyle="round,pad=0.01,rounding_size=0.06",
                                    facecolor=color, edgecolor="#94A3B8", lw=0.8, zorder=0))
        ax.text(0.4, (y0 + y1) / 2, title, ha="left", va="center", fontsize=9, color="#1E3A8A", rotation=90)

    band(3.55, 5.05, "感知层", "#F1F5F9")
    band(1.85, 3.35, "AI决策", "#F8FAFC")
    band(0.15, 1.65, "执行层", "#F1F5F9")

    a = box(ax, 2.1, 4.3, 1.7, 0.7, "工单下发", "primary", 9)
    b = box(ax, 4.3, 4.3, 1.9, 0.7, "上料与位姿标定", "primary", 9)
    c = box(ax, 6.6, 4.3, 1.7, 0.7, "全板扫描", "primary", 9)
    d = box(ax, 9.1, 4.3, 2.0, 0.7, "缺陷实例分割\n7 类", "primary", 9)
    for p, q in [(a, b), (b, c), (c, d)]:
        arrow(ax, (p[0] + 0.9, p[1]), (q[0] - 0.9, q[1]))

    e = box(ax, 2.1, 2.6, 1.9, 0.75, "Skill\n禁区膨胀", "process", 8.8)
    f = box(ax, 4.5, 2.6, 2.0, 0.75, "Skill\n几何寻优", "process", 8.8)
    g = box(ax, 6.9, 2.6, 1.9, 0.75, "逐钉位\n停靠复核", "process", 8.8)
    h = diamond(ax, 9.3, 2.6, 2.35, 1.1, "AI 决策 Agent\n坐标 + 动作")
    for p, q in [(e, f), (f, g)]:
        arrow(ax, (p[0] + 1.0, p[1]), (q[0] - 1.0, q[1]))
    arrow(ax, (g[0] + 1.0, g[1]), (h[0] - 1.05, h[1]))

    i = box(ax, 2.4, 0.9, 1.9, 0.7, "机械臂执行", "process", 9)
    j = box(ax, 4.8, 0.9, 1.9, 0.7, "执行过程监控", "process", 9)
    k = box(ax, 7.3, 0.9, 1.9, 0.7, "证据包与施工日志", "process", 8.8)
    l = box(ax, 10.0, 0.9, 1.8, 0.7, "人工复核队列", "result", 9)
    for p, q in [(i, j), (j, k)]:
        arrow(ax, (p[0] + 1.0, p[1]), (q[0] - 1.0, q[1]))
    arrow(ax, (l[0] - 0.95, l[1]), (k[0] + 1.0, k[1]))

    arrow(ax, (h[0] - 0.4, h[1] - 0.52), (i[0] + 0.4, i[1] + 0.38), "放行")
    arrow(ax, (h[0] + 0.55, h[1] - 0.45), (l[0], l[1] + 0.38), "跳过")
    return save(fig, "internal_architecture.png")


def fig_internal_quality():
    fig, ax = plt.subplots(figsize=(10.6, 6.4))
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 8.4)
    ax.axis("off")
    ax.set_title("图像质量门控：不合格不得判为无缺陷", fontsize=13, color="#0F172A", pad=6)

    a = box(ax, 5.3, 7.7, 2.6, 0.6, "采集板面图像帧", "primary")
    b = diamond(ax, 5.3, 6.55, 2.8, 1.0, "清晰度合格？")
    c = diamond(ax, 5.3, 5.15, 2.8, 1.0, "曝光正常？")
    d = diamond(ax, 5.3, 3.75, 2.8, 1.0, "缺陷像素足够？")
    e = diamond(ax, 5.3, 2.35, 2.8, 1.0, "掩码完整且\n反光可控？")
    g = box(ax, 5.3, 0.95, 2.8, 0.7, "合格帧\n进入缺陷分割与决策", "process")
    r = box(ax, 8.5, 5.15, 2.4, 0.9, "调整采集条件后重采\n补光 / 静止 / 变焦 / 移位", "primary", 8.5)
    u = box(ax, 1.7, 2.35, 2.4, 0.85, "返回 UNKNOWN\n禁止判为无缺陷", "result", 8.5)
    v = box(ax, 1.7, 0.95, 2.4, 0.7, "写入人工复核队列", "result", 8.8)

    arrow(ax, (a[0], a[1] - 0.32), (b[0], b[1] + 0.48))
    arrow(ax, (b[0], b[1] - 0.5), (c[0], c[1] + 0.5), "是")
    arrow(ax, (c[0], c[1] - 0.5), (d[0], d[1] + 0.5), "是")
    arrow(ax, (d[0], d[1] - 0.5), (e[0], e[1] + 0.5), "是")
    arrow(ax, (e[0], e[1] - 0.5), (g[0], g[1] + 0.38), "是")
    arrow(ax, (b[0] + 1.35, b[1]), (r[0] - 1.2, r[1] + 0.6), "否")
    arrow(ax, (c[0] + 1.35, c[1]), (r[0] - 1.2, r[1]))
    arrow(ax, (d[0] + 1.35, d[1]), (r[0] - 1.2, r[1] - 0.55), "否")
    arrow(ax, (e[0] - 1.35, e[1]), (u[0] + 1.2, u[1]), "否")
    arrow(ax, (u[0], u[1] - 0.45), (v[0], v[1] + 0.38))
    arrow(ax, (r[0], r[1] + 0.48), (a[0] + 1.4, a[1]), "", rad=-0.18)
    return save(fig, "internal_quality.png")


def fig_external_overall():
    fig, ax = plt.subplots(figsize=(12.4, 5.6))
    ax.set_xlim(0, 13.0)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    ax.set_title("整体技术方案流程", fontsize=13, color="#0F172A", pad=6)

    a = box(ax, 1.5, 4.7, 2.0, 0.7, "构件上料到位", "primary", 9)
    b = box(ax, 4.4, 4.7, 2.2, 0.7, "采集板面环境信息", "process", 9)
    c = box(ax, 7.4, 4.7, 2.3, 0.7, "识别材料缺陷及既有钉件", "process", 8.6)
    d = diamond(ax, 10.8, 4.7, 2.6, 1.05, "成像条件\n是否满足判定")
    arrow(ax, (a[0] + 1.05, a[1]), (b[0] - 1.15, b[1]))
    arrow(ax, (b[0] + 1.15, b[1]), (c[0] - 1.2, c[1]))
    arrow(ax, (c[0] + 1.2, c[1]), (d[0] - 1.25, d[1]))

    e = box(ax, 1.6, 2.85, 2.1, 0.7, "建立缺陷避让范围", "process", 8.8)
    f = box(ax, 4.4, 2.85, 2.1, 0.7, "逐钉位可行性判定", "process", 8.8)
    g = diamond(ax, 7.4, 2.85, 2.5, 1.0, "钉位是否\n满足施工要求")
    h = box(ax, 10.6, 2.85, 2.1, 0.7, "调整钉位或切换工艺", "process", 8.6)
    arrow(ax, (d[0] - 0.4, d[1] - 0.52), (e[0] + 0.3, e[1] + 0.38), "满足")
    arrow(ax, (e[0] + 1.1, e[1]), (f[0] - 1.1, f[1]))
    arrow(ax, (f[0] + 1.1, f[1]), (g[0] - 1.2, g[1]))
    arrow(ax, (g[0] + 1.25, g[1]), (h[0] - 1.1, h[1]), "不满足")

    i = diamond(ax, 10.6, 1.15, 2.5, 1.0, "调整后是否\n存在可用点位")
    j = box(ax, 7.4, 1.15, 2.1, 0.7, "执行钉合作业", "process", 9)
    k = box(ax, 4.4, 1.15, 2.2, 0.7, "生成待复核事件", "result", 9)
    l = box(ax, 1.6, 1.15, 2.2, 0.7, "记录结果，下一钉位", "process", 8.6)
    arrow(ax, (h[0], h[1] - 0.38), (i[0], i[1] + 0.5))
    arrow(ax, (g[0], g[1] - 0.5), (j[0], j[1] + 0.38), "满足")
    arrow(ax, (i[0] - 1.25, i[1]), (j[0] + 1.1, j[1]), "是")
    arrow(ax, (i[0] - 0.6, i[1] - 0.15), (k[0] + 1.15, k[1]), "否")
    arrow(ax, (d[0] - 1.6, d[1] - 0.4), (k[0] + 0.4, k[1] + 0.38), "不满足")
    arrow(ax, (j[0] - 1.1, j[1]), (l[0] + 1.15, l[1] + 0.12))
    arrow(ax, (k[0] - 1.15, k[1]), (l[0] + 1.15, l[1]))
    return save(fig, "external_overall.png")


def fig_external_process():
    fig, ax = plt.subplots(figsize=(8.8, 10.2))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 12.4)
    ax.axis("off")
    ax.set_title("系统整体实现流程", fontsize=13, color="#0F172A", pad=6)

    items = [
        (4.5, 11.7, "工单下发\n构件与工艺参数", "primary", False),
        (4.5, 10.55, "构件上料与空间定位", "process", False),
        (4.5, 9.4, "定位偏差是否合格", "decision", True),
        (4.5, 8.15, "全板信息采集", "process", False),
        (4.5, 7.0, "成像质量是否合格", "decision", True),
        (4.5, 5.75, "材料缺陷与既有钉件识别", "process", False),
        (4.5, 4.7, "建立避让范围并完成全板规划", "process", False),
        (4.5, 3.65, "逐钉位停靠复核与分层决策", "process", False),
        (4.5, 2.5, "执行结果是否合格", "decision", True),
        (4.5, 1.35, "记录施工信息", "process", False),
        (4.5, 0.35, "生成施工报告并上传管理平台", "primary", False),
    ]
    pts = []
    for x, y, t, k, is_d in items:
        pts.append(diamond(ax, x, y, 3.4, 0.9, t) if is_d else box(ax, x, y, 3.6, 0.72, t, k, 9))
    for i in range(len(pts) - 1):
        arrow(ax, (pts[i][0], pts[i][1] - 0.4), (pts[i + 1][0], pts[i + 1][1] + 0.38))

    r1 = box(ax, 7.5, 9.4, 2.2, 0.7, "提示重新上料", "result", 8.5)
    r2 = box(ax, 7.5, 7.0, 2.2, 0.7, "调整后重采", "primary", 8.5)
    r3 = box(ax, 7.5, 2.5, 2.2, 0.7, "待复核队列", "result", 8.5)
    arrow(ax, (pts[2][0] + 1.7, pts[2][1]), (r1[0] - 1.15, r1[1]), "不合格")
    arrow(ax, (pts[4][0] + 1.7, pts[4][1]), (r2[0] - 1.15, r2[1]), "不合格")
    arrow(ax, (pts[8][0] + 1.7, pts[8][1]), (r3[0] - 1.15, r3[1]), "不合格")
    return save(fig, "external_process.png")


def main():
    fig_internal_arch()
    fig_internal_quality()
    fig_external_overall()
    fig_external_process()


if __name__ == "__main__":
    main()
