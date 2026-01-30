"""
HTML Reporter for Die Per Wafer Tool

Generates professional HTML reports with interactive interfaces,
wafer visualizations, and comprehensive calculation results.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

from dpw.calculator import CalculationResult, ValidationMethod, ValidationMethods
from dpw.config import DPWParameters, WaferPresets, ScribeLanePresets
from dpw.visualizer import WaferVisualizer, VisualizationConfig

logger = logging.getLogger(__name__)


class DPWHTMLReporter:
    """
    Generates comprehensive HTML reports for DPW calculations.
    
    Features:
    - Interactive parameter input interface
    - Real-time calculation updates
    - Professional wafer visualization
    - Detailed results and statistics
    - Export capabilities
    """
    
    def __init__(self):
        """Initialize HTML reporter."""
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.visualizer = WaferVisualizer()
        self.logger = logging.getLogger(__name__)
    
    def generate_interactive_report(self, 
                                   result: Optional[CalculationResult] = None,
                                   parameters: Optional[DPWParameters] = None,
                                   output_path: Path = None) -> str:
        """
        Generate interactive HTML report with calculation interface.
        
        Args:
            result: Optional calculation result to display
            parameters: Optional initial parameters
            output_path: Optional path to save HTML file
            
        Returns:
            HTML content as string
        """
        try:
            # Prepare report data
            report_data = self._prepare_interactive_report_data(result, parameters)
            
            # Load and render template
            template = self.env.get_template("dpw_interactive.html.j2")
            html_content = template.render(**report_data)
            
            # Save to file if path provided
            if output_path:
                self._save_html_file(html_content, output_path)
            
            self.logger.info("Interactive HTML report generated successfully")
            return html_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate interactive HTML report: {e}")
            raise
    
    def generate_results_report(self, 
                               result: CalculationResult,
                               parameters: DPWParameters,
                               output_path: Path) -> str:
        """
        Generate detailed results report.
        
        Args:
            result: Calculation result
            parameters: DPW parameters used
            output_path: Path to save HTML file
            
        Returns:
            HTML content as string
        """
        try:
            # Prepare report data
            report_data = self._prepare_results_report_data(result, parameters)
            
            # Generate wafer visualization
            wafer_svg = self.visualizer.generate_wafer_map(result)
            report_data['wafer_visualization'] = wafer_svg
            
            # Load and render template
            template = self.env.get_template("dpw_results.html.j2")
            html_content = template.render(**report_data)
            
            # Save to file
            self._save_html_file(html_content, output_path)
            
            self.logger.info(f"Results report generated: {output_path}")
            return html_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate results report: {e}")
            raise
    
    def generate_comparison_report(self,
                                  results: Dict[ValidationMethod, CalculationResult],
                                  parameters: DPWParameters,
                                  output_path: Path) -> str:
        """
        Generate comparison report for multiple validation methods.
        
        Args:
            results: Dictionary mapping validation methods to results
            parameters: DPW parameters used
            output_path: Path to save HTML file
            
        Returns:
            HTML content as string
        """
        try:
            # Prepare comparison data
            report_data = self._prepare_comparison_report_data(results, parameters)
            
            # Generate comparison visualization
            comparison_svg = self.visualizer.generate_comparison_visualization(results)
            report_data['comparison_visualization'] = comparison_svg
            
            # Load and render template
            template = self.env.get_template("dpw_comparison.html.j2")
            html_content = template.render(**report_data)
            
            # Save to file
            self._save_html_file(html_content, output_path)
            
            self.logger.info(f"Comparison report generated: {output_path}")
            return html_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate comparison report: {e}")
            raise
    
    def _prepare_interactive_report_data(self, 
                                        result: Optional[CalculationResult],
                                        parameters: Optional[DPWParameters]) -> Dict[str, Any]:
        """Prepare data for interactive report template."""
        
        # Default parameters if none provided
        if parameters is None:
            parameters = DPWParameters(
                die_size_x_um=1000.0,
                die_size_y_um=2000.0,
                scribe_lane_x_um=50.0,
                scribe_lane_y_um=50.0,
                wafer_diameter_mm=200.0,
                edge_exclusion_mm=3.0,
                yield_percentage=100.0
            )
        
        # Prepare wafer presets for dropdowns
        wafer_presets = {}
        for name, preset in WaferPresets.PRESETS.items():
            wafer_presets[name] = {
                'name': preset.name,
                'diameter_mm': preset.size.mm,
                'edge_exclusion_mm': preset.edge_exclusion_mm,
                'description': preset.description
            }
        
        # Prepare scribe lane presets
        scribe_presets = {}
        for name, preset in ScribeLanePresets.PRESETS.items():
            scribe_presets[name] = {
                'x': preset['x'],
                'y': preset['y'],
                'description': preset['description']
            }
        
        # Prepare validation methods
        validation_methods = {}
        for method in ValidationMethod:
            validation_methods[method.value] = {
                'name': method.value.replace('_', ' ').title(),
                'description': ValidationMethods.get_method_description(method)
            }
        
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'page_title': 'Die Per Wafer Calculator',
            'parameters': parameters.to_dict() if parameters else {},
            'wafer_presets': wafer_presets,
            'scribe_presets': scribe_presets,
            'validation_methods': validation_methods,
            'has_result': result is not None,
        }
        
        # Add result data if available
        if result:
            data.update(self._extract_result_data(result))
            data['wafer_visualization'] = self.visualizer.generate_wafer_map(result)
        
        return data
    
    def _prepare_results_report_data(self, 
                                    result: CalculationResult,
                                    parameters: DPWParameters) -> Dict[str, Any]:
        """Prepare data for results report template."""
        
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'page_title': f'DPW Results - {result.calculation_method.value.title()} Method',
            'parameters': parameters.to_dict(),
        }
        
        # Add result data
        data.update(self._extract_result_data(result))
        
        # Add optimization suggestions
        from .dpw_calculator import DieCalculator
        calculator = DieCalculator()
        data['optimization_suggestions'] = calculator.get_optimization_suggestions(result)
        
        # Add detailed statistics
        data['detailed_stats'] = self._calculate_detailed_statistics(result)
        
        return data
    
    def _prepare_comparison_report_data(self,
                                       results: Dict[ValidationMethod, CalculationResult],
                                       parameters: DPWParameters) -> Dict[str, Any]:
        """Prepare data for comparison report template."""
        
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'page_title': 'DPW Method Comparison',
            'parameters': parameters.to_dict(),
            'comparison_results': {}
        }
        
        # Extract data for each method
        for method, result in results.items():
            method_data = self._extract_result_data(result)
            method_data['method_name'] = method.value.replace('_', ' ').title()
            method_data['method_description'] = ValidationMethods.get_method_description(method)
            data['comparison_results'][method.value] = method_data
        
        # Add comparison statistics
        data['comparison_stats'] = self._calculate_comparison_statistics(results)
        
        return data
    
    def _extract_result_data(self, result: CalculationResult) -> Dict[str, Any]:
        """Extract data from calculation result."""
        return {
            'total_dies': result.total_dies,
            'yield_dies': result.yield_dies,
            'wafer_utilization': result.wafer_utilization,
            'calculation_method': result.calculation_method.value,
            'method_name': result.calculation_method.value.replace('_', ' ').title(),
            'valid_die_positions': [
                {
                    'row': pos.row,
                    'col': pos.col,
                    'center_x': pos.center_x,
                    'center_y': pos.center_y,
                    'distance': pos.distance_from_center,
                    'area_ratio': pos.area_ratio
                }
                for pos in result.die_positions if pos.is_valid
            ]
        }
    
    def _calculate_detailed_statistics(self, result: CalculationResult) -> Dict[str, Any]:
        """Calculate detailed statistics for result."""
        params = result.parameters
        
        # Calculate areas
        wafer_area_mm2 = 3.14159 * (params['wafer_diameter_mm'] / 2.0) ** 2
        effective_area_mm2 = 3.14159 * params['effective_radius_mm'] ** 2
        die_area_mm2 = (params['die_size_x_um'] * params['die_size_y_um']) / (1000.0 * 1000.0)
        total_die_area_mm2 = result.total_dies * die_area_mm2
        
        # Calculate pitches
        die_pitch_mm2 = params['die_pitch_x_mm'] * params['die_pitch_y_mm']
        
        # Die position statistics
        valid_positions = [pos for pos in result.die_positions if pos.is_valid]
        distances = [pos.distance_from_center for pos in valid_positions]
        
        # Base statistics
        stats = {
            'wafer_area_mm2': round(wafer_area_mm2, 2),
            'effective_area_mm2': round(effective_area_mm2, 2),
            'edge_exclusion_area_mm2': round(wafer_area_mm2 - effective_area_mm2, 2),
            'die_area_mm2': round(die_area_mm2, 4),
            'total_die_area_mm2': round(total_die_area_mm2, 2),
            'die_pitch_mm2': round(die_pitch_mm2, 4),
            'area_efficiency': round((die_area_mm2 / die_pitch_mm2) * 100, 2),
            'dies_per_cm2': round(result.total_dies / (effective_area_mm2 / 100), 1),
            'average_distance_from_center': round(sum(distances) / len(distances), 2) if distances else 0,
            'max_distance_from_center': round(max(distances), 2) if distances else 0,
            'edge_loss_percentage': round(((effective_area_mm2 - total_die_area_mm2) / effective_area_mm2) * 100, 2)
        }
        
        # Add notch impact statistics if notch is present
        from .dpw_calculator import NotchType
        notch_type_str = params.get('notch_type', 'none')
        
        if notch_type_str != 'none':
            notch_depth_mm = params.get('notch_depth_mm', 1.0)
            notch_area_mm2 = params.get('notch_area_mm2', 0.0)
            
            # Calculate notch impact
            notch_area_percentage = (notch_area_mm2 / wafer_area_mm2) * 100 if wafer_area_mm2 > 0 else 0
            
            # Estimate potential die loss due to notch
            # This is approximate - dies near the notch edge might be affected
            estimated_die_loss = max(0, int(notch_area_mm2 / die_area_mm2))
            
            notch_stats = {
                'has_notch': True,
                'notch_type': notch_type_str,
                'notch_type_display': {"v90": "V-90°", "flat": "Flat", "none": "None"}.get(notch_type_str, notch_type_str),
                'notch_depth_mm': round(notch_depth_mm, 2),
                'notch_area_mm2': round(notch_area_mm2, 3),
                'notch_area_percentage': round(notch_area_percentage, 3),
                'estimated_die_loss': estimated_die_loss,
                'notch_yield_impact': round((estimated_die_loss / result.total_dies) * 100, 2) if result.total_dies > 0 else 0
            }
            
            # Calculate notch-specific geometry
            wafer_radius_mm = params['wafer_diameter_mm'] / 2.0
            
            if notch_type_str == 'v90':
                # V90 notch geometry
                notch_base_width_mm = notch_depth_mm * 2.0
                notch_stats.update({
                    'notch_base_width_mm': round(notch_base_width_mm, 2),
                    'notch_apex_angle': 90,
                    'notch_geometry_type': 'Triangular'
                })
            
            elif notch_type_str == 'flat':
                # Flat notch geometry - calculate chord width
                import math
                r = wafer_radius_mm
                d = notch_depth_mm
                chord_width_mm = 2.0 * math.sqrt(2.0 * r * d - d * d) if (2.0 * r * d - d * d) > 0 else 0
                notch_stats.update({
                    'notch_chord_width_mm': round(chord_width_mm, 2),
                    'notch_geometry_type': 'Rectangular'
                })
            
            stats.update(notch_stats)
        else:
            stats['has_notch'] = False
        
        return stats
    
    def _calculate_comparison_statistics(self, 
                                        results: Dict[ValidationMethod, CalculationResult]) -> Dict[str, Any]:
        """Calculate comparison statistics across methods."""
        if not results:
            return {}
        
        die_counts = [result.total_dies for result in results.values()]
        utilizations = [result.wafer_utilization for result in results.values()]
        
        return {
            'min_dies': min(die_counts),
            'max_dies': max(die_counts),
            'die_count_range': max(die_counts) - min(die_counts),
            'min_utilization': round(min(utilizations), 2),
            'max_utilization': round(max(utilizations), 2),
            'utilization_range': round(max(utilizations) - min(utilizations), 2),
            'recommended_method': ValidationMethods.get_recommended_method().value
        }
    
    def _save_html_file(self, html_content: str, output_path: Path) -> None:
        """Save HTML content to file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save HTML file: {e}")
            raise
    
    def export_json_data(self, result: CalculationResult, output_path: Path) -> None:
        """
        Export calculation data as JSON.
        
        Args:
            result: Calculation result
            output_path: Path for output JSON file
        """
        try:
            data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'calculation_method': result.calculation_method.value,
                    'total_dies': result.total_dies,
                    'yield_dies': result.yield_dies,
                    'wafer_utilization': result.wafer_utilization
                },
                'parameters': result.parameters,
                'die_positions': [
                    {
                        'row': pos.row,
                        'col': pos.col,
                        'center_x': pos.center_x,
                        'center_y': pos.center_y,
                        'is_valid': pos.is_valid,
                        'area_ratio': pos.area_ratio,
                        'distance_from_center': pos.distance_from_center
                    }
                    for pos in result.die_positions
                ],
                'statistics': self._calculate_detailed_statistics(result)
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON data exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON data: {e}")
            raise
    
    def export_csv_summary(self, result: CalculationResult, output_path: Path) -> None:
        """
        Export summary statistics as CSV.
        
        Args:
            result: Calculation result
            output_path: Path for output CSV file
        """
        try:
            import csv
            
            # Prepare summary data
            stats = self._calculate_detailed_statistics(result)
            params = result.parameters
            
            summary_data = [
                ['Parameter', 'Value', 'Unit'],
                ['Die Size X', params['die_size_x_um'], 'μm'],
                ['Die Size Y', params['die_size_y_um'], 'μm'],
                ['Scribe Lane X', params['scribe_lane_x_um'], 'μm'],
                ['Scribe Lane Y', params['scribe_lane_y_um'], 'μm'],
                ['Wafer Diameter', params['wafer_diameter_mm'], 'mm'],
                ['Edge Exclusion', params['edge_exclusion_mm'], 'mm'],
                ['Yield Percentage', params['yield_percentage'], '%'],
                ['Validation Method', result.calculation_method.value, ''],
                ['Total Dies', result.total_dies, 'count'],
                ['Yield Dies', result.yield_dies, 'count'],
                ['Wafer Utilization', round(result.wafer_utilization, 2), '%'],
                ['Die Area', stats['die_area_mm2'], 'mm²'],
                ['Area Efficiency', stats['area_efficiency'], '%'],
                ['Dies per cm²', stats['dies_per_cm2'], 'dies/cm²'],
            ]
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(summary_data)
            
            self.logger.info(f"CSV summary exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV summary: {e}")
            raise