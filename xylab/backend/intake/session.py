"""一块长板的钉位、照片和红外结果。只存在内存里，重启进程后清空。"""
from __future__ import annotations

import threading
import uuid
from typing import Any


class BoardRecord:
    def __init__(self, length_mm: float, width_mm: float, label: str):
        self.id = uuid.uuid4().hex[:12]
        self.length_mm = float(length_mm)
        self.width_mm = float(width_mm)
        self.label = label or "长板"
        self.stations: list[dict[str, Any]] = []
        self.ir: list[dict[str, Any]] = []
        self.grade: dict[str, Any] | None = None

    def view(self) -> dict[str, Any]:
        stations = []
        for station in self.stations:
            item = {key: value for key, value in station.items() if key != "annotated_path"}
            item["has_annotated"] = bool(station.get("annotated_path"))
            stations.append(item)
        return {
            "id": self.id,
            "length_mm": self.length_mm,
            "width_mm": self.width_mm,
            "label": self.label,
            "stations": stations,
            "ir": self.ir,
            "grade": self.grade,
        }


class IntakeBook:
    def __init__(self) -> None:
        self._boards: dict[str, BoardRecord] = {}
        self._lock = threading.Lock()

    def create(self, length_mm: float, width_mm: float, label: str) -> BoardRecord:
        board = BoardRecord(length_mm, width_mm, label)
        with self._lock:
            self._boards[board.id] = board
        return board

    def get(self, board_id: str) -> BoardRecord | None:
        with self._lock:
            return self._boards.get(board_id)


book = IntakeBook()
