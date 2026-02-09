from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from .calculator import (
    DieCalculator,
    NotchType,
    ValidationMethod,
    OptimizedDieCalculator,
)


def _parse_pair(value: str, what: str) -> Tuple[float, float]:
    try:
        left, right = value.lower().split("x", 1)
        return float(left), float(right)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"{what} must be like AxB (e.g. 1000x2000), got: {value!r}"
        )


def _parse_kv_tokens(tokens: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for t in tokens:
        if "=" not in t:
            continue
        k, v = t.split("=", 1)
        out[k.strip().lower()] = v.strip()
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dpw", description="Die per wafer calculator (CLI)"
    )
    p.add_argument(
        "command",
        nargs="*",
        help=(
            "Quick form: <wafer_mm> <die_x_um>x<die_y_um> [scribe=50x50] [edge=3] "
            "[yield=80] [method=corner] [notch=none|v90|flat] [notch_depth=1.0]"
        ),
    )
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    return p


def run(argv: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if len(args.command) < 2:
        parser.print_help(sys.stderr)
        return 2

    wafer_raw = args.command[0]
    die_raw = args.command[1]
    kv = _parse_kv_tokens(args.command[2:])

    try:
        wafer_diameter_mm = float(wafer_raw)
        die_x_um, die_y_um = _parse_pair(die_raw, "die")
        scribe_x_um, scribe_y_um = (0.0, 0.0)
        if "scribe" in kv:
            scribe_x_um, scribe_y_um = _parse_pair(kv["scribe"], "scribe")

        edge_exclusion_mm = float(kv.get("edge", "3"))
        yield_percentage = float(kv.get("yield", "100"))
        validation_method = ValidationMethod(kv.get("method", "corner").lower())
        notch_type = NotchType(kv.get("notch", "none").lower())
        notch_depth_mm = float(kv.get("notch_depth", "1.0"))
    except Exception as e:
        print(f"dpw: bad arguments: {e}", file=sys.stderr)
        return 2

    try:
        # 使用优化版计算器
        calc = OptimizedDieCalculator()
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=die_x_um,
            die_size_y_um=die_y_um,
            scribe_lane_x_um=scribe_x_um,
            scribe_lane_y_um=scribe_y_um,
            wafer_diameter_mm=wafer_diameter_mm,
            edge_exclusion_mm=edge_exclusion_mm,
            yield_percentage=yield_percentage,
            validation_method=validation_method,
            notch_type=notch_type,
            notch_depth_mm=notch_depth_mm,
        )
    except Exception as e:
        print(f"dpw: calculation failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        payload: Dict[str, Any] = {
            "total_dies": result.total_dies,
            "yield_dies": result.yield_dies,
            "wafer_utilization": result.wafer_utilization,
            "calculation_method": result.calculation_method.value,
            "parameters": result.parameters,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    print(
        "DPW 结果："
        f"total_dies={result.total_dies}, "
        f"yield_dies={result.yield_dies}, "
        f"utilization={result.wafer_utilization:.2f}%, "
        f"method={result.calculation_method.value}, "
        f"notch={notch_type.value}"
    )
    return 0


def main() -> None:
    raise SystemExit(run(sys.argv[1:]))
