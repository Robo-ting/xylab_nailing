"""长板钉位扫描：拍照、红外、选优机定级。不改选区检测接口。"""
from __future__ import annotations

import io
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel, Field

from intake.advisor import DEFAULT_PROMPT, ask_qwen, build_prompt
from intake.annotate import annotate
from intake.grader import rule_grade, visual_grade
from intake.infrared import get_infrared
from intake.session import book
from intake.vision import scan_photo

HERE = Path(__file__).resolve().parents[1]
ANNOTATED_DIR = HERE / "uploads" / "intake"
ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()
_ir = get_infrared()


class BoardBody(BaseModel):
    length_mm: float = Field(gt=0, le=20000)
    width_mm: float = Field(default=200, gt=0, le=2000)
    label: str = "长板"


class LengthBody(BaseModel):
    length_mm: float = Field(gt=0, le=20000)


class StationBody(BaseModel):
    x_mm: float = Field(ge=0)


class IrBody(BaseModel):
    simulate: bool = False


class AdviseBody(BaseModel):
    prompt: str = DEFAULT_PROMPT
    spacing_mm: float | None = None


def _board(board_id: str):
    board = book.get(board_id)
    if board is None:
        raise HTTPException(404, "这块板不存在")
    return board


def _station(board, station_id: str) -> dict:
    for station in board.stations:
        if station["id"] == station_id:
            return station
    raise HTTPException(404, "这个钉位不存在")


@router.post("/api/intake/boards")
def create_board(body: BoardBody):
    board = book.create(body.length_mm, body.width_mm, body.label)
    return board.view()


@router.get("/api/intake/boards/{board_id}")
def get_board(board_id: str):
    return _board(board_id).view()


@router.patch("/api/intake/boards/{board_id}")
def resize_board(board_id: str, body: LengthBody):
    board = _board(board_id)
    board.length_mm = body.length_mm
    board.stations = [s for s in board.stations if s["x_mm"] <= body.length_mm]
    board.ir = [h for h in board.ir if h["x_mm"] <= body.length_mm]
    board.grade = None
    return board.view()


@router.post("/api/intake/boards/{board_id}/stations")
def add_station(board_id: str, body: StationBody):
    board = _board(board_id)
    if body.x_mm > board.length_mm:
        raise HTTPException(400, "钉位超出板长")
    station = {
        "id": "N" + uuid.uuid4().hex[:4],
        "x_mm": round(float(body.x_mm), 1),
        "photo": False,
        "defects": [],
    }
    board.stations.append(station)
    board.stations.sort(key=lambda s: s["x_mm"])
    board.grade = None
    return board.view()


@router.delete("/api/intake/boards/{board_id}/stations/{station_id}")
def remove_station(board_id: str, station_id: str):
    board = _board(board_id)
    board.stations = [s for s in board.stations if s["id"] != station_id]
    board.grade = None
    return board.view()


@router.post("/api/intake/boards/{board_id}/stations/{station_id}/photo")
async def scan_station_photo(board_id: str, station_id: str, image: UploadFile = File(...)):
    board = _board(board_id)
    station = _station(board, station_id)
    raw = await image.read()
    if not raw:
        raise HTTPException(400, "空照片")
    try:
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise HTTPException(400, f"读不了这张照片: {exc}") from exc
    station["defects"] = scan_photo(pil)
    station["photo"] = True
    marked = annotate(pil, station["defects"])
    dest = ANNOTATED_DIR / f"{board.id}_{station['id']}.jpg"
    marked.save(dest, format="JPEG", quality=90)
    station["annotated_path"] = str(dest)
    station["advice"] = None
    board.grade = None
    return board.view()


@router.get("/api/intake/boards/{board_id}/stations/{station_id}/annotated")
def get_annotated(board_id: str, station_id: str):
    station = _station(_board(board_id), station_id)
    path = station.get("annotated_path")
    if not path or not Path(path).is_file():
        raise HTTPException(404, "还没有缺陷图")
    return FileResponse(path, media_type="image/jpeg")


@router.post("/api/intake/boards/{board_id}/stations/{station_id}/advise")
def advise_station(board_id: str, station_id: str, body: AdviseBody):
    board = _board(board_id)
    station = _station(board, station_id)
    path = station.get("annotated_path")
    if not path or not Path(path).is_file():
        raise HTTPException(400, "先拍照扫描这个钉位")
    with Image.open(path) as marked:
        image_size = marked.size
    prompt = build_prompt(station, body.spacing_mm, body.prompt, board.length_mm, image_size)
    try:
        station["advice"] = ask_qwen(Path(path).read_bytes(), prompt)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return board.view()


@router.post("/api/intake/boards/{board_id}/ir")
def scan_ir(board_id: str, body: IrBody):
    board = _board(board_id)
    try:
        board.ir = _ir.scan(board.length_mm, board.stations, body.simulate)
    except Exception as exc:
        raise HTTPException(503, str(exc)) from exc
    board.grade = None
    view = board.view()
    view["ir_mode"] = getattr(_ir, "mode", "stub")
    return view


@router.post("/api/intake/boards/{board_id}/grade")
def grade(board_id: str):
    board = _board(board_id)
    packet = {
        "length_mm": board.length_mm,
        "width_mm": board.width_mm,
        "stations": board.stations,
        "ir": board.ir,
    }
    image = _annotated_image(board)
    if image is None:
        board.grade = rule_grade(packet)
        board.grade["reasons"].insert(0, "还没有榉木缺陷图，只按规则兜底")
        return board.view()
    try:
        board.grade = visual_grade(packet, image)
    except RuntimeError as exc:
        board.grade = rule_grade(packet)
        board.grade["ai_error"] = str(exc)
    return board.view()


def _annotated_image(board) -> bytes | None:
    for station in board.stations:
        path = station.get("annotated_path")
        if path and Path(path).is_file():
            return Path(path).read_bytes()
    return None
