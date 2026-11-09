# -*- coding: utf-8 -*-
"""兼容入口。实现已归到 inference.detector。"""
from inference.detector import (
    DEMO_FIXED_DEFECTS,
    DEMO_IMAGE_SIZE,
    DEMO_NAILABLE_REGION,
    DemoFixedDetector,
    Detector,
    get_demo_defects,
    get_demo_nailable_region,
    get_demo_plan_scale,
    get_detector,
)

__all__ = [
    "DEMO_FIXED_DEFECTS",
    "DEMO_IMAGE_SIZE",
    "DEMO_NAILABLE_REGION",
    "DemoFixedDetector",
    "Detector",
    "get_demo_defects",
    "get_demo_nailable_region",
    "get_demo_plan_scale",
    "get_detector",
]
