"""GB/T 8170 数值修约 (四舍六入五成双)"""
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation

def round_gb8170(value: float, interval: float = 0.1) -> float:
    if value != value:
        raise ValueError("NaN value")
    d = Decimal(str(value))
    scale = Decimal(str(interval))
    rounded = (d / scale).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN) * scale
    return float(rounded)
