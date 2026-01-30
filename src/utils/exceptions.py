"""
DPW自定义异常

定义DPW计算工具的异常层次结构，用于更精确的错误处理。
"""


class DPWException(Exception):
    """DPW基础异常类"""
    pass


class ParameterValidationError(DPWException):
    """参数验证错误

    当输入参数不符合要求时抛出，例如：
    - 负数或零值
    - 超出有效范围
    - 类型错误
    """
    pass


class CalculationError(DPWException):
    """计算过程错误

    当计算过程中发生错误时抛出，例如：
    - 几何计算失败
    - 数值溢出
    - 内部逻辑错误
    """
    pass


class ReportGenerationError(DPWException):
    """报告生成错误

    当生成HTML报告或可视化时发生错误，例如：
    - 模板文件缺失
    - 文件写入失败
    - 渲染错误
    """
    pass


class APIError(DPWException):
    """API调用错误

    当API接口调用失败时抛出，例如：
    - HTTP请求错误
    - 响应格式错误
    - 超时
    """
    pass
