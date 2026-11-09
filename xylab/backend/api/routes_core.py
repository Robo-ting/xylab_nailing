# -*- coding: utf-8 -*-
"""原有检测、规划和占位接口。图片规划默认仍走演示可钉矩形。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

from inference.detector import get_demo_nailable_region, get_demo_plan_scale, get_detector
from planning.planner import plan_nails

router = APIRouter()
detector = get_detector()

HERE = Path(__file__).resolve().parents[1]
UPLOAD_DIR = HERE / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_SUFFIX = {".jpg", ".jpeg", ".png", ".webp"}


class PlanRequest(BaseModel):
    image_width: int
    image_height: int
    defects: list[dict]
    edge_margin_px: float = 40
    knot_margin_px: float = 30
    nail_spacing_px: float = 80
    full_frame: bool = False


class DecideRequest(BaseModel):
    nail_id: str
    context: dict


class RagRequest(BaseModel):
    query: str
    top_k: int = 5


@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "xylab-nailing-api",
        "detector": type(detector).__name__,
        "detection_mode": getattr(detector, "detection_mode", "mock"),
    }


@router.post("/api/detect")
async def detect(image: UploadFile = File(...)):
    """接收木板图片。1024×768 demo 图返回人工预标注节疤框。"""
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
        "detection_mode": getattr(detector, "detection_mode", "mock"),
        "defects": defects,
    }


@router.get("/api/uploads/{name}")
def get_upload(name: str):
    path = (UPLOAD_DIR / Path(name).name).resolve()
    if path.parent != UPLOAD_DIR.resolve() or not path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(path)


@router.post("/api/plan")
def plan(req: PlanRequest):
    """按原图像素坐标做规则钉位规划。

    full_frame 为假时，演示图仍限制在固定可钉矩形。
    图片/视频输入源走 full_frame，钉点铺整张图。
    """
    if req.image_width <= 0 or req.image_height <= 0:
        raise HTTPException(400, "invalid image size")
    edge = req.edge_margin_px
    knot_m = req.knot_margin_px
    spacing = req.nail_spacing_px
    nailable = None
    if not req.full_frame:
        nailable = get_demo_nailable_region((req.image_width, req.image_height))
        plan_scale = get_demo_plan_scale((req.image_width, req.image_height))
        if nailable and plan_scale:
            edge *= plan_scale
            knot_m *= plan_scale
            spacing *= plan_scale
    return plan_nails(
        req.image_width,
        req.image_height,
        req.defects,
        edge,
        knot_m,
        spacing,
        nailable_region=nailable,
    )


@router.get("/api/rules")
def rules():
    return {"chunks": []}


@router.post("/api/rules/search")
def rules_search(req: RagRequest):
    return {"chunks": []}


@router.post("/api/decide")
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
