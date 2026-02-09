"""
Test configuration management and presets.
"""

import pytest
from dpw.config import (
    WaferSize,
    WaferPreset,
    WaferPresets,
    ScribeLanePresets,
    DPWParameters,
    DPWConfig,
)


class TestWaferPresets:
    """Test wafer preset functionality."""

    def test_wafer_sizes(self):
        """Test wafer size definitions."""
        # Check common wafer sizes exist
        assert WaferSize.MM_50 in WaferSize
        assert WaferSize.MM_100 in WaferSize
        assert WaferSize.MM_150 in WaferSize
        assert WaferSize.MM_200 in WaferSize
        assert WaferSize.MM_300 in WaferSize

        # Check values are reasonable
        assert WaferSize.MM_200.value == 200.0
        assert WaferSize.MM_300.value == 300.0

    def test_wafer_preset_creation(self):
        """Test wafer preset creation."""
        preset = WaferPreset(
            name="Test Wafer", size_mm=200.0, edge_exclusion_mm=3.0, notch_type="none"
        )

        assert preset.name == "Test Wafer"
        assert preset.size_mm == 200.0
        assert preset.edge_exclusion_mm == 3.0
        assert preset.notch_type == "none"

    def test_wafer_presets_collection(self):
        """Test wafer presets collection."""
        presets = WaferPresets()

        # Test getting common presets
        preset_200 = presets.get_preset(WaferSize.MM_200)
        assert preset_200.size_mm == 200.0
        assert preset_200.edge_exclusion_mm >= 0

        preset_300 = presets.get_preset(WaferSize.MM_300)
        assert preset_300.size_mm == 300.0
        assert preset_300.edge_exclusion_mm >= 0

        # Test all presets exist
        for wafer_size in WaferSize:
            preset = presets.get_preset(wafer_size)
            assert preset.size_mm == wafer_size.value
            assert preset.edge_exclusion_mm >= 0
            assert preset.notch_type in ["none", "v90", "flat"]

    def test_all_wafer_presets(self):
        """Test getting all wafer presets."""
        presets = WaferPresets()
        all_presets = presets.get_all_presets()

        assert len(all_presets) > 0

        # Should have presets for common wafer sizes
        preset_sizes = [p.size_mm for p in all_presets]
        assert 200.0 in preset_sizes
        assert 300.0 in preset_sizes


class TestScribeLanePresets:
    """Test scribe lane preset functionality."""

    def test_scribe_lane_presets_creation(self):
        """Test scribe lane presets creation."""
        presets = ScribeLanePresets()

        # Test getting common presets
        fine_preset = presets.get_preset("fine")
        assert fine_preset.name == "fine"
        assert fine_preset.width_x_um > 0
        assert fine_preset.width_y_um > 0

        standard_preset = presets.get_preset("standard")
        assert standard_preset.name == "standard"
        assert standard_preset.width_x_um > 0
        assert standard_preset.width_y_um > 0

    def test_all_scribe_lane_presets(self):
        """Test getting all scribe lane presets."""
        presets = ScribeLanePresets()
        all_presets = presets.get_all_presets()

        assert len(all_presets) >= 3  # Should have fine, standard, coarse

        # Check common presets exist
        preset_names = [p.name for p in all_presets]
        assert "fine" in preset_names
        assert "standard" in preset_names
        assert "coarse" in preset_names

        # All widths should be positive
        for preset in all_presets:
            assert preset.width_x_um >= 0
            assert preset.width_y_um >= 0


class TestDPWParameters:
    """Test DPW parameter validation and management."""

    def test_parameters_creation(self):
        """Test DPW parameters creation."""
        params = DPWParameters(
            die_size_x_um=1000.0,
            die_size_y_um=2000.0,
            wafer_diameter_mm=200.0,
            edge_exclusion_mm=3.0,
            yield_percentage=80.0,
            validation_method="corner",
            notch_type="none",
            scribe_lane_x_um=50.0,
            scribe_lane_y_um=50.0,
        )

        assert params.die_size_x_um == 1000.0
        assert params.die_size_y_um == 2000.0
        assert params.wafer_diameter_mm == 200.0
        assert params.edge_exclusion_mm == 3.0
        assert params.yield_percentage == 80.0
        assert params.validation_method == "corner"
        assert params.notch_type == "none"
        assert params.scribe_lane_x_um == 50.0
        assert params.scribe_lane_y_um == 50.0

    def test_parameters_validation(self):
        """Test parameter validation."""
        # Test valid parameters
        params = DPWParameters(
            die_size_x_um=1000.0, die_size_y_um=2000.0, wafer_diameter_mm=200.0
        )
        assert params.is_valid()

        # Test negative die size
        params = DPWParameters(
            die_size_x_um=-1000.0, die_size_y_um=2000.0, wafer_diameter_mm=200.0
        )
        assert not params.is_valid()

        # Test zero wafer diameter
        params = DPWParameters(
            die_size_x_um=1000.0, die_size_y_um=2000.0, wafer_diameter_mm=0.0
        )
        assert not params.is_valid()

    def test_parameters_to_dict(self):
        """Test parameter conversion to dictionary."""
        params = DPWParameters(
            die_size_x_um=1000.0, die_size_y_um=2000.0, wafer_diameter_mm=200.0
        )

        param_dict = params.to_dict()

        assert isinstance(param_dict, dict)
        assert param_dict["die_size_x_um"] == 1000.0
        assert param_dict["die_size_y_um"] == 2000.0
        assert param_dict["wafer_diameter_mm"] == 200.0

    def test_parameters_from_dict(self):
        """Test parameter creation from dictionary."""
        param_dict = {
            "die_size_x_um": 1000.0,
            "die_size_y_um": 2000.0,
            "wafer_diameter_mm": 200.0,
            "edge_exclusion_mm": 3.0,
            "yield_percentage": 80.0,
        }

        params = DPWParameters.from_dict(param_dict)

        assert params.die_size_x_um == 1000.0
        assert params.die_size_y_um == 2000.0
        assert params.wafer_diameter_mm == 200.0
        assert params.edge_exclusion_mm == 3.0
        assert params.yield_percentage == 80.0


