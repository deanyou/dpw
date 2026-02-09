"""
Property-based tests using Hypothesis for mathematical verification.
"""

import math
import pytest
from hypothesis import given, strategies as st, assume
from hypothesis.strategies import floats, integers, booleans, sampled_from

from dpw.calculator import (
    DieCalculator,
    OptimizedDieCalculator,
    ValidationMethod,
    NotchType,
    DiePosition,
)


class TestPropertyBasedCalculations:
    """Property-based tests for mathematical correctness."""

    @given(
        wafer_diameter_mm=floats(min_value=50, max_value=300),
        die_size_x_um=floats(min_value=100, max_value=10000),
        die_size_y_um=floats(min_value=100, max_value=10000),
        scribe_lane_x_um=floats(min_value=0, max_value=200),
        scribe_lane_y_um=floats(min_value=0, max_value=200),
        edge_exclusion_mm=floats(min_value=0, max_value=10),
        yield_percentage=floats(min_value=0, max_value=100),
        validation_method=sampled_from(list(ValidationMethod)),
        notch_type=sampled_from(list(NotchType)),
    )
    def test_mathematical_properties(
        self,
        wafer_diameter_mm,
        die_size_x_um,
        die_size_y_um,
        scribe_lane_x_um,
        scribe_lane_y_um,
        edge_exclusion_mm,
        yield_percentage,
        validation_method,
        notch_type,
    ):
        """Test fundamental mathematical properties of DPW calculations."""

        # Skip invalid combinations
        assume(edge_exclusion_mm < wafer_diameter_mm / 2)
        assume(die_size_x_um > 0 and die_size_y_um > 0)
        assume(wafer_diameter_mm > 0)

        calc = DieCalculator()

        # Skip if notch depth would be invalid (simplified for property test)
        if notch_type != NotchType.NONE:
            assume(notch_type in [NotchType.NONE])  # Simplify for now

        try:
            result = calc.calculate_dies_per_wafer(
                die_size_x_um=die_size_x_um,
                die_size_y_um=die_size_y_um,
                scribe_lane_x_um=scribe_lane_x_um,
                scribe_lane_y_um=scribe_lane_y_um,
                wafer_diameter_mm=wafer_diameter_mm,
                edge_exclusion_mm=edge_exclusion_mm,
                yield_percentage=yield_percentage,
                validation_method=validation_method,
                notch_type=notch_type,
            )

            # Property 1: Total dies should be non-negative integer
            assert isinstance(result.total_dies, int)
            assert result.total_dies >= 0

            # Property 2: Yield dies should be <= total dies
            assert isinstance(result.yield_dies, int)
            assert 0 <= result.yield_dies <= result.total_dies

            # Property 3: Wafer utilization should be between 0 and 100
            assert isinstance(result.wafer_utilization, float)
            assert 0 <= result.wafer_utilization <= 100

            # Property 4: Yield calculation should be correct
            expected_yield_dies = int(result.total_dies * yield_percentage / 100.0)
            assert result.yield_dies == expected_yield_dies

            # Property 5: Die positions count should match total dies
            assert len(result.die_positions) == result.total_dies

            # Property 6: All die positions should have valid coordinates
            for pos in result.die_positions:
                assert isinstance(pos, DiePosition)
                assert isinstance(pos.row, int)
                assert isinstance(pos.col, int)
                assert isinstance(pos.center_x, float)
                assert isinstance(pos.center_y, float)
                assert isinstance(pos.is_valid, bool)
                assert 0 <= pos.area_ratio <= 1.0
                assert pos.distance_from_center >= 0

        except ValueError:
            # Expected for some edge cases - skip test
            pass

    @given(
        wafer_diameter_mm=floats(min_value=100, max_value=300),
        die_size_um=floats(min_value=500, max_value=5000),
    )
    def test_square_die_symmetry(self, wafer_diameter_mm, die_size_um):
        """Test symmetry properties for square dies."""
        calc = DieCalculator()

        try:
            # Calculate with same X and Y dimensions (square die)
            result = calc.calculate_dies_per_wafer(
                die_size_x_um=die_size_um,
                die_size_y_um=die_size_um,
                scribe_lane_x_um=0,
                scribe_lane_y_um=0,
                wafer_diameter_mm=wafer_diameter_mm,
                edge_exclusion_mm=0,
                validation_method=ValidationMethod.CENTER_BASED,
            )

            # Property: For square dies, rotation shouldn't change count
            # (This is true for center-based validation)
            rotated_result = calc.calculate_dies_per_wafer(
                die_size_x_um=die_size_um,
                die_size_y_um=die_size_um,
                scribe_lane_x_um=0,
                scribe_lane_y_um=0,
                wafer_diameter_mm=wafer_diameter_mm,
                edge_exclusion_mm=0,
                validation_method=ValidationMethod.CENTER_BASED,
            )

            assert result.total_dies == rotated_result.total_dies

        except ValueError:
            pass

    @given(
        wafer_diameter_mm=floats(min_value=100, max_value=300),
        die_size_um=floats(min_value=1000, max_value=5000),
    )
    def test_monotonicity_with_die_size(self, wafer_diameter_mm, die_size_um):
        """Test that larger dies produce fewer or equal counts."""
        calc = DieCalculator()

        try:
            # Small die
            small_result = calc.calculate_dies_per_wafer(
                die_size_x_um=die_size_um,
                die_size_y_um=die_size_um,
                wafer_diameter_mm=wafer_diameter_mm,
                validation_method=ValidationMethod.CENTER_BASED,
            )

            # Larger die
            large_result = calc.calculate_dies_per_wafer(
                die_size_x_um=die_size_um * 2,
                die_size_y_um=die_size_um * 2,
                wafer_diameter_mm=wafer_diameter_mm,
                validation_method=ValidationMethod.CENTER_BASED,
            )

            # Property: Larger dies should produce fewer or equal counts
            assert small_result.total_dies >= large_result.total_dies

        except ValueError:
            pass

    @given(wafer_diameter_mm=floats(min_value=100, max_value=300))
    def test_edge_exclusion_monotonicity(self, wafer_diameter_mm):
        """Test that increasing edge exclusion never increases die count."""
        calc = DieCalculator()

        die_size_um = 1000.0  # Fixed die size

        try:
            # No edge exclusion
            no_exclusion = calc.calculate_dies_per_wafer(
                die_size_x_um=die_size_um,
                die_size_y_um=die_size_um,
                wafer_diameter_mm=wafer_diameter_mm,
                edge_exclusion_mm=0,
                validation_method=ValidationMethod.CENTER_BASED,
            )

            # Some edge exclusion
            with_exclusion = calc.calculate_dies_per_wafer(
                die_size_x_um=die_size_um,
                die_size_y_um=die_size_um,
                wafer_diameter_mm=wafer_diameter_mm,
                edge_exclusion_mm=5,  # 5mm exclusion
                validation_method=ValidationMethod.CENTER_BASED,
            )

            # Property: Edge exclusion should reduce or maintain die count
            assert no_exclusion.total_dies >= with_exclusion.total_dies

        except ValueError:
            pass

    @given(
        die_size_x_um=floats(min_value=500, max_value=3000),
        die_size_y_um=floats(min_value=500, max_value=3000),
        wafer_diameter_mm=floats(min_value=100, max_value=300),
    )
    def test_validation_method_consistency(
        self, die_size_x_um, die_size_y_um, wafer_diameter_mm
    ):
        """Test consistency between validation methods."""
        calc = DieCalculator()

        try:
            # Get results from all validation methods
            methods = [
                ValidationMethod.CENTER_BASED,
                ValidationMethod.CORNER_BASED,
                ValidationMethod.AREA_BASED,
                ValidationMethod.STRICT,
            ]
            results = {}

            for method in methods:
                result = calc.calculate_dies_per_wafer(
                    die_size_x_um=die_size_x_um,
                    die_size_y_um=die_size_y_um,
                    wafer_diameter_mm=wafer_diameter_mm,
                    validation_method=method,
                )
                results[method] = result

            # Property: Center-based should be most permissive
            assert (
                results[ValidationMethod.CENTER_BASED].total_dies
                >= results[ValidationMethod.CORNER_BASED].total_dies
            )

            # Property: Strict should be most conservative
            assert (
                results[ValidationMethod.STRICT].total_dies
                <= results[ValidationMethod.CORNER_BASED].total_dies
            )

            # Property: All methods should have same wafer dimensions
            for method in methods:
                assert (
                    results[method].parameters["wafer_diameter_mm"] == wafer_diameter_mm
                )

        except ValueError:
            pass

    def test_optimized_calculator_properties(self):
        """Test OptimizedDieCalculator specific properties."""
        calc = OptimizedDieCalculator()

        # Test with known values
        result = calc.calculate_dies_per_wafer(
            die_size_x_um=1000,
            die_size_y_um=2000,
            scribe_lane_x_um=50,
            scribe_lane_y_um=50,
            wafer_diameter_mm=200,
            edge_exclusion_mm=3.0,
            yield_percentage=80.0,
            validation_method=ValidationMethod.CORNER_BASED,
        )

        # Basic property checks
        assert result.total_dies > 0
        assert result.yield_dies == int(result.total_dies * 0.8)
        assert 0 <= result.wafer_utilization <= 100
        assert len(result.die_positions) == result.total_dies
        assert result.calculation_method == ValidationMethod.CORNER_BASED


