#!/usr/bin/env python3
"""
Feishu app bot callback server (no encryption, no signature verification).

Receives message events, parses plain-text `dpw` command, runs calculation locally,
and replies to the same chat.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

try:
    import requests  # type: ignore
    from fastapi import FastAPI, Request  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    requests = None  # type: ignore
    FastAPI = None  # type: ignore
    Request = None  # type: ignore

from dpw.calculator import DieCalculator, NotchType, ValidationMethod


FEISHU_BASE_URL = os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn")
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")


@dataclass(frozen=True)
class DpwCommand:
    wafer_diameter_mm: float
    die_size_x_um: float
    die_size_y_um: float
    scribe_lane_x_um: float = 0.0
    scribe_lane_y_um: float = 0.0
    edge_exclusion_mm: float = 3.0
    yield_percentage: float = 100.0
    validation_method: ValidationMethod = ValidationMethod.CORNER_BASED
    notch_type: NotchType = NotchType.NONE
    notch_depth_mm: float = 1.0


_DIE_RE = re.compile(r"^(?P<x>\d+(?:\.\d+)?)x(?P<y>\d+(?:\.\d+)?)$", re.IGNORECASE)
_PAIR_RE = re.compile(r"^(?P<x>\d+(?:\.\d+)?)x(?P<y>\d+(?:\.\d+)?)$", re.IGNORECASE)


def parse_dpw_command(text: str) -> Tuple[Optional[DpwCommand], Optional[str]]:
    """
    Parse a message like:
      dpw 200 1000x2000 scribe=50x50 edge=3 yield=80 method=corner notch=none
    """
    raw = text.strip()
    if not raw.lower().startswith("dpw"):
        return None, None

    parts = raw.split()
    if len(parts) < 3:
        return None, "用法：dpw <wafer_mm> <die_x_um>x<die_y_um> [scribe=50x50] [edge=3] [yield=80] [method=corner] [notch=none|v90|flat] [notch_depth=1.0]"

    try:
        wafer_diameter_mm = float(parts[1])
    except ValueError:
        return None, "wafer_mm 需要是数字，例如：dpw 200 1000x2000"

    die_match = _DIE_RE.match(parts[2])
    if not die_match:
        return None, "die 尺寸格式应为：<x_um>x<y_um>，例如：1000x2000"

    die_size_x_um = float(die_match.group("x"))
    die_size_y_um = float(die_match.group("y"))

    kwargs: Dict[str, Any] = {}

    for token in parts[3:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        key = key.strip().lower()
        value = value.strip()

        if key in ("scribe", "scribe_lane"):
            m = _PAIR_RE.match(value)
            if not m:
                return None, "scribe 格式应为：scribe=50x50（单位 um）"
            kwargs["scribe_lane_x_um"] = float(m.group("x"))
            kwargs["scribe_lane_y_um"] = float(m.group("y"))
        elif key in ("edge", "edge_exclusion"):
            kwargs["edge_exclusion_mm"] = float(value)
        elif key in ("yield", "yield_percentage"):
            kwargs["yield_percentage"] = float(value)
        elif key in ("method", "validation_method"):
            kwargs["validation_method"] = ValidationMethod(value.lower())
        elif key in ("notch", "notch_type"):
            kwargs["notch_type"] = NotchType(value.lower())
        elif key in ("notch_depth", "notch_depth_mm"):
            kwargs["notch_depth_mm"] = float(value)

    try:
        return (
            DpwCommand(
                wafer_diameter_mm=wafer_diameter_mm,
                die_size_x_um=die_size_x_um,
                die_size_y_um=die_size_y_um,
                **kwargs,
            ),
            None,
        )
    except Exception as e:
        return None, f"参数解析失败：{e}"


def get_tenant_access_token() -> str:
    if requests is None:  # pragma: no cover
        raise RuntimeError("Missing dependency: install extras `.[feishu]` (requests/fastapi/uvicorn)")
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        raise RuntimeError("Missing FEISHU_APP_ID / FEISHU_APP_SECRET")

    url = f"{FEISHU_BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"token error: {data}")
    return data["tenant_access_token"]


def send_text_to_chat(chat_id: str, text: str) -> None:
    if requests is None:  # pragma: no cover
        raise RuntimeError("Missing dependency: install extras `.[feishu]` (requests/fastapi/uvicorn)")
    token = get_tenant_access_token()
    url = f"{FEISHU_BASE_URL}/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"send message error: {data}")


if FastAPI is not None:
    app = FastAPI()
else:  # pragma: no cover
    app = None

calculator = DieCalculator(enable_optimizations=True)


if app is not None:

    @app.post("/feishu/callback")
    async def feishu_callback(req: Request) -> Dict[str, Any]:
        body = await req.json()

        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge")}

        event = body.get("event") or {}
        message = event.get("message") or {}
        if message.get("message_type") != "text":
            return {"ok": True}

        chat_id = message.get("chat_id")
        if not chat_id:
            return {"ok": True}

        try:
            content = json.loads(message.get("content") or "{}")
        except json.JSONDecodeError:
            return {"ok": True}

        text = (content.get("text") or "").strip()
        cmd, err = parse_dpw_command(text)
        if err:
            send_text_to_chat(chat_id, err)
            return {"ok": True}
        if cmd is None:
            return {"ok": True}

        try:
            result = calculator.calculate_dies_per_wafer(
                die_size_x_um=cmd.die_size_x_um,
                die_size_y_um=cmd.die_size_y_um,
                scribe_lane_x_um=cmd.scribe_lane_x_um,
                scribe_lane_y_um=cmd.scribe_lane_y_um,
                wafer_diameter_mm=cmd.wafer_diameter_mm,
                edge_exclusion_mm=cmd.edge_exclusion_mm,
                yield_percentage=cmd.yield_percentage,
                validation_method=cmd.validation_method,
                notch_type=cmd.notch_type,
                notch_depth_mm=cmd.notch_depth_mm,
            )

            reply = (
                f"DPW 结果：total_dies={result.total_dies}, yield_dies={result.yield_dies}, "
                f"utilization={result.wafer_utilization:.2f}%, method={result.calculation_method.value}, "
                f"notch={cmd.notch_type.value}\n"
                f"params: wafer={cmd.wafer_diameter_mm}mm die={cmd.die_size_x_um}x{cmd.die_size_y_um}um "
                f"scribe={cmd.scribe_lane_x_um}x{cmd.scribe_lane_y_um}um edge={cmd.edge_exclusion_mm}mm yield={cmd.yield_percentage}%"
            )
            send_text_to_chat(chat_id, reply)
        except Exception as e:
            send_text_to_chat(chat_id, f"计算失败：{e}")

        return {"ok": True, "ts": int(time.time())}
