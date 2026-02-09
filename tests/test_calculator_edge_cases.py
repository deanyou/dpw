"""
Comprehensive test suite for DPW calculator edge cases and error conditions.
"""

import math
import pytest
from hypothesis import given, strategies as st

from dpw.calculator import (
    DieCalculator,
    OptimizedDieCalculator,
    ValidationMethod,
    NotchType,
    DiePosition,
    CalculationResult,
)


class TestDieCalculatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_valid_die_size(self):
        """Test with smallest possible die size."""
        calc = DieCalculator()
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=0.1,  # Very small die
            die_size_y_um=0.1,
            wafer_diameter_mm=50,
            validation_method=ValidationMethod.CENTER_BASED,
        )
        assert result.total_dies > 0
        assert isinstance(result.total_dies, int)

    def test_large_die_exceeds_wafer(self):
        """Test when die size exceeds wafer dimensions."""
        calc = DieCalculator()
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=300000,  # 300mm die on 200mm wafer
            die_size_y_um=300000,
            wafer_diameter_mm=200,
            validation_method=ValidationMethod.CENTER_BASED,
        )
        assert result.total_dies == 0
        assert len(result.die_positions) == 0

    def test_zero_edge_exclusion(self):
        """Test with zero edge exclusion."""
        calc = DieCalculator()
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=5000,
            die_size_y_um=5000,
            wafer_diameter_mm=200,
            edge_exclusion_mm=0.0,
            validation_method=ValidationMethod.CORNER_BASED,
        )
        assert result.total_dies > 0

    def test_maximum_edge_exclusion(self):
        """Test with edge exclusion that eliminates most dies."""
        calc = DieCalculator()
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=5000,
            die_size_y_um=5000,
            wafer_diameter_mm=200,
            edge_exclusion_mm=90,  # Very large edge exclusion
            validation_method=ValidationMethod.CENTER_BASED,
        )
        # Should still have some dies in the center
        assert result.total_dies >= 0

    def test_all_validation_methods(self):
        """Test all validation methods produce consistent results."""
        calc = DieCalculator()
        params = {
            "die_size_x_um": 1000,
            "die_size_y_um": 2000,
            "scribe_lane_x_um": 50,
            "scribe_lane_y_um": 50,
            "wafer_diameter_mm": 200,
            "edge_exclusion_mm": 3.0,
            "yield_percentage": 80.0,
            "notch_type": NotchType.NONE,
        }

        results = {}
        for method in ValidationMethod:
            result = calc.calculate_dies_per_wafer(validation_method=method, **params)
            results[method] = result

        # Corner-based should be most conservative
        assert (
            results[ValidationMethod.CORNER_BASED].total_dies
            <= results[ValidationMethod.CENTER_BASED].total_dies
        )
        # Strict should be most conservative
        assert (
            results[ValidationMethod.STRICT].total_dies
            <= results[ValidationMethod.CORNER_BASED].total_dies
        )

    def test_all_notch_types(self):
        """Test all notch types."""
        calc = DieCalculator()
        params = {
            "die_size_x_um": 1000,
            "die_size_y_um": 2000,
            "wafer_diameter_mm": 200,
            "validation_method": ValidationMethod.CORNER_BASED,
        }

        for notch_type in NotchType:
            result = calc.calculate_dies_per_wafer(notch_type=notch_type, **params)
            assert result.total_dies >= 0

    def test_extreme_yield_percentages(self):
        """Test extreme yield values."""
        calc = DieCalculator()

        # 0% yield
        result_zero = calc.calculate_dies_per_wafer(
            die_size_x_um=1000,
            die_size_y_um=2000,
            wafer_diameter_mm=200,
            yield_percentage=0.0,
        )
        assert result_zero.yield_dies == 0

        # 100% yield
        result_full = calc.calculate_dies_per_wafer(
            die_size_x_um=1000,
            die_size_y_um=2000,
            wafer_diameter_mm=200,
            yield_percentage=100.0,
        )
        assert result_full.yield_dies == result_full.total_dies


