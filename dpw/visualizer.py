"""
Wafer Visualization Generator

Creates SVG-based wafer maps showing die layout, scribe lanes,
and detailed die positioning information.
"""

import math
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from dpw.calculator import CalculationResult, DiePosition, ValidationMethod

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for wafer visualization."""
    
    # SVG canvas dimensions
    canvas_width: int = 800
    canvas_height: int = 800
    
    # Color scheme
    wafer_color: str = "#E8F4FD"  # Light blue wafer
    wafer_edge_color: str = "#2196F3"  # Blue wafer edge
    notch_color: str = "#1976D2"  # Darker blue for notch area
    die_valid_color: str = "#4CAF50"  # Green valid dies
    die_partial_color: str = "#FF9800"  # Orange partial dies
    die_invalid_color: str = "#F44336"  # Red invalid dies
    scribe_color: str = "#757575"  # Gray scribe lanes
    exclusion_color: str = "#FFEB3B"  # Yellow exclusion zone
    grid_color: str = "#E0E0E0"  # Light gray grid
    
    # Display options
    show_grid: bool = True
    show_die_labels: bool = False
    show_scribe_lanes: bool = True
    show_exclusion_zone: bool = True
    show_partial_dies: bool = True
    show_notch_highlight: bool = True  # Highlight notch area with different color
    
    # Font settings
    font_family: str = "Arial, sans-serif"
    font_size: int = 8


class WaferVisualizer:
    """Generates SVG visualizations of wafer die layouts."""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize wafer visualizer.
        
        Args:
            config: Visualization configuration
        """
        self.config = config or VisualizationConfig()
        self.logger = logging.getLogger(__name__)
    
    def generate_wafer_map(self, result: CalculationResult) -> str:
        """
        Generate SVG wafer map from calculation result.
        
        Args:
            result: Die calculation result
            
        Returns:
            SVG content as string
        """
        # Extract parameters
        params = result.parameters
        wafer_radius_mm = params['wafer_diameter_mm'] / 2.0
        effective_radius_mm = params['effective_radius_mm']
        die_pitch_x_mm = params['die_pitch_x_mm']
        die_pitch_y_mm = params['die_pitch_y_mm']
        
        # Calculate scaling factor to fit wafer in canvas
        canvas_radius = min(self.config.canvas_width, self.config.canvas_height) / 2.0 - 50
        scale_factor = canvas_radius / wafer_radius_mm
        
        # Canvas center
        center_x = self.config.canvas_width / 2.0
        center_y = self.config.canvas_height / 2.0
        
        # Start building SVG
        svg_parts = []
        svg_parts.append(f'<svg width="{self.config.canvas_width}" height="{self.config.canvas_height}" '
                        f'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.config.canvas_width} {self.config.canvas_height}">')
        
        # Add definitions for patterns and gradients
        svg_parts.append(self._generate_svg_definitions())
        
        # Draw wafer background with notch integration
        wafer_radius_px = wafer_radius_mm * scale_factor
        wafer_path = self._generate_wafer_with_notch(center_x, center_y, wafer_radius_px, result)
        svg_parts.append(wafer_path)
        
        # Draw exclusion zone if enabled
        if self.config.show_exclusion_zone and params['edge_exclusion_mm'] > 0:
            exclusion_radius_px = effective_radius_mm * scale_factor
            svg_parts.append(f'<circle cx="{center_x}" cy="{center_y}" r="{exclusion_radius_px}" '
                            f'fill="none" stroke="{self.config.exclusion_color}" stroke-width="1" '
                            f'stroke-dasharray="5,5" opacity="0.7"/>')
        
        # Draw grid if enabled
        if self.config.show_grid:
            svg_parts.append(self._generate_grid(center_x, center_y, scale_factor, 
                                               die_pitch_x_mm, die_pitch_y_mm, effective_radius_mm))
        
        # Draw dies
        svg_parts.append(self._generate_dies(result, center_x, center_y, scale_factor))
        
        # Add wafer notch based on notch type
        svg_parts.append(self._generate_wafer_notch(center_x, center_y, wafer_radius_px, result))
        
        # Add legend with notch information
        svg_parts.append(self._generate_legend(result))
        
        # Add title and statistics
        svg_parts.append(self._generate_title_and_stats(result))
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)
    
    def _generate_svg_definitions(self) -> str:
        """Generate SVG definitions for patterns and gradients."""
        return '''
        <defs>
            <pattern id="scribePattern" patternUnits="userSpaceOnUse" width="4" height="4">
                <rect width="4" height="4" fill="none"/>
                <path d="M0,4 L4,0" stroke="#999" stroke-width="0.5"/>
            </pattern>
            <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="#000" flood-opacity="0.3"/>
            </filter>
        </defs>
        '''
    
    def _generate_grid(self, center_x: float, center_y: float, scale_factor: float,
                      die_pitch_x_mm: float, die_pitch_y_mm: float, 
                      effective_radius_mm: float) -> str:
        """Generate grid lines showing die pitch."""
        grid_lines = []
        
        # Calculate grid bounds
        max_extent_x = effective_radius_mm * 1.2  # Slightly larger than effective radius
        max_extent_y = effective_radius_mm * 1.2
        
        # Vertical grid lines
        x_mm = 0
        while x_mm <= max_extent_x:
            x_px = center_x + x_mm * scale_factor
            y1_px = center_y - effective_radius_mm * scale_factor
            y2_px = center_y + effective_radius_mm * scale_factor
            
            if x_mm > 0:  # Positive side
                grid_lines.append(f'<line x1="{x_px}" y1="{y1_px}" x2="{x_px}" y2="{y2_px}" '
                                f'stroke="{self.config.grid_color}" stroke-width="0.5" opacity="0.5"/>')
            
            if x_mm > 0:  # Negative side
                x_px_neg = center_x - x_mm * scale_factor
                grid_lines.append(f'<line x1="{x_px_neg}" y1="{y1_px}" x2="{x_px_neg}" y2="{y2_px}" '
                                f'stroke="{self.config.grid_color}" stroke-width="0.5" opacity="0.5"/>')
            
            x_mm += die_pitch_x_mm
        
        # Horizontal grid lines  
        y_mm = 0
        while y_mm <= max_extent_y:
            y_px = center_y + y_mm * scale_factor
            x1_px = center_x - effective_radius_mm * scale_factor
            x2_px = center_x + effective_radius_mm * scale_factor
            
            if y_mm > 0:  # Positive side
                grid_lines.append(f'<line x1="{x1_px}" y1="{y_px}" x2="{x2_px}" y2="{y_px}" '
                                f'stroke="{self.config.grid_color}" stroke-width="0.5" opacity="0.5"/>')
            
            if y_mm > 0:  # Negative side
                y_px_neg = center_y - y_mm * scale_factor
                grid_lines.append(f'<line x1="{x1_px}" y1="{y_px_neg}" x2="{x2_px}" y2="{y_px_neg}" '
                                f'stroke="{self.config.grid_color}" stroke-width="0.5" opacity="0.5"/>')
            
            y_mm += die_pitch_y_mm
        
        return '\n'.join(grid_lines)
    
    def _is_die_in_notch_area(self, die_pos: DiePosition, result: CalculationResult, 
                             center_x: float, center_y: float, scale_factor: float) -> bool:
        """
        Check if a die position falls within the notch area.
        
        Args:
            die_pos: Die position to check
            result: Calculation result containing notch parameters
            center_x: Canvas center X coordinate
            center_y: Canvas center Y coordinate  
            scale_factor: Scaling factor from mm to pixels
            
        Returns:
            True if die is in notch area, False otherwise
        """
        params = result.parameters
        notch_type_str = params.get('notch_type', 'none')
        
        # No notch area for 'none' type
        if notch_type_str == 'none':
            return False
            
        # Only check for flat and v90 notch types
        if notch_type_str not in ['flat', 'v90']:
            return False
            
        notch_depth_mm = params.get('notch_depth_mm', 1.0)
        wafer_radius_mm = params['wafer_diameter_mm'] / 2.0
        wafer_radius_px = wafer_radius_mm * scale_factor
        
        # Convert die position to canvas coordinates
        die_x_px = center_x + die_pos.center_x * scale_factor
        die_y_px = center_y - die_pos.center_y * scale_factor  # Flip Y for SVG coordinates
        
        if notch_type_str == 'flat':
            # Flat notch geometry - rectangular cut at bottom
            import math
            
            r = wafer_radius_mm
            d = notch_depth_mm
            
            # Safety checks
            if d >= r:
                d = r * 0.9
            if d <= 0:
                return False
                
            # Calculate chord geometry
            chord_width_mm = 2.0 * math.sqrt(2.0 * r * d - d * d)
            chord_half_width_px = (chord_width_mm * scale_factor) / 2.0
            
            # Y position where flat notch begins (on wafer circumference)
            flat_y_px = center_y + math.sqrt(wafer_radius_px**2 - chord_half_width_px**2)
            
            # Check if die is within flat notch area
            return (abs(die_x_px - center_x) <= chord_half_width_px and 
                   die_y_px >= flat_y_px)
                   
        elif notch_type_str == 'v90':
            # V90 notch geometry - triangular cut at bottom
            import math
            
            # Safety check for notch depth
            notch_depth_px = notch_depth_mm * scale_factor
            if notch_depth_px >= wafer_radius_px:
                notch_depth_px = wafer_radius_px * 0.8
            
            # For 90° V-notch: depth = half_width
            notch_half_width_px = notch_depth_px
            
            # V-notch apex point (inward from wafer bottom)
            notch_apex_x = center_x
            notch_apex_y = center_y + wafer_radius_px - notch_depth_px
            
            # Calculate angle from center to notch edge points
            notch_angle = math.asin(min(notch_half_width_px / wafer_radius_px, 1.0))
            
            # Arc endpoints on wafer circumference  
            right_arc_x = center_x + wafer_radius_px * math.sin(notch_angle)
            right_arc_y = center_y + wafer_radius_px * math.cos(notch_angle)
            left_arc_x = center_x - wafer_radius_px * math.sin(notch_angle)
            left_arc_y = center_y + wafer_radius_px * math.cos(notch_angle)
            
            # Check if die is within triangular notch area using cross products
            # Triangle vertices: (left_arc_x, left_arc_y), (notch_apex_x, notch_apex_y), (right_arc_x, right_arc_y)
            def point_in_triangle(px, py, x1, y1, x2, y2, x3, y3):
                # Using barycentric coordinates method
                denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
                if abs(denom) < 1e-10:
                    return False
                    
                a = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom
                b = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom
                c = 1 - a - b
                
                return a >= 0 and b >= 0 and c >= 0
            
            return point_in_triangle(die_x_px, die_y_px, 
                                   left_arc_x, left_arc_y,
                                   notch_apex_x, notch_apex_y, 
                                   right_arc_x, right_arc_y)
        
        return False
    
    def _generate_dies(self, result: CalculationResult, center_x: float, 
                      center_y: float, scale_factor: float) -> str:
        """Generate die rectangles on the wafer."""
        die_elements = []
        params = result.parameters
        
        # Die dimensions in pixels
        die_size_x_px = (params['die_size_x_um'] / 1000.0) * scale_factor
        die_size_y_px = (params['die_size_y_um'] / 1000.0) * scale_factor
        die_pitch_x_px = params['die_pitch_x_mm'] * scale_factor
        die_pitch_y_px = params['die_pitch_y_mm'] * scale_factor
        
        for die_pos in result.die_positions:
            # Calculate die position in pixels
            die_x_px = center_x + die_pos.center_x * scale_factor
            die_y_px = center_y - die_pos.center_y * scale_factor  # Flip Y for SVG coordinates
            
            # Calculate die rectangle corners
            die_left = die_x_px - die_size_x_px / 2.0
            die_top = die_y_px - die_size_y_px / 2.0
            
            # Check if die is in notch area first (for flat and v90 notch types)
            is_in_notch = self._is_die_in_notch_area(die_pos, result, center_x, center_y, scale_factor)
            
            # Determine die color based on notch area and validity
            if is_in_notch:
                # Dies in notch area are always rendered as invalid
                color = self.config.die_invalid_color
                opacity = "0.6"  # Slightly more opaque to distinguish from regular invalid dies
            elif die_pos.is_valid:
                if die_pos.area_ratio >= 1.0:
                    color = self.config.die_valid_color
                    opacity = "0.8"
                else:
                    color = self.config.die_partial_color
                    opacity = f"{0.4 + 0.4 * die_pos.area_ratio}"  # Variable opacity based on area
            else:
                if self.config.show_partial_dies:
                    color = self.config.die_invalid_color
                    opacity = "0.3"
                else:
                    continue  # Skip invalid dies if not showing them
            
            # Draw die rectangle
            die_elements.append(f'<rect x="{die_left}" y="{die_top}" width="{die_size_x_px}" height="{die_size_y_px}" '
                              f'fill="{color}" stroke="white" stroke-width="0.5" opacity="{opacity}" '
                              f'filter="url(#dropShadow)"/>')
            
            # Add die label if enabled
            if self.config.show_die_labels and die_pos.is_valid:
                label = f"({die_pos.col},{die_pos.row})"
                die_elements.append(f'<text x="{die_x_px}" y="{die_y_px + 2}" text-anchor="middle" '
                                  f'font-family="{self.config.font_family}" font-size="{self.config.font_size}" '
                                  f'fill="white" opacity="0.8">{label}</text>')
        
        # Draw scribe lanes if enabled
        if self.config.show_scribe_lanes:
            die_elements.append(self._generate_scribe_lanes(result, center_x, center_y, scale_factor))
        
        return '\n'.join(die_elements)
    
    def _generate_scribe_lanes(self, result: CalculationResult, center_x: float,
                             center_y: float, scale_factor: float) -> str:
        """Generate scribe lane visualization."""
        scribe_elements = []
        params = result.parameters
        
        scribe_x_px = (params['scribe_lane_x_um'] / 1000.0) * scale_factor
        scribe_y_px = (params['scribe_lane_y_um'] / 1000.0) * scale_factor
        die_pitch_x_px = params['die_pitch_x_mm'] * scale_factor
        die_pitch_y_px = params['die_pitch_y_mm'] * scale_factor
        
        # Only show scribe lanes if they're visible at current scale
        if scribe_x_px > 1 or scribe_y_px > 1:
            # Draw sample scribe lanes around valid dies
            for die_pos in result.die_positions:
                if not die_pos.is_valid:
                    continue
                
                die_x_px = center_x + die_pos.center_x * scale_factor
                die_y_px = center_y - die_pos.center_y * scale_factor
                
                # Draw vertical scribe lanes (right side of die)
                if scribe_x_px > 1:
                    scribe_left = die_x_px + (params['die_size_x_um'] / 2000.0) * scale_factor
                    scribe_top = die_y_px - die_pitch_y_px / 2.0
                    scribe_elements.append(f'<rect x="{scribe_left}" y="{scribe_top}" '
                                         f'width="{scribe_x_px}" height="{die_pitch_y_px}" '
                                         f'fill="{self.config.scribe_color}" opacity="0.3"/>')
                
                # Draw horizontal scribe lanes (bottom side of die)
                if scribe_y_px > 1:
                    scribe_left = die_x_px - die_pitch_x_px / 2.0
                    scribe_top = die_y_px + (params['die_size_y_um'] / 2000.0) * scale_factor
                    scribe_elements.append(f'<rect x="{scribe_left}" y="{scribe_top}" '
                                         f'width="{die_pitch_x_px}" height="{scribe_y_px}" '
                                         f'fill="{self.config.scribe_color}" opacity="0.3"/>')
        
        return '\n'.join(scribe_elements)
    
    def _generate_wafer_with_notch(self, center_x: float, center_y: float, wafer_radius_px: float, 
                                  result: CalculationResult) -> str:
        """Generate wafer shape with integrated notch geometry."""
        from .dpw_calculator import NotchType
        
        # Get notch parameters from result
        params = result.parameters
        notch_type_str = params.get('notch_type', 'none')
        notch_depth_mm = params.get('notch_depth_mm', 1.0)
        wafer_radius_mm = params['wafer_diameter_mm'] / 2.0
        
        # Calculate scale factor (pixels per mm)
        scale_factor = wafer_radius_px / wafer_radius_mm
        notch_depth_px = notch_depth_mm * scale_factor
        
        if notch_type_str == 'none':
            # Standard circular wafer
            return (f'<circle cx="{center_x}" cy="{center_y}" r="{wafer_radius_px}" '
                   f'fill="{self.config.wafer_color}" stroke="{self.config.wafer_edge_color}" stroke-width="2"/>')
        
        elif notch_type_str == 'v90':
            # V-shaped notch at bottom of wafer - 90° V cut
            # Safety check for notch depth
            if notch_depth_px >= wafer_radius_px:
                notch_depth_px = wafer_radius_px * 0.8
            
            # For 90° V-notch: depth = half_width
            notch_half_width_px = notch_depth_px
            
            # Calculate exact positions on wafer circumference
            import math
            
            # Calculate angle from center to notch edge points
            notch_angle = math.asin(min(notch_half_width_px / wafer_radius_px, 1.0))
            
            # Arc endpoints on wafer circumference
            right_arc_x = center_x + wafer_radius_px * math.sin(notch_angle)
            right_arc_y = center_y + wafer_radius_px * math.cos(notch_angle)
            left_arc_x = center_x - wafer_radius_px * math.sin(notch_angle)  
            left_arc_y = center_y + wafer_radius_px * math.cos(notch_angle)
            
            # V-notch apex point (inward from wafer bottom)
            notch_apex_x = center_x
            notch_apex_y = center_y + wafer_radius_px - notch_depth_px
            
            # Create integrated wafer+notch path
            path_d = (f'M {center_x - wafer_radius_px} {center_y} '  # Start at leftmost point
                     f'A {wafer_radius_px} {wafer_radius_px} 0 1 1 {right_arc_x} {right_arc_y} '  # Arc to right of V-notch
                     f'L {notch_apex_x} {notch_apex_y} '  # Line to V-notch apex
                     f'L {left_arc_x} {left_arc_y} '      # Line to left of V-notch
                     f'A {wafer_radius_px} {wafer_radius_px} 0 1 1 {center_x - wafer_radius_px} {center_y} Z')  # Complete arc
            
            wafer_svg = (f'<path d="{path_d}" fill="{self.config.wafer_color}" '
                        f'stroke="{self.config.wafer_edge_color}" stroke-width="2"/>')
            
            # Add notch area highlighting if enabled
            if self.config.show_notch_highlight:
                notch_highlight = (f'<path d="M {right_arc_x} {right_arc_y} '
                                  f'L {notch_apex_x} {notch_apex_y} '
                                  f'L {left_arc_x} {left_arc_y} '
                                  f'A {wafer_radius_px} {wafer_radius_px} 0 0 0 {right_arc_x} {right_arc_y} Z" '
                                  f'fill="{self.config.notch_color}" stroke="{self.config.wafer_edge_color}" stroke-width="1" opacity="0.8"/>')
                return f"{wafer_svg}\n{notch_highlight}"
            else:
                return wafer_svg
        
        elif notch_type_str == 'flat':
            # Flat notch at bottom of wafer
            import math
            
            r = wafer_radius_mm
            d = notch_depth_mm
            
            # Safety checks
            if d >= r:
                d = r * 0.9
            if d <= 0:
                d = 0.1
                
            # Chord width calculation: w = 2 * sqrt(2*r*d - d^2)
            chord_width_mm = 2.0 * math.sqrt(2.0 * r * d - d * d)
            chord_half_width_px = (chord_width_mm * scale_factor) / 2.0
            
            # Calculate flat notch geometry on wafer circumference
            
            # Arc endpoints where flat notch begins/ends
            right_arc_x = center_x + chord_half_width_px
            right_arc_y = center_y + math.sqrt(wafer_radius_px**2 - chord_half_width_px**2)
            left_arc_x = center_x - chord_half_width_px
            left_arc_y = center_y + math.sqrt(wafer_radius_px**2 - chord_half_width_px**2)
            
            # Create path with flat notch integrated
            path_d = (f'M {center_x - wafer_radius_px} {center_y} '  # Start at leftmost point
                     f'A {wafer_radius_px} {wafer_radius_px} 0 1 1 {right_arc_x} {right_arc_y} '  # Arc to right of flat notch
                     f'L {left_arc_x} {left_arc_y} '  # Flat line across notch
                     f'A {wafer_radius_px} {wafer_radius_px} 0 1 1 {center_x - wafer_radius_px} {center_y} Z')  # Complete arc
            
            wafer_svg = (f'<path d="{path_d}" fill="{self.config.wafer_color}" '
                        f'stroke="{self.config.wafer_edge_color}" stroke-width="2"/>')
            
            # Add flat notch area highlighting if enabled
            if self.config.show_notch_highlight:
                # Highlight only the removed circular segment, not extending beyond wafer boundary
                notch_highlight = (f'<path d="M {right_arc_x} {right_arc_y} '
                                  f'A {wafer_radius_px} {wafer_radius_px} 0 0 1 {left_arc_x} {left_arc_y} '
                                  f'Z" '
                                  f'fill="{self.config.notch_color}" stroke="{self.config.wafer_edge_color}" stroke-width="1" opacity="0.8"/>')
                return f"{wafer_svg}\n{notch_highlight}"
            else:
                return wafer_svg
        
        # Fallback for unknown notch types
        return (f'<circle cx="{center_x}" cy="{center_y}" r="{wafer_radius_px}" '
               f'fill="{self.config.wafer_color}" stroke="{self.config.wafer_edge_color}" stroke-width="2"/>')
    
    def _generate_wafer_notch(self, center_x: float, center_y: float, wafer_radius_px: float, 
                             result: CalculationResult) -> str:
        """Generate notch indicator for legend (deprecated - notch now integrated in wafer shape)."""
        # This method is now deprecated as notch is integrated into wafer shape
        # Kept for backward compatibility but returns empty string
        return ""
    
    def _generate_legend(self, result: Optional[CalculationResult] = None) -> str:
        """Generate legend for die colors and wafer features."""
        legend_elements = []
        legend_x = 20
        legend_y = self.config.canvas_height - 160  # More space for notch info
        
        legend_items = [
            (self.config.die_valid_color, "Valid Dies"),
            (self.config.die_partial_color, "Partial Dies"),
            (self.config.die_invalid_color, "Invalid Dies"),
        ]
        
        # Add notch information if available
        notch_info = ""
        if result:
            from .dpw_calculator import NotchType
            params = result.parameters
            notch_type_str = params.get('notch_type', 'none')
            notch_depth_mm = params.get('notch_depth_mm', 1.0)
            
            if notch_type_str != 'none':
                notch_name = {"v90": "V-90°", "flat": "Flat", "none": "None"}.get(notch_type_str, notch_type_str)
                notch_info = f"Notch: {notch_name} ({notch_depth_mm}mm)"
                legend_items.append((self.config.wafer_edge_color, notch_info))
        
        # Calculate legend height
        legend_height = len(legend_items) * 20 + 30
        
        # Legend background
        legend_elements.append(f'<rect x="{legend_x - 10}" y="{legend_y - 10}" width="140" height="{legend_height}" '
                              f'fill="white" stroke="#ccc" stroke-width="1" opacity="0.9"/>')
        
        # Legend title
        legend_elements.append(f'<text x="{legend_x}" y="{legend_y + 5}" font-family="{self.config.font_family}" '
                              f'font-size="12" font-weight="bold" fill="#333">Legend</text>')
        
        # Legend items
        for i, (color, label) in enumerate(legend_items):
            item_y = legend_y + 25 + i * 20
            
            # Special handling for notch indicator
            if "Notch:" in label:
                # Draw small triangle for V-notch or rectangle for flat notch
                if "V-90°" in label:
                    # Small triangle (V-notch symbol)
                    points = f"{legend_x + 6},{item_y - 2} {legend_x},{item_y - 8} {legend_x + 12},{item_y - 8}"
                    legend_elements.append(f'<polygon points="{points}" fill="{self.config.notch_color}" stroke="{self.config.wafer_edge_color}" stroke-width="0.5" opacity="0.8"/>')
                elif "Flat" in label:
                    # Small rectangle (flat notch symbol)
                    legend_elements.append(f'<rect x="{legend_x}" y="{item_y - 8}" width="12" height="6" '
                                          f'fill="{self.config.notch_color}" stroke="{self.config.wafer_edge_color}" stroke-width="0.5" opacity="0.8"/>')
                else:
                    # Generic notch indicator
                    legend_elements.append(f'<rect x="{legend_x}" y="{item_y - 8}" width="12" height="6" '
                                          f'fill="{self.config.notch_color}" stroke="{self.config.wafer_edge_color}" stroke-width="0.5" opacity="0.8"/>')
            else:
                # Standard die color rectangle
                legend_elements.append(f'<rect x="{legend_x}" y="{item_y - 8}" width="12" height="12" '
                                      f'fill="{color}" stroke="white" stroke-width="0.5"/>')
            
            legend_elements.append(f'<text x="{legend_x + 20}" y="{item_y + 2}" font-family="{self.config.font_family}" '
                                  f'font-size="10" fill="#333">{label}</text>')
        
        return '\n'.join(legend_elements)
    
    def _generate_title_and_stats(self, result: CalculationResult) -> str:
        """Generate title and statistics overlay."""
        stats_elements = []
        
        # Title
        title_text = f"Die Per Wafer Analysis - {result.calculation_method.value.title()} Method"
        stats_elements.append(f'<text x="{self.config.canvas_width / 2}" y="30" text-anchor="middle" '
                             f'font-family="{self.config.font_family}" font-size="16" font-weight="bold" '
                             f'fill="#333">{title_text}</text>')
        
        # Statistics box
        stats_x = self.config.canvas_width - 200
        stats_y = 60
        
        stats_data = [
            f"Total Dies: {result.total_dies}",
            f"Yield Dies: {result.yield_dies}",
            f"Utilization: {result.wafer_utilization:.1f}%",
            f"Die Size: {result.parameters['die_size_x_um']:.0f}×{result.parameters['die_size_y_um']:.0f}μm",
            f"Wafer: {result.parameters['wafer_diameter_mm']:.0f}mm",
        ]
        
        # Add notch information if present
        from .dpw_calculator import NotchType
        params = result.parameters
        notch_type_str = params.get('notch_type', 'none')
        notch_depth_mm = params.get('notch_depth_mm', 1.0)
        
        if notch_type_str != 'none':
            notch_name = {"v90": "V-90°", "flat": "Flat", "none": "None"}.get(notch_type_str, notch_type_str)
            stats_data.append(f"Notch: {notch_name} ({notch_depth_mm}mm)")
            
            # Add notch area loss if available
            if 'notch_area_mm2' in params:
                notch_area = params['notch_area_mm2']
                stats_data.append(f"Notch Area: {notch_area:.2f}mm²")
        
        # Stats background
        stats_elements.append(f'<rect x="{stats_x - 10}" y="{stats_y - 10}" width="200" height="{len(stats_data) * 18 + 20}" '
                             f'fill="white" stroke="#ccc" stroke-width="1" opacity="0.9"/>')
        
        # Stats text
        for i, stat in enumerate(stats_data):
            stat_y = stats_y + 15 + i * 18
            stats_elements.append(f'<text x="{stats_x}" y="{stat_y}" font-family="{self.config.font_family}" '
                                 f'font-size="11" fill="#333">{stat}</text>')
        
        return '\n'.join(stats_elements)
    
    def save_svg(self, svg_content: str, output_path: Path) -> None:
        """
        Save SVG content to file.
        
        Args:
            svg_content: SVG content string
            output_path: Output file path
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            self.logger.info(f"Wafer visualization saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save wafer visualization: {e}")
            raise
    
    def generate_comparison_visualization(self, results: Dict[ValidationMethod, CalculationResult]) -> str:
        """
        Generate comparison visualization for multiple validation methods.
        
        Args:
            results: Dictionary mapping validation methods to results
            
        Returns:
            SVG content showing side-by-side comparison
        """
        if not results:
            raise ValueError("No results provided for comparison")
        
        # Create larger canvas for multiple wafers
        num_methods = len(results)
        canvas_width = 300 * num_methods + 100
        canvas_height = 400
        
        svg_parts = []
        svg_parts.append(f'<svg width="{canvas_width}" height="{canvas_height}" '
                        f'xmlns="http://www.w3.org/2000/svg">')
        
        svg_parts.append(self._generate_svg_definitions())
        
        # Generate wafer for each method
        for i, (method, result) in enumerate(results.items()):
            x_offset = 50 + i * 300
            y_offset = 50
            
            # Scale down individual wafers for comparison
            temp_config = VisualizationConfig()
            temp_config.canvas_width = 200
            temp_config.canvas_height = 200
            
            temp_visualizer = WaferVisualizer(temp_config)
            wafer_svg = temp_visualizer.generate_wafer_map(result)
            
            # Extract wafer content (remove SVG wrapper)
            wafer_content = wafer_svg[wafer_svg.find('<circle'):wafer_svg.rfind('</svg>')]
            
            # Add translated group
            svg_parts.append(f'<g transform="translate({x_offset}, {y_offset})">')
            svg_parts.append(wafer_content)
            
            # Add method label
            svg_parts.append(f'<text x="100" y="220" text-anchor="middle" '
                           f'font-family="Arial" font-size="12" font-weight="bold">'
                           f'{method.value.title()}</text>')
            svg_parts.append(f'<text x="100" y="235" text-anchor="middle" '
                           f'font-family="Arial" font-size="10">'
                           f'{result.total_dies} dies</text>')
            
            svg_parts.append('</g>')
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)