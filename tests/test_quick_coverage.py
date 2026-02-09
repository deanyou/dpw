"""
Quick coverage tests for essential calculator functions.
"""

import pytest
from dpw.calculator import (
    OptimizedDieCalculator,
    ValidationMethod,
    NotchType,
    OptimizedWaferGeometry,
    DiePosition,
    CalculationResult,
)


def test_calculator_basic_functionality():
    """Test basic calculator functionality for coverage."""
    calc = OptimizedDieCalculator()

    result = calc.calculate_dies_per_wafer(
        die_size_x_um=1000,
        die_size_y_um=2000,
        scribe_lane_x_um=50,
        scribe_lane_y_um=50,
        wafer_diameter_mm=200,
        validation_method=ValidationMethod.CORNER_BASED,
    )

    assert result.total_dies > 0
    assert result.yield_dies == result.total_dies  # Default 100% yield


def test_wafer_geometry_methods():
    """Test wafer geometry methods for coverage."""
    geometry = OptimizedWaferGeometry(200.0)

    # Test basic point checking
    assert geometry.is_point_in_wafer(0, 0)
    assert geometry.is_point_in_wafer(50, 50)
    assert not geometry.is_point_in_wafer(150, 150)

    # Test boundary
    assert geometry.is_point_in_wafer(100, 0)
    assert not geometry.is_point_in_wafer(101, 0)


def test_all_validation_methods():
    """Test all validation methods quickly."""
    calc = OptimizedDieCalculator()

    for method in [ValidationMethod.CENTER_BASED, ValidationMethod.CORNER_BASED]:
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=2000,
            die_size_y_um=2000,
            scribe_lane_x_um=50,
            scribe_lane_y_um=50,
            wafer_diameter_mm=200,
            validation_method=method,
        )
        assert result.total_dies >= 0


def test_notch_types():
    """Test different notch types."""
    geometry_v = OptimizedWaferGeometry(
        200.0, notch_type=NotchType.V_NOTCH_90, notch_depth_mm=1.0
    )
    geometry_f = OptimizedWaferGeometry(
        200.0, notch_type=NotchType.FLAT, notch_depth_mm=1.0
    )

    assert geometry_v.notch_area_mm2 == 1.0
    assert geometry_f.notch_area_mm2 > 0
