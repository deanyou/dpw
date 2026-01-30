"""
DPW Configuration Management

Handles configuration validation, wafer presets, and parameter management
for the Die Per Wafer calculation tool.
"""

import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from dpw.calculator import ValidationMethod, NotchType

logger = logging.getLogger(__name__)


class WaferSize(Enum):
    """Standard wafer sizes in inches and millimeters."""
    INCH_4 = (4, 100)      # 4-inch wafer, 100mm diameter
    INCH_6 = (6, 150)      # 6-inch wafer, 150mm diameter  
    INCH_8 = (8, 200)      # 8-inch wafer, 200mm diameter
    INCH_12 = (12, 300)    # 12-inch wafer, 300mm diameter
    
    def __init__(self, inches: int, mm: int):
        self.inches = inches
        self.mm = mm
    
    @classmethod
    def from_inches(cls, inches: int) -> 'WaferSize':
        """Get wafer size from inch specification."""
        for size in cls:
            if size.inches == inches:
                return size
        raise ValueError(f"Unsupported wafer size: {inches} inches")
    
    @classmethod
    def from_mm(cls, mm: int) -> 'WaferSize':
        """Get wafer size from millimeter specification."""
        for size in cls:
            if size.mm == mm:
                return size
        raise ValueError(f"Unsupported wafer size: {mm} mm")


@dataclass
class WaferPreset:
    """Predefined wafer configuration preset."""
    name: str
    size: WaferSize
    edge_exclusion_mm: float
    description: str
    typical_applications: List[str] = field(default_factory=list)


