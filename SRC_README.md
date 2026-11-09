# 机械臂大论文 · 源代码目录

本目录集中存放毕业论文相关的**可执行代码与工程**，与论文正文、数据集、配置等并列，便于统一开发与版本管理。

## 目录规划

```
机械臂大论文/
├── src/                    ← 本目录（执行代码）
│   ├── README.md
│   └── xylab/              XYLab 钉合控制系统
│       ├── frontend/       React 控制界面 + 浏览器端算法
│       ├── backend/        FastAPI 接口桩（YOLO / RAG / LLM 预留）
│       ├── pitch/          投资路演 PPT 生成脚本
│       └── README.md       子项目说明
├── docs/                   文档与产出物
│   └── XYLab-投资路演-PitchDeck.pptx
├── yolov11/                视觉检测模型与训练
├── kuka/                   机械臂配置与标定
└── …                       其他论文资料
```

## 子项目

| 路径 | 说明 |
| --- | --- |
| [xylab/](xylab/README.md) | **XYLab 预制竹木结构机械臂智能钉合控制系统** — 软著配套前端、钉位规划算法、决策智能体、数字孪生等 |
| *(预留)* | 后续可在此新增 ROS 节点、标定脚本、实验批处理等 |

## 快速入口

```bash
# 前端（详见 xylab/README.md）
cd xylab/frontend && npm run dev

# 后端桩（可选）
cd xylab/backend && uvicorn main:app --reload --port 8000

# 重新生成投资路演 PPT
cd xylab/pitch && python build_deck.py
# 输出：../docs/XYLab-投资路演-PitchDeck.pptx
```

> 原路径 `D:\论文\xylab-nailing-system\` 已迁移至此；旧目录仅保留跳转说明。