class TestDPWConfig:
    """Test DPW configuration management."""

    def test_config_creation(self):
        """Test configuration creation."""
        wafer_presets = WaferPresets()
        scribe_presets = ScribeLanePresets()

        config = DPWConfig(
            wafer_presets=wafer_presets, scribe_lane_presets=scribe_presets
        )

        assert config.wafer_presets is wafer_presets
        assert config.scribe_lane_presets is scribe_presets

    def test_get_wafer_preset(self):
        """Test getting wafer preset from config."""
        config = DPWConfig()

        preset = config.get_wafer_preset(WaferSize.MM_200)
        assert preset.size_mm == 200.0
        assert preset.edge_exclusion_mm >= 0

    def test_get_scribe_lane_preset(self):
        """Test getting scribe lane preset from config."""
        config = DPWConfig()

        preset = config.get_scribe_lane_preset("standard")
        assert preset.name == "standard"
        assert preset.width_x_um > 0
        assert preset.width_y_um > 0

    def test_create_parameters_from_presets(self):
        """Test creating parameters from presets."""
        config = DPWConfig()

        params = config.create_parameters_from_presets(
            wafer_size=WaferSize.MM_200,
            scribe_lane_type="standard",
            die_size_x_um=1000.0,
            die_size_y_um=2000.0,
        )

        assert params.wafer_diameter_mm == 200.0
        assert params.die_size_x_um == 1000.0
        assert params.die_size_y_um == 2000.0

        # Should inherit from presets
        wafer_preset = config.get_wafer_preset(WaferSize.MM_200)
        scribe_preset = config.get_scribe_lane_preset("standard")

        assert params.edge_exclusion_mm == wafer_preset.edge_exclusion_mm
        assert params.notch_type == wafer_preset.notch_type
        assert params.scribe_lane_x_um == scribe_preset.width_x_um
        assert params.scribe_lane_y_um == scribe_preset.width_y_um

    def test_validate_parameters(self):
        """Test parameter validation in config."""
        config = DPWConfig()

        # Test valid parameters
        valid_params = DPWParameters(
            die_size_x_um=1000.0, die_size_y_um=2000.0, wafer_diameter_mm=200.0
        )

        errors = config.validate_parameters(valid_params)
        assert len(errors) == 0

        # Test invalid parameters
        invalid_params = DPWParameters(
            die_size_x_um=-1000.0,  # Invalid
            die_size_y_um=2000.0,
            wafer_diameter_mm=200.0,
            yield_percentage=150.0,  # Invalid
        )

        errors = config.validate_parameters(invalid_params)
        assert len(errors) > 0
        assert any("die_size_x_um" in error for error in errors)
        assert any("yield_percentage" in error for error in errors)


class TestConfigurationEdgeCases:
    """Test configuration edge cases and error handling."""

    def test_unknown_wafer_preset(self):
        """Test handling of unknown wafer presets."""
        config = DPWConfig()

        # This should use a default or raise an error
        with pytest.raises((KeyError, ValueError)):
            config.get_wafer_preset("unknown")

    def test_unknown_scribe_lane_preset(self):
        """Test handling of unknown scribe lane presets."""
        config = DPWConfig()

        # This should use a default or raise an error
        with pytest.raises((KeyError, ValueError)):
            config.get_scribe_lane_preset("unknown")

    def test_extreme_parameter_values(self):
        """Test configuration with extreme parameter values."""
        config = DPWConfig()

        # Very small die
        params = DPWParameters(
            die_size_x_um=0.1, die_size_y_um=0.1, wafer_diameter_mm=50.0
        )
        errors = config.validate_parameters(params)
        assert len(errors) == 0  # Should be valid

        # Very large wafer
        params = DPWParameters(
            die_size_x_um=10000.0, die_size_y_um=10000.0, wafer_diameter_mm=300.0
        )
        errors = config.validate_parameters(params)
        assert len(errors) == 0  # Should be valid

    def test_configuration_serialization(self):
        """Test configuration serialization and deserialization."""
        config = DPWConfig()

        # Create parameters
        params = config.create_parameters_from_presets(
            wafer_size=WaferSize.MM_200,
            scribe_lane_type="standard",
            die_size_x_um=1000.0,
            die_size_y_um=2000.0,
        )

        # Serialize to dict
        param_dict = params.to_dict()

        # Deserialize
        new_params = DPWParameters.from_dict(param_dict)

        # Should be equivalent
        assert new_params.die_size_x_um == params.die_size_x_um
        assert new_params.die_size_y_um == params.die_size_y_um
        assert new_params.wafer_diameter_mm == params.wafer_diameter_mm
