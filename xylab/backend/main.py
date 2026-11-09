# -*- coding: utf-8 -*-
"""
XYLab 后端入口。

分层与前端对应：
- api/            HTTP
- inference/      缺陷检测（当前为固定标注）
- planning/       整帧筛选与钉位网格
- sources/        图片、视频、摄像头
- intake/         长板钉位、红外探伤、选优机定级

启动：uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_core import router as core_router
from api.routes_intake import router as intake_router
from api.routes_sources import router as sources_router

app = FastAPI(title="XYLab Nailing Control API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Frame-Width", "X-Frame-Height"],
)
app.include_router(core_router)
app.include_router(sources_router)
app.include_router(intake_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
