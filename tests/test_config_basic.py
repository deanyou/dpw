"""
Basic configuration tests to improve coverage.
"""

import pytest
from dpw.config import (
    WaferSize,
    WaferPreset,
    ScribeLanePresets,
    DPWParameters,
    DPWConfig,
)


class TestBasicConfig:
    """Basic configuration tests for coverage."""

    def test_wafer_size_enum(self):
        """Test WaferSize enum functionality."""
        # Test inch sizes
        assert WaferSize.INCH_4.inches == 4
        assert WaferSize.INCH_4.mm == 100

        assert WaferSize.INCH_6.inches == 6
        assert WaferSize.INCH_6.mm == 150

        assert WaferSize.INCH_8.inches == 8
        assert WaferSize.INCH_8.mm == 200

        assert WaferSize.INCH_12.inches == 12
        assert WaferSize.INCH_12.mm == 300

        # Test from_inches
        wafer_6 = WaferSize.from_inches(6)
        assert wafer_6.mm == 150

        wafer_12 = WaferSize.from_inches(12)
        assert wafer_12.mm == 300

        # Test from_mm
        wafer_200 = WaferSize.from_mm(200)
        assert wafer_200.inches == 8

        wafer_300 = WaferSize.from_mm(300)
        assert wafer_300.inches == 12

        # Test invalid inputs
        with pytest.raises(ValueError):
            WaferSize.from_inches(10)  # Not supported

        with pytest.raises(ValueError):
            WaferSize.from_mm(250)  # Not supported


def test_wafer_preset():
    """Test WaferPreset dataclass."""
    from dpw.config import WaferPresets

    preset = WaferPreset(
        name="Test",
        size=WaferSize.INCH_8,
        edge_exclusion_mm=3.0,
        description="Test wafer",
    )

    assert preset.name == "Test"
    assert preset.size == WaferSize.INCH_8
    assert preset.edge_exclusion_mm == 3.0
    assert preset.description == "Test wafer"

    # Test preset collection
    preset_8inch = WaferPresets.get_preset("8inch_mainstream")
    assert preset_8inch.size == WaferSize.INCH_8
    assert preset_8inch.edge_exclusion_mm == 3.0


def test_scribe_lane_presets():
    """Test ScribeLanePresets functionality."""
    # Test getting presets
    minimal_preset = ScribeLanePresets.get_preset("minimal")
    assert minimal_preset["x"] == 20
    assert minimal_preset["y"] == 20

    standard_preset = ScribeLanePresets.get_preset("standard")
    assert standard_preset["x"] == 50
    assert standard_preset["y"] == 50

    wide_preset = ScribeLanePresets.get_preset("wide")
    assert wide_preset["x"] == 80
    assert wide_preset["y"] == 80

    # Test all preset names
    available_presets = ScribeLanePresets.PRESETS.keys()
    assert "minimal" in available_presets
    assert "standard" in available_presets
    assert "wide" in available_presets
    assert "test" in available_presets
    assert "asymmetric" in available_presets


def test_dpw_parameters():
    """Test DPWParameters functionality."""
    # Test basic creation
    params = DPWParameters(
        die_size_x_um=1000.0,
        die_size_y_um=2000.0,
        scribe_lane_x_um=50.0,
        scribe_lane_y_um=50.0,
        wafer_diameter_mm=200.0,
    )

    assert params.die_size_x_um == 1000.0
    assert params.die_size_y_um == 2000.0
    assert params.scribe_lane_x_um == 50.0
    assert params.scribe_lane_y_um == 50.0
    assert params.wafer_diameter_mm == 200.0


def test_dpw_config():
    """Test DPWConfig functionality."""
    config = DPWConfig()

    # Test basic config creation
    assert config is not None
