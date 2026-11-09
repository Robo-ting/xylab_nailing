# XYLab 预制竹木结构机械臂智能钉合控制系统

> 面向预制竹木结构墙体钉合 / 托板钉制的机械臂智能建造控制系统。集成缺陷视觉检测、禁区膨胀、KD-tree 钉位优化、规范 RAG 检索、分层决策智能体、机器人执行与数字孪生的一体化前端控制界面。

本系统为软件著作权登记配套的可交互前端控制界面。核心几何算法（栅格化、形态学膨胀、KD-tree 最近邻、多边形求交、软代价图、Eurocode 5 间距）均在浏览器端**真实计算**；缺陷检测（YOLOv8-seg）与大模型决策（LLM）通过后端 API 预留对接（当前使用内置数据，可无缝切换到真实模型）。

---

## 一、技术栈

| 层 | 技术 |
| --- | --- |
| 前端框架 | React 18 + TypeScript + Vite 5 |
| 状态管理 | Zustand |
| 路由 | React Router (HashRouter) |
| 可视化 | HTML5 Canvas 2D（自研渲染引擎） |
| 后端接口桩 | Python FastAPI（预留 YOLO / RAG / LLM / ROS 对接） |

## 二、功能模块（11 个）

1. 总控台 Dashboard — 全流程状态机、统计概览、一键运行
2. 装配标定 Calibration — T 型节点板件标定、重合区求交、手眼对齐（≤0.5mm）
3. 感知检测 Perception — YOLOv8-seg 7 类缺陷分割、类别开关、置信度过滤、基材/木纹分析
4. 钉位规划 Planning — **ROI 框选（矩形/圆形/任意多边形）** + 四步流水线（检测→原始禁区→膨胀禁区→KD-tree 选点）+ 软/硬代价图
5. 规范规则库 RuleBase — 规范 ingest、RAG 语义检索、防幻觉引用校验
6. 决策矩阵 DecisionMatrix — 缺陷×基材×纹理决策矩阵、Eurocode 5 间距计算器
7. 决策智能体 AgentConsole — 分层决策、逐钉决策 JSON、人工复核队列
8. 机器人执行 RobotControl — KUKA 技能原语、状态机、执行时序
9. 数字孪生 DigitalTwin — 上料→扫描→打钉 2D 仿真动画
10. 日志与报告 LogsReports — 逐钉施工日志、JSON/CSV 导出
11. 力学试验 MechanicsLab — 试件矩阵、EN 1382 加载速率标定、Johansen 承载力、κ(d) 折减

## 三、核心算法（前端真实实现）

| 模块 | 文件 | 说明 |
| --- | --- | --- |
| 几何 | `src/lib/geometry.ts` | 射线法点在多边形、多边形求交(Sutherland–Hodgman)、腐蚀、面积 |
| 栅格化 | `src/lib/grid.ts` | 缺陷掩码栅格化 + ROI 过滤 |
| 形态学膨胀 | `src/lib/morphology.ts` | 圆形核 Minkowski 膨胀（r 默认 10mm） |
| KD-tree | `src/lib/kdtree.ts` | 二维最近邻查询 |
| 软代价图 | `src/lib/costmap.ts` | 高斯衰减代价场 + 目标函数寻优 |
| Eurocode 5 | `src/lib/ec5.ts` | Table 8.2 间距/边距/端距 |
| 决策引擎 | `src/lib/decision.ts` | 分层决策 + 缺陷决策矩阵 |
| 流水线编排 | `src/lib/pipeline.ts` | 全流程串联 |

## 四、运行方式

### 前端

```bash
cd 机械臂大论文/src/xylab/frontend
npm install
npm run dev      # 开发模式，默认 http://localhost:5173
# 或
npm run build && npm run preview   # 生产构建 + 预览
```

> 本机 Node 通过 conda 环境 `nodeenv` 提供。若新开终端，先激活：
> `conda activate nodeenv`（或将其 bin 目录加入 PATH）。

### 后端（可选，预留接口）

```bash
cd 机械臂大论文/src/xylab/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

后端在线时，前端自动切换到 `/api/*` 真实接口；离线时回退内置数据。前端顶栏显示「后端在线 / 模拟数据」状态。

## 五、目录结构

```
机械臂大论文/src/xylab/
├── frontend/
│   ├── src/
│   │   ├── lib/          核心算法库
│   │   ├── mock/         内置数据（缺陷/板件/规范/力学）
│   │   ├── api/          API 服务层（后端回退）
│   │   ├── store/        全局状态
│   │   ├── components/   通用组件 + 交互画布
│   │   ├── pages/        功能页面（感知检测、钉位扫描、选区检测分开）
│   │   └── styles/       全局主题
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── main.py           启动入口（uvicorn main:app）
│   ├── api/              HTTP：选区接口与钉位扫描接口分开
│   ├── inference/        缺陷检测（当前固定标注，可换 YOLO）
│   ├── planning/         多边形筛选 + 整图钉位网格
│   ├── sources/          选区检测的当前帧与多边形
│   ├── intake/           长板钉位、红外探伤、选优机定级
│   └── requirements.txt
├── pitch/
│   ├── build_deck.py     投资路演 PPT 生成脚本
│   └── assets/           截图等素材
└── README.md
```

## 六、软件著作权说明

- 软件名称：XYLab 预制竹木结构机械臂智能钉合控制系统
- 开发语言：TypeScript / Python
- 运行环境：现代浏览器（Chrome/Edge）+ Node.js 18+；后端 Python 3.10+
- 主要源代码位于 `frontend/src/`，可用于软著申请的源程序材料。
