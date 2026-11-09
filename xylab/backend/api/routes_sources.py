# -*- coding: utf-8 -*-
"""图片、视频、摄像头输入，以及停帧多边形。"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from PIL import Image
from pydantic import BaseModel

from api.routes_core import UPLOAD_DIR, detector
from planning.planner import plan_nails
from planning.zone_filter import filter_defects
from sources.registry import VIDEO_SUFFIX, FrameSource, bgr_to_pil, encode_jpeg, pil_to_bgr, registry

router = APIRouter()


class ZoneBody(BaseModel):
    points: list[list[float]]
    frame_w: int = 0
    frame_h: int = 0


class RunBody(BaseModel):
    edge_margin_px: float = 40
    knot_margin_px: float = 30
    nail_spacing_px: float = 80


def _parse_zone(raw: str | None) -> list[list[float]] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "区域坐标不是合法 JSON") from exc
    if not isinstance(data, list):
        raise HTTPException(400, "区域坐标格式不对")
    return data


def _require(source_id: str) -> FrameSource:
    src = registry.get(source_id)
    if src is None or src.closed:
        raise HTTPException(404, "输入源不存在")
    return src


def _http_runtime(exc: Exception) -> HTTPException:
    return HTTPException(503, str(exc))


def _run_on(src: FrameSource, edge: float, knot_m: float, spacing: float) -> dict:
    shot = src.snapshot()
    if shot is None:
        raise HTTPException(503, "还没有画面")
    _frame, width, height = shot
    defects = detector.detect(bgr_to_pil(_frame))
    zone, scaled = src.current_zone()
    kept, dropped = filter_defects(defects, zone)
    planned = plan_nails(width, height, kept, edge, knot_m, spacing, nailable_region=None)
    body = src.summary()
    body.update(
        {
            "frame_jpeg": base64.b64encode(encode_jpeg(_frame)).decode("ascii"),
            "zone_scaled": scaled,
            "detection_mode": getattr(detector, "detection_mode", "mock"),
            "defects": kept,
            "dropped": dropped,
            "forbidden_regions": planned["forbidden_regions"],
            "nail_points": planned["nail_points"],
        }
    )
    return body


@router.post("/api/sources/image")
async def create_image(
    image: UploadFile = File(...),
    zone: str | None = Form(default=None),
    zone_w: int = Form(default=0),
    zone_h: int = Form(default=0),
):
    raw = await image.read()
    if not raw:
        raise HTTPException(400, "空图片")
    try:
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
        bgr = pil_to_bgr(pil)
    except RuntimeError as exc:
        raise _http_runtime(exc) from exc
    except Exception as exc:
        raise HTTPException(400, f"读不了这张图: {exc}") from exc
    registry.release_all()
    src = FrameSource("image")
    src.paused = True
    src.set_frame(bgr)
    src.adopt_zone(_parse_zone(zone), zone_w, zone_h)
    registry.add(src)
    return src.summary()


@router.post("/api/sources/{source_id}/image")
async def replace_image(source_id: str, image: UploadFile = File(...)):
    src = _require(source_id)
    raw = await image.read()
    if not raw:
        raise HTTPException(400, "空图片")
    try:
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
        src.replace_image(pil_to_bgr(pil))
    except RuntimeError as exc:
        raise _http_runtime(exc) from exc
    except Exception as exc:
        raise HTTPException(400, f"读不了这张图: {exc}") from exc
    return src.summary()


@router.post("/api/sources/video")
async def create_video(
    video: UploadFile = File(...),
    zone: str | None = Form(default=None),
    zone_w: int = Form(default=0),
    zone_h: int = Form(default=0),
):
    suffix = Path(video.filename or "clip.mp4").suffix.lower()
    if suffix not in VIDEO_SUFFIX:
        raise HTTPException(400, "视频格式限于 mp4、avi、mov、webm、mkv")
    raw = await video.read()
    if not raw:
        raise HTTPException(400, "空视频")
    registry.release_all()
    src = FrameSource("video")
    dest = UPLOAD_DIR / f"{src.id}{suffix}"
    dest.write_bytes(raw)
    try:
        src.start_capture(str(dest))
        src.adopt_zone(_parse_zone(zone), zone_w, zone_h)
    except RuntimeError as exc:
        src.close()
        dest.unlink(missing_ok=True)
        raise _http_runtime(exc) from exc
    registry.add(src)
    return src.summary()


@router.post("/api/sources/camera")
def create_camera(
    camera_index: int = 0,
    zone: str | None = None,
    zone_w: int = 0,
    zone_h: int = 0,
):
    if camera_index < 0 or camera_index > 8:
        raise HTTPException(400, "摄像头序号超出范围")
    registry.release_all()
    src = FrameSource("camera")
    try:
        src.start_capture(camera_index)
        src.adopt_zone(_parse_zone(zone), zone_w, zone_h)
    except RuntimeError as exc:
        src.close()
        raise _http_runtime(exc) from exc
    registry.add(src)
    return src.summary()


@router.get("/api/sources/{source_id}")
def get_source(source_id: str):
    return _require(source_id).summary()


@router.post("/api/sources/{source_id}/pause")
def pause_source(source_id: str):
    src = _require(source_id)
    src.pause()
    return {"status": "ok", "paused": True}


@router.post("/api/sources/{source_id}/resume")
def resume_source(source_id: str):
    src = _require(source_id)
    src.resume()
    return {"status": "ok", "paused": src.paused}


@router.get("/api/sources/{source_id}/snapshot")
def snapshot(source_id: str):
    src = _require(source_id)
    shot = src.snapshot()
    if shot is None:
        raise HTTPException(503, "还没有画面")
    frame, width, height = shot
    try:
        payload = encode_jpeg(frame)
    except RuntimeError as exc:
        raise _http_runtime(exc) from exc
    return Response(
        content=payload,
        media_type="image/jpeg",
        headers={
            "X-Frame-Width": str(width),
            "X-Frame-Height": str(height),
            "Cache-Control": "no-store",
        },
    )


@router.get("/api/sources/{source_id}/stream")
def stream(source_id: str):
    src = _require(source_id)

    def frames():
        import time

        while True:
            current = registry.get(source_id)
            if current is None or current.closed:
                break
            shot = current.snapshot()
            if shot is None:
                time.sleep(0.05)
                continue
            try:
                jpg = encode_jpeg(shot[0])
            except RuntimeError:
                break
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
            time.sleep(0.05)

    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/api/sources/{source_id}/zone")
def get_zone(source_id: str):
    src = _require(source_id)
    body = src.summary()
    return {"zone": body["zone"], "frame_w": body["width"], "frame_h": body["height"], "zone_scaled": body["zone_scaled"]}


@router.post("/api/sources/{source_id}/zone")
def set_zone(source_id: str, body: ZoneBody):
    src = _require(source_id)
    if len(body.points) < 3:
        raise HTTPException(400, "至少需要 3 个顶点")
    try:
        src.set_zone(body.points, body.frame_w or src.width, body.frame_h or src.height)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return src.summary()


@router.delete("/api/sources/{source_id}/zone")
def delete_zone(source_id: str):
    src = _require(source_id)
    src.clear_zone()
    return src.summary()


@router.post("/api/sources/{source_id}/run")
def run_source(source_id: str, body: RunBody):
    src = _require(source_id)
    try:
        return _run_on(src, body.edge_margin_px, body.knot_margin_px, body.nail_spacing_px)
    except RuntimeError as exc:
        raise _http_runtime(exc) from exc
