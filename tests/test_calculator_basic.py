import math

import pytest

from dpw.calculator import DieCalculator, NotchType, ValidationMethod


def test_calculate_dies_per_wafer_smoke():
    calculator = DieCalculator(enable_optimizations=True)
    result = calculator.calculate_dies_per_wafer(
        die_size_x_um=1000,
        die_size_y_um=2000,
        scribe_lane_x_um=50,
        scribe_lane_y_um=50,
        wafer_diameter_mm=200,
        edge_exclusion_mm=3.0,
        yield_percentage=80.0,
        validation_method=ValidationMethod.CORNER_BASED,
        notch_type=NotchType.NONE,
    )

    assert result.total_dies > 0
    assert result.yield_dies == int(result.total_dies * 0.8)
    assert 0.0 <= result.wafer_utilization <= 100.0
    assert result.calculation_method == ValidationMethod.CORNER_BASED
    assert isinstance(result.die_positions, list)
    assert len(result.die_positions) > 0


def test_notch_reduces_or_keeps_die_count():
    calculator = DieCalculator(enable_optimizations=True)
    base = calculator.calculate_dies_per_wafer(
        die_size_x_um=1000,
        die_size_y_um=2000,
        scribe_lane_x_um=50,
        scribe_lane_y_um=50,
        wafer_diameter_mm=200,
        edge_exclusion_mm=0.0,
        yield_percentage=100.0,
        validation_method=ValidationMethod.CORNER_BASED,
        notch_type=NotchType.NONE,
    )
    with_notch = calculator.calculate_dies_per_wafer(
        die_size_x_um=1000,
        die_size_y_um=2000,
        scribe_lane_x_um=50,
        scribe_lane_y_um=50,
        wafer_diameter_mm=200,
        edge_exclusion_mm=0.0,
        yield_percentage=100.0,
        validation_method=ValidationMethod.CORNER_BASED,
        notch_type=NotchType.V_NOTCH_90,
        notch_depth_mm=1.0,
    )

    assert with_notch.total_dies <= base.total_dies


def test_invalid_inputs_raise():
    calculator = DieCalculator()
    with pytest.raises(ValueError):
        calculator.calculate_dies_per_wafer(
            die_size_x_um=-1,
            die_size_y_um=2000,
            scribe_lane_x_um=50,
            scribe_lane_y_um=50,
            wafer_diameter_mm=200,
        )


def test_positions_distance_matches_center():
    calculator = DieCalculator(enable_optimizations=False)
    result = calculator.calculate_dies_per_wafer(
        die_size_x_um=1000,
        die_size_y_um=1000,
        scribe_lane_x_um=0,
        scribe_lane_y_um=0,
        wafer_diameter_mm=100,
        edge_exclusion_mm=0.0,
        yield_percentage=100.0,
        validation_method=ValidationMethod.CENTER_BASED,
    )
    sample = result.die_positions[len(result.die_positions) // 2]
    assert sample.distance_from_center == pytest.approx(math.hypot(sample.center_x, sample.center_y))