class WaferPresets:
    """Collection of industry-standard wafer presets."""
    
    PRESETS = {
        "4inch_standard": WaferPreset(
            name="4-inch Standard",
            size=WaferSize.INCH_4,
            edge_exclusion_mm=2.0,
            description="Standard 4-inch wafer for research and development",
            typical_applications=["R&D", "Prototyping", "Small volume production"]
        ),
        "6inch_production": WaferPreset(
            name="6-inch Production",
            size=WaferSize.INCH_6,
            edge_exclusion_mm=3.0,
            description="6-inch wafer for medium volume production",
            typical_applications=["Analog devices", "Power semiconductors", "MEMS"]
        ),
        "8inch_mainstream": WaferPreset(
            name="8-inch Mainstream",
            size=WaferSize.INCH_8,
            edge_exclusion_mm=3.0,
            description="8-inch wafer for mainstream semiconductor production",
            typical_applications=["Logic devices", "Memory", "Mixed-signal ICs"]
        ),
        "12inch_advanced": WaferPreset(
            name="12-inch Advanced",
            size=WaferSize.INCH_12,
            edge_exclusion_mm=5.0,
            description="12-inch wafer for advanced high-volume production",
            typical_applications=["Advanced logic", "High-density memory", "System-on-chip"]
        ),
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> WaferPreset:
        """Get wafer preset by name."""
        if preset_name not in cls.PRESETS:
            available = ", ".join(cls.PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")
        return cls.PRESETS[preset_name]
    
    @classmethod
    def list_presets(cls) -> List[str]:
        """Get list of available preset names."""
        return list(cls.PRESETS.keys())
    
    @classmethod
    def get_preset_by_size(cls, wafer_size: Union[WaferSize, int]) -> List[WaferPreset]:
        """Get all presets for a specific wafer size."""
        if isinstance(wafer_size, int):
            wafer_size = WaferSize.from_inches(wafer_size)
        
        return [preset for preset in cls.PRESETS.values() if preset.size == wafer_size]


@dataclass
class ScribeLanePresets:
    """Common scribe lane width presets in micrometers."""
    
    # Technology node specific scribe lane widths
    PRESETS = {
        "minimal": {"x": 20, "y": 20, "description": "Minimal scribe lanes for maximum die count"},
        "standard": {"x": 50, "y": 50, "description": "Standard scribe lanes for most applications"},
        "wide": {"x": 80, "y": 80, "description": "Wide scribe lanes for enhanced dicing reliability"},
        "test": {"x": 100, "y": 100, "description": "Extra wide scribe lanes for test structures"},
        "asymmetric": {"x": 60, "y": 40, "description": "Asymmetric scribe lanes for rectangular dies"},
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Dict[str, int]:
        """Get scribe lane preset by name."""
        if preset_name not in cls.PRESETS:
            available = ", ".join(cls.PRESETS.keys())
            raise ValueError(f"Unknown scribe lane preset '{preset_name}'. Available: {available}")
        preset = cls.PRESETS[preset_name].copy()
        del preset["description"]  # Remove description from returned values
        return preset


@dataclass
class DPWParameters:
    """DPW calculation parameters with validation."""
    
    # Die dimensions (micrometers)
    die_size_x_um: float
    die_size_y_um: float
    
    # Scribe lane dimensions (micrometers)
    scribe_lane_x_um: float
    scribe_lane_y_um: float
    
    # Wafer specifications
    wafer_diameter_mm: float
    edge_exclusion_mm: float = 3.0
    
    # Manufacturing parameters
    yield_percentage: float = 100.0
    validation_method: ValidationMethod = ValidationMethod.CORNER_BASED
    
    # Notch parameters
    notch_type: NotchType = NotchType.NONE
    notch_depth_mm: float = 1.0
    
    # Output options
    output_directory: Optional[Path] = None
    generate_html: bool = True
    generate_visualization: bool = True
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all parameters."""
        errors = []
        
        # Die size validation
        if self.die_size_x_um <= 0:
            errors.append("Die size X must be positive")
        if self.die_size_y_um <= 0:
            errors.append("Die size Y must be positive")
        if self.die_size_x_um > 50000:  # 50mm
            errors.append("Die size X seems too large (>50mm)")
        if self.die_size_y_um > 50000:  # 50mm
            errors.append("Die size Y seems too large (>50mm)")
        
        # Scribe lane validation
        if self.scribe_lane_x_um < 0:
            errors.append("Scribe lane X must be non-negative")
        if self.scribe_lane_y_um < 0:
            errors.append("Scribe lane Y must be non-negative")
        if self.scribe_lane_x_um > 1000:  # 1mm
            errors.append("Scribe lane X seems too large (>1mm)")
        if self.scribe_lane_y_um > 1000:  # 1mm
            errors.append("Scribe lane Y seems too large (>1mm)")
        
        # Wafer validation
        if self.wafer_diameter_mm <= 0:
            errors.append("Wafer diameter must be positive")
        if self.wafer_diameter_mm < 25:  # 1 inch
            errors.append("Wafer diameter seems too small (<25mm)")
        if self.wafer_diameter_mm > 450:  # 18 inch
            errors.append("Wafer diameter seems too large (>450mm)")
        
        # Edge exclusion validation
        if self.edge_exclusion_mm < 0:
            errors.append("Edge exclusion must be non-negative")
        if self.edge_exclusion_mm >= self.wafer_diameter_mm / 2:
            errors.append("Edge exclusion cannot be larger than wafer radius")
        
        # Yield validation
        if not (0 <= self.yield_percentage <= 100):
            errors.append("Yield percentage must be between 0 and 100")
        
        # Die pitch validation (die + scribe lane should fit in wafer)
        die_pitch_x_mm = (self.die_size_x_um + self.scribe_lane_x_um) / 1000.0
        die_pitch_y_mm = (self.die_size_y_um + self.scribe_lane_y_um) / 1000.0
        effective_diameter = self.wafer_diameter_mm - 2 * self.edge_exclusion_mm
        
        if die_pitch_x_mm > effective_diameter:
            errors.append(f"Die pitch X ({die_pitch_x_mm:.1f}mm) larger than effective wafer diameter ({effective_diameter:.1f}mm)")
        if die_pitch_y_mm > effective_diameter:
            errors.append(f"Die pitch Y ({die_pitch_y_mm:.1f}mm) larger than effective wafer diameter ({effective_diameter:.1f}mm)")
        
        if errors:
            raise ValueError(f"Parameter validation failed: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary."""
        return {
            'die_size_x_um': self.die_size_x_um,
            'die_size_y_um': self.die_size_y_um,
            'scribe_lane_x_um': self.scribe_lane_x_um,
            'scribe_lane_y_um': self.scribe_lane_y_um,
            'wafer_diameter_mm': self.wafer_diameter_mm,
            'edge_exclusion_mm': self.edge_exclusion_mm,
            'yield_percentage': self.yield_percentage,
            'validation_method': self.validation_method.value,
            'output_directory': str(self.output_directory) if self.output_directory else None,
            'generate_html': self.generate_html,
            'generate_visualization': self.generate_visualization,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DPWParameters':
        """Create parameters from dictionary."""
        # Handle validation method conversion
        if 'validation_method' in data:
            if isinstance(data['validation_method'], str):
                data['validation_method'] = ValidationMethod(data['validation_method'])
        
        # Handle output directory conversion
        if 'output_directory' in data and data['output_directory']:
            data['output_directory'] = Path(data['output_directory'])
        
        return cls(**data)


class DPWConfig:
    """Main configuration manager for DPW tool."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional configuration file path
        """
        self.config_file = config_file
        self.parameters: Optional[DPWParameters] = None
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file: Path) -> DPWParameters:
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Validated DPW parameters
        """
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Extract DPW-specific configuration
            dpw_config = config_data.get('dpw', {})
            
            self.parameters = DPWParameters.from_dict(dpw_config)
            self.logger.info(f"Configuration loaded from {config_file}")
            
            return self.parameters
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_file}: {e}")
            raise
    
    def save_config(self, config_file: Path, parameters: DPWParameters) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config_file: Path to save configuration
            parameters: DPW parameters to save
        """
        try:
            config_data = {
                'dpw': parameters.to_dict()
            }
            
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {config_file}: {e}")
            raise
    
    def create_default_config(self, output_file: Path) -> DPWParameters:
        """
        Create default configuration file.
        
        Args:
            output_file: Path to save default configuration
            
        Returns:
            Default DPW parameters
        """
        default_params = DPWParameters(
            die_size_x_um=1000.0,
            die_size_y_um=2000.0,
            scribe_lane_x_um=50.0,
            scribe_lane_y_um=50.0,
            wafer_diameter_mm=200.0,  # 8-inch wafer
            edge_exclusion_mm=3.0,
            yield_percentage=100.0,
            validation_method=ValidationMethod.CORNER_BASED,
            generate_html=True,
            generate_visualization=True
        )
        
        self.save_config(output_file, default_params)
        return default_params
    
    def apply_preset(self, parameters: DPWParameters, 
                    wafer_preset: Optional[str] = None,
                    scribe_preset: Optional[str] = None) -> DPWParameters:
        """
        Apply presets to parameters.
        
        Args:
            parameters: Base parameters to modify
            wafer_preset: Name of wafer preset to apply
            scribe_preset: Name of scribe lane preset to apply
            
        Returns:
            Updated parameters
        """
        if wafer_preset:
            preset = WaferPresets.get_preset(wafer_preset)
            parameters.wafer_diameter_mm = preset.size.mm
            parameters.edge_exclusion_mm = preset.edge_exclusion_mm
            self.logger.info(f"Applied wafer preset: {preset.name}")
        
        if scribe_preset:
            scribe_config = ScribeLanePresets.get_preset(scribe_preset)
            parameters.scribe_lane_x_um = scribe_config['x']
            parameters.scribe_lane_y_um = scribe_config['y']
            self.logger.info(f"Applied scribe lane preset: {scribe_preset}")
        
        # Re-validate after applying presets
        parameters.validate()
        
        return parameters
    
    def get_validation_info(self) -> Dict[str, Any]:
        """Get information about validation methods and presets."""
        return {
            'validation_methods': {
                method.value: ValidationMethods.get_method_description(method)
                for method in ValidationMethod
            },
            'wafer_presets': {
                name: {
                    'size_inches': preset.size.inches,
                    'size_mm': preset.size.mm,
                    'edge_exclusion_mm': preset.edge_exclusion_mm,
                    'description': preset.description,
                    'applications': preset.typical_applications
                }
                for name, preset in WaferPresets.PRESETS.items()
            },
            'scribe_presets': ScribeLanePresets.PRESETS,
        }