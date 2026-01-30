"""
Die Per Wafer (DPW) Calculator - 独立版本

A comprehensive die per wafer calculation tool with precise counting algorithms,
professional visualization, and multiple interface options (CLI, Python API, HTTP API).

迁移自 PyEDA 项目，完全解耦并添加了飞书集成功能。
"""

from dpw.calculator import DieCalculator, WaferGeometry, ValidationMethod
from dpw.config import DPWConfig, WaferPresets
from dpw.visualizer import WaferVisualizer
from dpw.reporter import DPWHTMLReporter

__version__ = "1.0.0"
__author__ = "PyEDA Team"

__all__ = [
    "DieCalculator",
    "WaferGeometry",
    "ValidationMethod",
    "DPWConfig",
    "WaferPresets",
    "WaferVisualizer",
    "DPWHTMLReporter",
]
