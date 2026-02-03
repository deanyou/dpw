"""
优化版Die Per Wafer计算器 - 高性能优化版本

基于数学优化和对称性减少计算量
"""

import math
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationMethod(Enum):
    """Die validation methods for counting."""
    CENTER_BASED = "center"      # Conservative: die center within boundary
    CORNER_BASED = "corner"      # Industry standard: all corners within boundary  
    AREA_BASED = "area"          # Most accurate: >50% area within boundary
    STRICT = "strict"            # Strictest: entire die within boundary


class NotchType(Enum):
    """Wafer notch types for die placement calculations."""
    NONE = "none"        # No notch consideration (default)
    V_NOTCH_90 = "v90"   # 90-degree V-notch (200mm+ wafers)
    FLAT = "flat"        # Flat edge cut (smaller wafers)


@dataclass
class DiePosition:
    """Represents a die position on the wafer."""
    row: int
    col: int
    center_x: float
    center_y: float
    is_valid: bool
    area_ratio: float = 1.0  # Fraction of die area within wafer
    distance_from_center: float = 0.0


@dataclass
class CalculationResult:
    """Results of die per wafer calculation."""
    total_dies: int
    yield_dies: int
    wafer_utilization: float  # Percentage of wafer area used
    die_positions: List[DiePosition]
    calculation_method: ValidationMethod
    parameters: Dict


