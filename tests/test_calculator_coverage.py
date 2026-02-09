"""
Additional tests to improve calculator coverage.
"""

import pytest
from dpw.calculator import (
    DieCalculator,
    OptimizedDieCalculator,
    ValidationMethod,
    NotchType,
    OptimizedWaferGeometry,
    DiePosition,
    CalculationResult,
)


class TestCalculatorCoverage:
    """Additional tests to improve calculator coverage."""

    def test_optimized_calculator_edge_cases(self):
        """Test OptimizedDieCalculator edge cases for coverage."""
        calc = OptimizedDieCalculator()

        # Test with extreme small values
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=0.1,
            die_size_y_um=0.1,
            wafer_diameter_mm=50,
            scribe_lane_x_um=0,
            scribe_lane_y_um=0,
            edge_exclusion_mm=0,
            validation_method=ValidationMethod.CENTER_BASED,
        )
        assert result.total_dies >= 0

        # Test with large scribe lanes
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=1000,
            die_size_y_um=1000,
            wafer_diameter_mm=200,
            scribe_lane_x_um=500,  # Large scribe lane
            scribe_lane_y_um=500,
            edge_exclusion_mm=0,
            validation_method=ValidationMethod.CENTER_BASED,
        )
        assert result.total_dies >= 0

    def test_optimized_wafer_geometry(self):
        """Test OptimizedWaferGeometry class for coverage."""

        # Test with different notch types
        geometry_none = OptimizedWaferGeometry(
            wafer_diameter_mm=200, notch_type=NotchType.NONE
        )
        assert geometry_none.notch_area_mm2 == 0.0

        geometry_v90 = OptimizedWaferGeometry(
            wafer_diameter_mm=200, notch_type=NotchType.V_NOTCH_90, notch_depth_mm=2.0
        )
        assert geometry_v90.notch_area_mm2 == 4.0  # 2²

        geometry_flat = OptimizedWaferGeometry(
            wafer_diameter_mm=200, notch_type=NotchType.FLAT, notch_depth_mm=1.0
        )
        assert geometry_flat.notch_area_mm2 > 0

        # Test point checking
        assert geometry_none.is_point_in_wafer(0, 0)  # Center point
        assert geometry_none.is_point_in_wafer(50, 50)  # Inside point
        assert not geometry_none.is_point_in_wafer(150, 150)  # Outside point

        # Test boundary cases
        assert geometry_none.is_point_in_wafer(100, 0)  # On boundary
        assert not geometry_none.is_point_in_wafer(100.1, 0)  # Just outside

    def test_validation_methods_coverage(self):
        """Test all validation methods for coverage."""
        calc = OptimizedDieCalculator()

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

        # Test each validation method
        for method in ValidationMethod:
            result = calc.calculate_dies_per_wafer(validation_method=method, **params)
            assert result.calculation_method == method
            assert result.total_dies >= 0

    def test_die_position_variations(self):
        """Test DiePosition with different values."""

        # Test with all parameters
        pos = DiePosition(
            row=5,
            col=10,
            center_x=15.5,
            center_y=25.5,
            is_valid=True,
            area_ratio=0.75,
            distance_from_center=30.0,
        )
        assert pos.row == 5
        assert pos.col == 10
        assert pos.center_x == 15.5
        assert pos.center_y == 25.5
        assert pos.is_valid is True
        assert pos.area_ratio == 0.75
        assert pos.distance_from_center == 30.0

        # Test with defaults
        pos_default = DiePosition(
            row=1, col=1, center_x=0.0, center_y=0.0, is_valid=False
        )
        assert pos_default.area_ratio == 1.0
        assert pos_default.distance_from_center == 0.0

    def test_calculation_result_structure(self):
        """Test CalculationResult structure."""

        positions = [
            DiePosition(row=0, col=0, center_x=0, center_y=0, is_valid=True),
            DiePosition(row=0, col=1, center_x=1, center_y=0, is_valid=True),
        ]

        result = CalculationResult(
            total_dies=2,
            yield_dies=1,
            wafer_utilization=50.0,
            die_positions=positions,
            calculation_method=ValidationMethod.CORNER_BASED,
            parameters={"test": "value"},
        )

        assert result.total_dies == 2
        assert result.yield_dies == 1
        assert result.wafer_utilization == 50.0
        assert len(result.die_positions) == 2
        assert result.calculation_method == ValidationMethod.CORNER_BASED
        assert result.parameters["test"] == "value"

    def test_calculator_with_different_wafer_sizes(self):
        """Test calculator with different wafer sizes."""
        calc = OptimizedDieCalculator()

        wafer_sizes = [50, 100, 150, 200, 300]

        for size in wafer_sizes:
            result = calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=1000,
                wafer_diameter_mm=size,
                validation_method=ValidationMethod.CENTER_BASED,
            )
            assert result.total_dies >= 0
            assert result.parameters["wafer_diameter_mm"] == size

    def test_notch_depth_variations(self):
        """Test different notch depth values."""
        calc = OptimizedDieCalculator()

        # Test with different notch depths
        for depth in [0.5, 1.0, 2.0, 5.0]:
            result = calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=1000,
                wafer_diameter_mm=200,
                notch_type=NotchType.V_NOTCH_90,
                notch_depth_mm=depth,
                validation_method=ValidationMethod.CENTER_BASED,
            )
            assert result.total_dies >= 0

    def test_yield_percentage_variations(self):
        """Test different yield percentages."""
        calc = OptimizedDieCalculator()

        yield_values = [0, 25, 50, 75, 100]

        for yield_pct in yield_values:
            result = calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=1000,
                wafer_diameter_mm=200,
                yield_percentage=yield_pct,
                validation_method=ValidationMethod.CENTER_BASED,
            )
            expected_yield = int(result.total_dies * yield_pct / 100.0)
            assert result.yield_dies == expected_yield

    def test_edge_exclusion_variations(self):
        """Test different edge exclusion values."""
        calc = OptimizedDieCalculator()

        edge_values = [0, 1, 3, 5, 10]

        for edge_exclusion in edge_values:
            result = calc.calculate_dies_per_wafer(
                die_size_x_um=1000,
                die_size_y_um=1000,
                wafer_diameter_mm=200,
                edge_exclusion_mm=edge_exclusion,
                validation_method=ValidationMethod.CENTER_BASED,
            )
            assert result.total_dies >= 0
            assert result.parameters["edge_exclusion_mm"] == edge_exclusion
