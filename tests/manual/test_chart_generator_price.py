#!/usr/bin/env python3
"""
用于手动验证 `InteractiveChartGenerator` 价格/信号图生成的脚本。

默认生成 AAPL 图表并保存到 charts/ 目录，可供人工检查图形输出。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:  # Ensure pytest skips this manual script during automated runs
    import pytest

    pytestmark = pytest.mark.skip("manual script; run directly via python")
except ImportError:  # pragma: no cover - pytest not available
    pytestmark = None  # type: ignore[assignment]

import importlib.util

def _load_chart_generator():
    module_path = PROJECT_ROOT / "src" / "tradingservice" / "services" / "presentation" / "chart_generator.py"
    spec = importlib.util.spec_from_file_location("chart_generator_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module

chart_generator_module = _load_chart_generator()
InteractiveChartGenerator = chart_generator_module.InteractiveChartGenerator


def run(symbol: str = "AAPL", output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    生成指定标的的价格/信号图，并写入磁盘。

    返回生成成功后的文件路径；若生成失败则返回 None 并输出提示。
    """
    chart_generator = InteractiveChartGenerator()
    figure = chart_generator.create_price_signal_chart(symbol)

    if figure is None:
        print(f"[FAIL] No chart produced for symbol {symbol}")
        return None

    destination_dir = output_dir or Path("charts")
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination = destination_dir / f"{symbol}_price_signal.png"
    figure.savefig(destination, dpi=200, bbox_inches="tight")
    plt.close(figure)

    print(f"[OK] Saved price/signal chart for {symbol} to {destination}")
    return destination


if __name__ == "__main__":
    run()
