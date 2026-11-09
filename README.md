# xylab_nailing

XYLab 预制竹木结构机械臂智能钉合控制系统。

面向预制竹木结构墙体钉合 / 托板钉制的机械臂智能建造控制系统，集成缺陷视觉检测、禁区膨胀、KD-tree 钉位优化、规范 RAG 检索、分层决策智能体、机器人执行与数字孪生前端控制界面。

## 仓库结构

```
xylab/          # 主系统代码（前端 / 后端 / 路演脚本）
  frontend/     # React + TypeScript + Vite
  backend/      # FastAPI 后端接口
  pitch/        # 路演 PPT / 文档生成脚本
ai/             # Qwen2.5-VL 等模型服务辅助脚本
docs/           # 打钉系统方案与路演文档
softreg/        # 软件著作权相关材料与核对脚本
```

## 快速启动

### 前端

```bash
cd xylab/frontend
npm install
npm run dev      # http://localhost:5173
```

### 后端（可选）

```bash
cd xylab/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

后端在线时前端自动走 `/api/*`；离线时回退内置模拟数据。

## 说明

- 已排除 `node_modules`、`__pycache__`、前端 `dist` 构建产物。
- 大型数据集、RoboDK 安装包、YOLO 训练权重未纳入本仓库；如需可另行补充。
