# 备份说明

## 20260829-before-demo-fixed

改造 demo_fixed 固定人工标注之前的状态。

| 文件 | 说明 |
|------|------|
| `detector.py` | MockDetector，按宽高比例生成模拟框 |
| `main.py` | `detection_mode` 硬编码为 `mock` |

恢复方式（在 `backend/` 目录下）：

```powershell
Copy-Item _backup\20260829-before-demo-fixed\detector.py detector.py -Force
Copy-Item _backup\20260829-before-demo-fixed\main.py main.py -Force
```

当前工作区 `detector.py` / `main.py` 已是 **demo_fixed** 版本。