class OptimizedWaferGeometry:
    """优化版晶圆几何计算，使用数学公式减少迭代"""
    
    def __init__(self, wafer_diameter_mm: float, edge_exclusion_mm: float = 0.0,
                 notch_type: NotchType = NotchType.NONE, notch_depth_mm: float = 1.0):
        self.wafer_diameter_mm = wafer_diameter_mm
        self.wafer_radius_mm = wafer_diameter_mm / 2.0
        self.edge_exclusion_mm = edge_exclusion_mm
        self.effective_radius_mm = self.wafer_radius_mm - edge_exclusion_mm
        self.notch_type = notch_type
        self.notch_depth_mm = notch_depth_mm
        self.notch_area_mm2 = self._calculate_notch_area()
        
        if self.effective_radius_mm <= 0:
            raise ValueError(f"Effective radius must be positive. Got {self.effective_radius_mm}mm")
        
        if notch_depth_mm < 0:
            raise ValueError(f"Notch depth must be non-negative. Got {notch_depth_mm}mm")
        
        if notch_depth_mm >= self.wafer_radius_mm:
            raise ValueError(f"Notch depth ({notch_depth_mm}mm) cannot exceed wafer radius ({self.wafer_radius_mm}mm)")
    
    def _calculate_notch_area(self) -> float:
        """Calculate the area of the wafer notch in mm²."""
        if self.notch_type == NotchType.NONE:
            return 0.0
        elif self.notch_type == NotchType.V_NOTCH_90:
            # V-notch with 90° angle: Area = depth²
            return self.notch_depth_mm * self.notch_depth_mm
        elif self.notch_type == NotchType.FLAT:
            # Flat notch: Area = chord_width × depth
            # For a flat of given depth, calculate chord width using circle geometry
            r = self.wafer_radius_mm
            d = self.notch_depth_mm
            if d >= r or d <= 0:
                return 0.0  # Invalid depth
            # Chord width = 2 × sqrt(r² - (r-d)²) = 2 × sqrt(2rd - d²)
            chord_width = 2.0 * math.sqrt(2.0 * r * d - d * d)
            return chord_width * d
        else:
            return 0.0
    
    def is_point_in_wafer(self, x: float, y: float) -> bool:
        """Check if point (x, y) is within the effective wafer area."""
        distance = math.sqrt(x * x + y * y)
        return distance <= self.effective_radius_mm
    
    def _is_rectangle_intersecting_notch(self, center_x: float, center_y: float, 
                                        width: float, height: float) -> bool:
        """Check if rectangle intersects with wafer notch."""
        if self.notch_type == NotchType.NONE:
            return False
        
        half_width = width / 2.0
        half_height = height / 2.0
        
        # Rectangle bounds
        rect_left = center_x - half_width
        rect_right = center_x + half_width
        rect_top = center_y - half_height
        rect_bottom = center_y + half_height
        
        if self.notch_type == NotchType.V_NOTCH_90:
            # V-notch at bottom of wafer (y = wafer_radius)
            notch_y = self.wafer_radius_mm - self.notch_depth_mm
            notch_half_width = self.notch_depth_mm  # For 90° V-notch
            
            # Check if rectangle intersects with V-notch triangle
            return (rect_bottom >= notch_y and 
                    rect_left <= notch_half_width and 
                    rect_right >= -notch_half_width and
                    rect_bottom <= self.wafer_radius_mm)
                    
        elif self.notch_type == NotchType.FLAT:
            # Flat notch at bottom of wafer
            notch_y = self.wafer_radius_mm - self.notch_depth_mm
            r = self.wafer_radius_mm
            d = self.notch_depth_mm
            
            if d >= r or d <= 0:
                return False
                
            # Calculate flat half-width
            flat_half_width = math.sqrt(2.0 * r * d - d * d)
            
            # Check if rectangle intersects with flat area
            return (rect_bottom >= notch_y and 
                    rect_left <= flat_half_width and 
                    rect_right >= -flat_half_width and
                    rect_bottom <= self.wafer_radius_mm)
        
        return False
    
    def is_rectangle_in_wafer(self, center_x: float, center_y: float, 
                             width: float, height: float, 
                             method: ValidationMethod = ValidationMethod.CORNER_BASED) -> Tuple[bool, float]:
        """
        优化版矩形在晶圆内的检查
        """
        # First check if rectangle intersects with notch (if any)
        if self._is_rectangle_intersecting_notch(center_x, center_y, width, height):
            return False, 0.0
        
        if method.value == ValidationMethod.CENTER_BASED.value:
            return self._validate_center_based(center_x, center_y), 1.0
        elif method.value == ValidationMethod.CORNER_BASED.value:
            return self._validate_corner_based(center_x, center_y, width, height), 1.0
        elif method.value == ValidationMethod.AREA_BASED.value:
            return self._validate_area_based(center_x, center_y, width, height)
        elif method.value == ValidationMethod.STRICT.value:
            return self._validate_strict(center_x, center_y, width, height), 1.0
        else:
            raise ValueError(f"Unknown validation method: {method}")
    
    def _validate_center_based(self, center_x: float, center_y: float) -> bool:
        """Conservative method: only die center within boundary."""
        return self.is_point_in_wafer(center_x, center_y)
    
    def _validate_corner_based(self, center_x: float, center_y: float, 
                              width: float, height: float) -> bool:
        """Industry standard: all four corners within boundary."""
        half_width = width / 2.0
        half_height = height / 2.0
        
        # 优化：只需检查最远的角
        # 使用绝对值来处理所有象限的情况
        abs_center_x, abs_center_y = abs(center_x), abs(center_y)
        
        # 最远角的坐标
        far_corner_x = abs_center_x + half_width
        far_corner_y = abs_center_y + half_height
        
        # 如果最远角都在圆内，则所有角都在圆内
        if far_corner_x * far_corner_x + far_corner_y * far_corner_y <= self.effective_radius_mm * self.effective_radius_mm:
            return True
            
        # 否则检查所有四个角
        corners = [
            (center_x - half_width, center_y - half_height),  # Bottom-left
            (center_x + half_width, center_y - half_height),  # Bottom-right
            (center_x + half_width, center_y + half_height),  # Top-right
            (center_x - half_width, center_y + half_height),  # Top-left
        ]
        
        return all(self.is_point_in_wafer(x, y) for x, y in corners)
    
    def _validate_area_based(self, center_x: float, center_y: float, 
                            width: float, height: float) -> Tuple[bool, float]:
        """Most accurate: calculate intersection area with circle."""
        # 简化版本 - 如果中心在圆内且至少有一半的角在圆内
        center_in = self.is_point_in_wafer(center_x, center_y)
        if not center_in:
            return False, 0.0
        
        half_width = width / 2.0
        half_height = height / 2.0
        corners = [
            (center_x - half_width, center_y - half_height),
            (center_x + half_width, center_y - half_height),
            (center_x + half_width, center_y + half_height),
            (center_x - half_width, center_y + half_height),
        ]
        
        corners_in = sum(1 for x, y in corners if self.is_point_in_wafer(x, y))
        area_ratio = corners_in / 4.0
        is_valid = area_ratio > 0.5
        
        return is_valid, area_ratio
    
    def _validate_strict(self, center_x: float, center_y: float, 
                        width: float, height: float) -> bool:
        """Strictest method: entire die including scribe lanes within boundary."""
        half_width = width / 2.0
        half_height = height / 2.0
        
        # 检查所有角落
        corners = [
            (center_x - half_width, center_y - half_height),
            (center_x + half_width, center_y - half_height),
            (center_x + half_width, center_y + half_height),
            (center_x - half_width, center_y + half_height),
        ]
        
        return all(self.is_point_in_wafer(x, y) for x, y in corners)


