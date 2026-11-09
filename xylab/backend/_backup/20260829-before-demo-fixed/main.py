# -*- coding: utf-8 -*-
"""
备份：demo_fixed 改造前的 main.py
时间：2026-08-29
说明：detection_mode 硬编码为 mock
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

from detector import get_detector
from planner import plan_nails

HERE = Path(__file__).resolve().parent
UPLOAD_DIR = HERE / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="XYLab Nailing Control API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_SUFFIX = {".jpg", ".jpeg", ".png", ".webp"}
detector = get_detector()


class PlanRequest(BaseModel):
    image_width: int
    image_height: int
    defects: list[dict]
    edge_margin_px: float = 40
    knot_margin_px: float = 30
    nail_spacing_px: float = 80


class DecideRequest(BaseModel):
    nail_id: str
    context: dict


class RagRequest(BaseModel):
    query: str
    top_k: int = 5


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "xylab-nailing-api",
        "detector": type(detector).__name__,
        "detection_mode": "mock",
    }


@app.post("/api/detect")
async def detect(image: UploadFile = File(...)):
    """接收木板图片。当前为 MockDetector，返回模拟死节框，不是真实识别结果。"""
    suffix = Path(image.filename or "board.jpg").suffix.lower()
    if suffix not in ALLOWED_SUFFIX:
        suffix = ".jpg"
    image_id = uuid.uuid4().hex
    dest = UPLOAD_DIR / f"{image_id}{suffix}"
    raw = await image.read()
    if not raw:
        raise HTTPException(400, "empty image")
    dest.write_bytes(raw)
    try:
        pil = Image.open(dest).convert("RGB")
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, f"cannot read image: {exc}") from exc
    width, height = pil.size
    defects = detector.detect(pil)
    return {
        "image_id": image_id,
        "width": width,
        "height": height,
        "image_url": f"/api/uploads/{dest.name}",
        "detection_mode": "mock",
        "defects": defects,
    }


@app.get("/api/uploads/{name}")
def get_upload(name: str):
    path = (UPLOAD_DIR / Path(name).name).resolve()
    if path.parent != UPLOAD_DIR.resolve() or not path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(path)


@app.post("/api/plan")
def plan(req: PlanRequest):
    """按原图像素坐标做规则钉位规划。不调用浏览器 KD-tree pipeline。"""
    if req.image_width <= 0 or req.image_height <= 0:
        raise HTTPException(400, "invalid image size")
    return plan_nails(
        req.image_width,
        req.image_height,
        req.defects,
        req.edge_margin_px,
        req.knot_margin_px,
        req.nail_spacing_px,
    )


@app.get("/api/rules")
def rules():
    return {"chunks": []}


@app.post("/api/rules/search")
def rules_search(req: RagRequest):
    return {"chunks": []}


@app.post("/api/decide")
def decide(req: DecideRequest):
    return {
        "nail_id": req.nail_id,
        "action": "NAIL",
        "reason": "占位决策，接入 LLM 后替换",
        "cited_codes": ["EN 1995-1-1 §8.3.1.2"],
        "confidence": 0.9,
        "params": {"insertion_angle": 0},
        "risk_flags": [],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
