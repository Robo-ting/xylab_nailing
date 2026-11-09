# -*- coding: utf-8 -*-
"""一路输入的当前帧和多边形。后续帧、后续图片沿用这份区域。"""
from __future__ import annotations

import threading
import uuid
from typing import Any

import numpy as np
from PIL import Image

from planning.zone_filter import scale_polygon


def _cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("需要安装 opencv-python") from exc
    return cv2


VIDEO_SUFFIX = {".mp4", ".avi", ".mov", ".webm", ".mkv"}


def bgr_to_pil(frame: np.ndarray) -> Image.Image:
    cv2 = _cv2()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    cv2 = _cv2()
    rgb = np.asarray(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def encode_jpeg(frame: np.ndarray) -> bytes:
    cv2 = _cv2()
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("画面编码失败")
    return buf.tobytes()


def open_capture(source: int | str):
    cv2 = _cv2()
    if isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(source, cv2.CAP_MSMF)
        return cap
    return cv2.VideoCapture(source)


class FrameSource:
    def __init__(self, kind: str):
        self.id = uuid.uuid4().hex
        self.kind = kind
        self.frame: np.ndarray | None = None
        self.width = 0
        self.height = 0
        self.zone: np.ndarray | None = None
        self.zone_w = 0
        self.zone_h = 0
        self.zone_scaled = False
        self.paused = False
        self.closed = False
        self.cap = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def set_frame(self, bgr: np.ndarray) -> None:
        h, w = int(bgr.shape[0]), int(bgr.shape[1])
        with self._lock:
            self.frame = bgr
            if self.zone is not None and self.zone_w > 0 and (w != self.zone_w or h != self.zone_h):
                self.zone = scale_polygon(self.zone, self.zone_w, self.zone_h, w, h)
                self.zone_w = w
                self.zone_h = h
                self.zone_scaled = True
            self.width = w
            self.height = h

    def snapshot(self) -> tuple[np.ndarray, int, int] | None:
        with self._lock:
            if self.frame is None:
                return None
            return self.frame.copy(), self.width, self.height

    def current_zone(self) -> tuple[np.ndarray | None, bool]:
        with self._lock:
            if self.zone is None or len(self.zone) < 3:
                return None, self.zone_scaled
            return self.zone.copy(), self.zone_scaled

    def set_zone(self, points: list[list[float]], src_w: int, src_h: int) -> bool:
        arr = np.asarray(points, dtype=np.float32).reshape(-1, 2)
        if arr.shape[0] < 3:
            raise ValueError("至少需要 3 个顶点")
        with self._lock:
            scaled = False
            if self.width > 0 and src_w > 0 and src_h > 0 and (src_w != self.width or src_h != self.height):
                arr = scale_polygon(arr, src_w, src_h, self.width, self.height).astype(np.float32)
                scaled = True
            elif self.width > 0 and self.height > 0:
                arr[:, 0] = np.clip(arr[:, 0], 0, max(0, self.width - 1))
                arr[:, 1] = np.clip(arr[:, 1], 0, max(0, self.height - 1))
            self.zone = arr.round().astype(np.int32)
            self.zone_w = self.width
            self.zone_h = self.height
            self.zone_scaled = scaled
            return scaled

    def clear_zone(self) -> None:
        with self._lock:
            self.zone = None
            self.zone_w = 0
            self.zone_h = 0
            self.zone_scaled = False

    def zone_payload(self) -> list[list[int]] | None:
        zone, _scaled = self.current_zone()
        if zone is None:
            return None
        return [[int(x), int(y)] for x, y in zone.tolist()]

    def summary(self) -> dict[str, Any]:
        _zone, scaled = self.current_zone()
        return {
            "source_id": self.id,
            "kind": self.kind,
            "width": self.width,
            "height": self.height,
            "paused": self.paused,
            "zone": self.zone_payload(),
            "zone_scaled": scaled,
            "image_url": f"/api/sources/{self.id}/snapshot",
        }

    def adopt_zone(self, points: list[list[float]] | None, src_w: int, src_h: int) -> None:
        if not points or len(points) < 3:
            return
        self.set_zone(points, src_w, src_h)

    def replace_image(self, bgr: np.ndarray) -> None:
        self.kind = "image"
        self.paused = True
        self._stop_capture()
        self.set_frame(bgr)

    def start_capture(self, source: int | str) -> None:
        cap = open_capture(source)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError("打不开视频或摄像头")
        cap.set(_cv2().CAP_PROP_BUFFERSIZE, 1)
        ok, frame = cap.read()
        if not ok or frame is None:
            cap.release()
            raise RuntimeError("读不到画面")
        self.cap = cap
        self.paused = False
        self.set_frame(frame)
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name=f"src-{self.id[:8]}", daemon=True)
        self._thread.start()

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        if self.cap is not None:
            self.paused = False

    def _loop(self) -> None:
        while not self._stop.is_set():
            if self.paused or self.cap is None:
                self._stop.wait(0.05)
                continue
            ok, frame = self.cap.read()
            if not ok or frame is None:
                if self.kind == "video" and self.cap is not None:
                    self.cap.set(_cv2().CAP_PROP_POS_FRAMES, 0)
                self._stop.wait(0.05)
                continue
            self.set_frame(frame)
            self._stop.wait(0.03)

    def _stop_capture(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        self._thread = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self._stop = threading.Event()

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.paused = True
        self._stop_capture()


class SourceRegistry:
    def __init__(self) -> None:
        self._items: dict[str, FrameSource] = {}
        self._lock = threading.Lock()

    def release_all(self) -> None:
        with self._lock:
            old = list(self._items.values())
            self._items = {}
        for src in old:
            src.close()

    def add(self, source: FrameSource) -> FrameSource:
        with self._lock:
            self._items[source.id] = source
        return source

    def get(self, source_id: str) -> FrameSource | None:
        with self._lock:
            return self._items.get(source_id)


registry = SourceRegistry()