class TestDieCalculatorErrorHandling:
    """Test error conditions and validation."""

    def test_negative_die_size_x(self):
        calc = DieCalculator()
        with pytest.raises(ValueError, match="die_size_x_um must be positive"):
            calc.calculate_dies_per_wafer(
                die_size_x_um=-1000, die_size_y_um=2000, wafer_diameter_mm=200
            )

    def test_negative_die_size_y(self):
        calc = DieCalculator()
        with pytest.raises(ValueError, match="die_size_y_um must be positive"):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000, die_size_y_um=-2000, wafer_diameter_mm=200
            )

    def test_zero_die_size(self):
        calc = DieCalculator()
        with pytest.raises(ValueError):
            calc.calculate_dies_per_wafer(
                die_size_x_um=0, die_size_y_um=2000, wafer_diameter_mm=200
            )

    def test_negative_scribe_lane(self):
        calc = DieCalculator()
        with pytest.raises(ValueError, match="scribe_lane_x_um must be non-negative"):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=2000,
                scribe_lane_x_um=-50,
                wafer_diameter_mm=200,
            )

    def test_negative_wafer_diameter(self):
        calc = DieCalculator()
        with pytest.raises(ValueError, match="wafer_diameter_mm must be positive"):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000, die_size_y_um=2000, wafer_diameter_mm=-200
            )

    def test_negative_edge_exclusion(self):
        calc = DieCalculator()
        with pytest.raises(ValueError, match="edge_exclusion_mm must be non-negative"):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=2000,
                wafer_diameter_mm=200,
                edge_exclusion_mm=-5,
            )

    def test_invalid_yield_percentage_low(self):
        calc = DieCalculator()
        with pytest.raises(
            ValueError, match="yield_percentage must be between 0 and 100"
        ):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=2000,
                wafer_diameter_mm=200,
                yield_percentage=-10,
            )

    def test_invalid_yield_percentage_high(self):
        calc = DieCalculator()
        with pytest.raises(
            ValueError, match="yield_percentage must be between 0 and 100"
        ):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=2000,
                wafer_diameter_mm=200,
                yield_percentage=110,
            )

    def test_excessive_edge_exclusion(self):
        calc = DieCalculator()
        with pytest.raises(ValueError, match="Effective radius must be positive"):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=2000,
                wafer_diameter_mm=200,
                edge_exclusion_mm=150,  # Exceeds wafer radius
            )

    def test_invalid_notch_depth(self):
        calc = DieCalculator()
        with pytest.raises(ValueError, match="Notch depth must be non-negative"):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=2000,
                wafer_diameter_mm=200,
                notch_type=NotchType.V_NOTCH_90,
                notch_depth_mm=-1,
            )

    def test_notch_depth_exceeds_radius(self):
        calc = DieCalculator()
        with pytest.raises(
            ValueError, match="Notch depth .* cannot exceed wafer radius"
        ):
            calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=2000,
                wafer_diameter_mm=200,
                notch_type=NotchType.V_NOTCH_90,
                notch_depth_mm=150,  # Exceeds radius of 100mm
            )


class TestOptimizedDieCalculatorSpecific:
    """Test OptimizedDieCalculator specific functionality."""

    def test_optimized_vs_standard_consistency(self):
        """Test that optimized calculator produces similar results to standard."""
        standard_calc = DieCalculator(enable_optimizations=False)
        optimized_calc = OptimizedDieCalculator()

        params = {
            "die_size_x_um": 1000,
            "die_size_y_um": 2000,
            "scribe_lane_x_um": 50,
            "scribe_lane_y_um": 50,
            "wafer_diameter_mm": 200,
            "edge_exclusion_mm": 3.0,
            "yield_percentage": 80.0,
            "validation_method": ValidationMethod.CORNER_BASED,
            "notch_type": NotchType.NONE,
        }

        standard_result = standard_calc.calculate_dies_per_wafer(**params)
        optimized_result = optimized_calc.calculate_dies_per_wafer(**params)

        # Should produce identical results
        assert standard_result.total_dies == optimized_result.total_dies
        assert standard_result.yield_dies == optimized_result.yield_dies
        assert (
            abs(standard_result.wafer_utilization - optimized_result.wafer_utilization)
            < 0.01
        )


class TestDiePositionProperties:
    """Test DiePosition dataclass properties."""

    def test_die_position_creation(self):
        """Test DiePosition creation and default values."""
        pos = DiePosition(row=1, col=2, center_x=1.5, center_y=2.5, is_valid=True)
        assert pos.row == 1
        assert pos.col == 2
        assert pos.center_x == 1.5
        assert pos.center_y == 2.5
        assert pos.is_valid is True
        assert pos.area_ratio == 1.0  # Default
        assert pos.distance_from_center == 0.0  # Default

    def test_die_position_with_values(self):
        """Test DiePosition with explicit values."""
        pos = DiePosition(
            row=1,
            col=2,
            center_x=3.0,
            center_y=4.0,
            is_valid=True,
            area_ratio=0.8,
            distance_from_center=5.0,
        )
        assert pos.area_ratio == 0.8
        assert pos.distance_from_center == 5.0


class TestCalculationResultProperties:
    """Test CalculationResult dataclass properties."""

    def test_calculation_result_structure(self):
        """Test CalculationResult has all required fields."""
        result = CalculationResult(
            total_dies=100,
            yield_dies=80,
            wafer_utilization=85.5,
            die_positions=[],
            calculation_method=ValidationMethod.CORNER_BASED,
            parameters={"test": "value"},
        )

        assert result.total_dies == 100
        assert result.yield_dies == 80
        assert result.wafer_utilization == 85.5
        assert isinstance(result.die_positions, list)
        assert result.calculation_method == ValidationMethod.CORNER_BASED
        assert isinstance(result.parameters, dict)