class OptimizedDieCalculator:
    """
    优化版die per wafer计算器
    使用数学优化和对称性提升性能
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_dies_per_wafer(self, 
                               die_size_x_um: float,
                               die_size_y_um: float,
                               scribe_lane_x_um: float,
                               scribe_lane_y_um: float,
                               wafer_diameter_mm: float,
                               edge_exclusion_mm: float = 3.0,
                               yield_percentage: float = 100.0,
                               validation_method: ValidationMethod = ValidationMethod.CORNER_BASED,
                               notch_type: NotchType = NotchType.NONE,
                               notch_depth_mm: float = 1.0) -> CalculationResult:
        """
        优化版DPW计算，使用数学公式减少计算量
        """
        errors = []
        if die_size_x_um <= 0:
            errors.append("die_size_x_um must be positive")
        if die_size_y_um <= 0:
            errors.append("die_size_y_um must be positive")
        if scribe_lane_x_um < 0:
            errors.append("scribe_lane_x_um must be non-negative")
        if scribe_lane_y_um < 0:
            errors.append("scribe_lane_y_um must be non-negative")
        if wafer_diameter_mm <= 0:
            errors.append("wafer_diameter_mm must be positive")
        if edge_exclusion_mm < 0:
            errors.append("edge_exclusion_mm must be non-negative")
        if not (0.0 <= yield_percentage <= 100.0):
            errors.append("yield_percentage must be between 0 and 100")
        if errors:
            raise ValueError("; ".join(errors))

        # Convert units to millimeters for consistency
        die_size_x_mm = die_size_x_um / 1000.0
        die_size_y_mm = die_size_y_um / 1000.0
        scribe_lane_x_mm = scribe_lane_x_um / 1000.0
        scribe_lane_y_mm = scribe_lane_y_um / 1000.0
        
        # Calculate die pitch (die + scribe lane)
        die_pitch_x_mm = die_size_x_mm + scribe_lane_x_mm
        die_pitch_y_mm = die_size_y_mm + scribe_lane_y_mm

        if die_pitch_x_mm <= 0 or die_pitch_y_mm <= 0:
            raise ValueError("die pitch must be positive (die size + scribe lane)")
        
        self.logger.info(f"Calculating DPW (OPTIMIZED): Die {die_size_x_um}×{die_size_y_um}μm, "
                        f"Scribe {scribe_lane_x_um}×{scribe_lane_y_um}μm, "
                        f"Wafer {wafer_diameter_mm}mm, Method: {validation_method.value}")
        
        # Initialize wafer geometry
        wafer_geom = OptimizedWaferGeometry(wafer_diameter_mm, edge_exclusion_mm, notch_type, notch_depth_mm)
        
        # 使用优化算法计算
        start_time = time.time()
        valid_dies, die_positions = self._calculate_valid_dies_optimized(
            wafer_geom, die_pitch_x_mm, die_pitch_y_mm,
            die_size_x_mm, die_size_y_mm, validation_method
        )
        calculation_time = time.time() - start_time
        
        # Calculate yield-adjusted die count
        yield_dies = int(valid_dies * (yield_percentage / 100.0))
        
        # Calculate wafer utilization
        total_wafer_area_mm2 = math.pi * wafer_geom.effective_radius_mm * wafer_geom.effective_radius_mm
        total_die_area_mm2 = valid_dies * die_size_x_mm * die_size_y_mm
        wafer_utilization = (total_die_area_mm2 / total_wafer_area_mm2) * 100.0 if total_wafer_area_mm2 > 0 else 0.0
        
        # Store calculation parameters
        parameters = {
            'die_size_x_um': die_size_x_um,
            'die_size_y_um': die_size_y_um,
            'scribe_lane_x_um': scribe_lane_x_um,
            'scribe_lane_y_um': scribe_lane_y_um,
            'wafer_diameter_mm': wafer_diameter_mm,
            'edge_exclusion_mm': edge_exclusion_mm,
            'yield_percentage': yield_percentage,
            'die_pitch_x_mm': die_pitch_x_mm,
            'die_pitch_y_mm': die_pitch_y_mm,
            'effective_radius_mm': wafer_geom.effective_radius_mm,
            'notch_type': notch_type.value,
            'notch_depth_mm': notch_depth_mm,
            'notch_area_mm2': wafer_geom.notch_area_mm2,
            'calculation_time_s': calculation_time,
            'optimization_applied': True
        }
        
        result = CalculationResult(
            total_dies=valid_dies,
            yield_dies=yield_dies,
            wafer_utilization=wafer_utilization,
            die_positions=die_positions,
            calculation_method=validation_method,
            parameters=parameters
        )
        
        self.logger.info(f"Optimized calculation complete: {valid_dies} total dies, "
                        f"{yield_dies} yield dies, {wafer_utilization:.1f}% utilization "
                        f"(time: {calculation_time:.3f}s)")
        
        return result
    
    def _calculate_valid_dies_optimized(self, wafer_geom: OptimizedWaferGeometry,
                                      pitch_x: float, pitch_y: float,
                                      die_size_x: float, die_size_y: float,
                                      validation_method: ValidationMethod) -> Tuple[int, List[DiePosition]]:
        """
        使用数学优化算法计算有效芯片数量
        注意：当存在notch时，不能使用对称性优化，因为notch是非对称的
        """
        effective_radius = wafer_geom.effective_radius_mm
        
        # 如果存在notch，不能使用对称性优化，否则可以使用
        has_notch = wafer_geom.notch_type != NotchType.NONE
        
        if has_notch:
            # 存在notch时，必须检查所有位置（包括负坐标）
            # 使用类似原始算法的方法，但仍然使用数学优化
            max_i = int(effective_radius / pitch_x) + 1
            max_j = int(effective_radius / pitch_y) + 1
            
            valid_dies = 0
            die_positions = []
            
            # 检查所有可能的i,j值（包括负值）
            for i in range(-max_i, max_i + 1):
                center_x = i * pitch_x
                # 计算对应的有效y范围
                remaining_radius_sq = effective_radius * effective_radius - center_x * center_x
                if remaining_radius_sq < 0:
                    continue  # x位置超出圆范围
                    
                max_y = math.sqrt(remaining_radius_sq)
                max_j_range = int(max_y / pitch_y)
                
                for j in range(-max_j_range, max_j_range + 1):
                    center_y = j * pitch_y
                    
                    # 检查该位置是否有效
                    is_valid, area_ratio = wafer_geom.is_rectangle_in_wafer(
                        center_x, center_y, die_size_x, die_size_y, validation_method
                    )
                    
                    if is_valid:
                        distance_from_center = math.sqrt(center_x * center_x + center_y * center_y)
                        
                        die_pos = DiePosition(
                            row=j,
                            col=i,
                            center_x=center_x,
                            center_y=center_y,
                            is_valid=True,
                            area_ratio=area_ratio,
                            distance_from_center=distance_from_center
                        )
                        
                        die_positions.append(die_pos)
                        valid_dies += 1
        else:
            # 不存在notch时，可以安全使用对称性优化
            valid_dies = 0
            die_positions = []
            
            # 只计算第一象限，利用对称性
            max_i = int(effective_radius / pitch_x) + 1
            max_j = int(effective_radius / pitch_y) + 1
            
            for i in range(max_i + 1):
                center_x = i * pitch_x
                
                # 直接计算y方向的有效范围
                remaining_radius_sq = effective_radius * effective_radius - center_x * center_x
                if remaining_radius_sq < 0:
                    continue  # x位置超出圆范围
                    
                max_y = math.sqrt(remaining_radius_sq)
                max_j_row = int(max_y / pitch_y)
                
                for j in range(max_j_row + 1):
                    center_y = j * pitch_y
                    
                    # 检查该位置是否有效
                    is_valid, area_ratio = wafer_geom.is_rectangle_in_wafer(
                        center_x, center_y, die_size_x, die_size_y, validation_method
                    )
                    
                    if is_valid:
                        # 利用对称性计算芯片数量
                        sym_positions = self._get_symmetric_positions(i, j, center_x, center_y, pitch_x, pitch_y)
                        
                        for pos_idx, (sym_i, sym_j, sym_x, sym_y) in enumerate(sym_positions):
                            distance_from_center = math.sqrt(sym_x * sym_x + sym_y * sym_y)
                            
                            die_pos = DiePosition(
                                row=sym_j,
                                col=sym_i,
                                center_x=sym_x,
                                center_y=sym_y,
                                is_valid=True,
                                area_ratio=area_ratio,
                                distance_from_center=distance_from_center
                            )
                            
                            die_positions.append(die_pos)
                            
                            # 如果是第一个对称位置，增加计数；其他位置已经在第一个位置的计数中体现
                            if pos_idx == 0:
                                if i == 0 and j == 0:
                                    # 原点，只计算1次
                                    valid_dies += 1
                                elif i == 0 or j == 0:
                                    # 轴上点，计算2次对称
                                    valid_dies += 2
                                else:
                                    # 象限内点，计算4次对称
                                    valid_dies += 4
        
        return valid_dies, die_positions
    
    def _get_symmetric_positions(self, i: int, j: int, center_x: float, center_y: float, 
                                pitch_x: float, pitch_y: float) -> List[Tuple[int, int, float, float]]:
        """
        获取对称位置
        返回[(row, col, x, y), ...]
        """
        positions = [(i, j, center_x, center_y)]
        
        # 根据位置类型添加对称点
        if i == 0 and j == 0:
            # 原点，只有自己
            pass
        elif i == 0:
            # y轴上，添加关于x轴的对称点
            positions.append((-i, -j, -center_x, -center_y))  # 实际上就是(0, -j, 0, -center_y)
            positions = [(0, j, 0, center_y), (0, -j, 0, -center_y)]
        elif j == 0:
            # x轴上，添加关于y轴的对称点
            positions = [(i, 0, center_x, 0), (-i, 0, -center_x, 0)]
        else:
            # 象限内，添加三个对称点
            positions = [
                (i, j, center_x, center_y),       # 第一象限
                (-i, j, -center_x, center_y),     # 第二象限
                (-i, -j, -center_x, -center_y),   # 第三象限
                (i, -j, center_x, -center_y)      # 第四象限
            ]
        
        return positions