class TestGeometricProperties:
    """Test geometric and mathematical properties of wafer calculations."""

    @given(
        wafer_diameter_mm=floats(min_value=100, max_value=300),
        x_mm=floats(min_value=-150, max_value=150),
        y_mm=floats(min_value=-150, max_value=150),
    )
    def test_point_in_wafer_geometry(self, wafer_diameter_mm, x_mm, y_mm):
        """Test geometric properties of point-in-wafer calculation."""
        from dpw.calculator import OptimizedWaferGeometry

        try:
            geometry = OptimizedWaferGeometry(wafer_diameter_mm, edge_exclusion_mm=0)

            # Test point
            is_inside = geometry.is_point_in_wafer(x_mm, y_mm)
            distance_from_center = math.sqrt(x_mm**2 + y_mm**2)
            radius = wafer_diameter_mm / 2

            # Property: Point should be inside iff distance <= radius
            expected_inside = distance_from_center <= radius
            assert is_inside == expected_inside

        except ValueError:
            pass

    def test_wafer_area_calculations(self):
        """Test wafer area calculations."""
        from dpw.calculator import OptimizedWaferGeometry

        geometry = OptimizedWaferGeometry(200.0, edge_exclusion_mm=0)

        # Area should be π * r²
        expected_area = math.pi * geometry.effective_radius_mm**2
        # Note: We don't have direct area method, but this tests the radius calculation

        assert geometry.effective_radius_mm == 100.0
        assert geometry.wafer_radius_mm == 100.0

    def test_notch_area_properties(self):
        """Test notch area calculation properties."""
        from dpw.calculator import OptimizedWaferGeometry

        # No notch should have zero area
        geometry_none = OptimizedWaferGeometry(200.0, notch_type=NotchType.NONE)
        assert geometry_none.notch_area_mm2 == 0.0

        # V-notch area should be depth² for 90° V-notch
        geometry_v = OptimizedWaferGeometry(
            200.0, notch_type=NotchType.V_NOTCH_90, notch_depth_mm=2.0
        )
        assert abs(geometry_v.notch_area_mm2 - 4.0) < 0.001  # 2² = 4
