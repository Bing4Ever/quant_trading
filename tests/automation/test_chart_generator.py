#!/usr/bin/env python3
"""
针对 InteractiveChartGenerator 的自动化测试。

这里通过确定性的 OHLCV 数据避免真实 API 调用。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tradingservice.services.presentation.chart_generator import (
    InteractiveChartGenerator,
)


@dataclass
class StubDataProvider:
    """模拟 DataProvider.get_historical_data 的简单桩对象。"""

    frame: pd.DataFrame

    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        return self.frame


def _sample_ohlcv(days: int = 30) -> pd.DataFrame:
    """
    根据指定天数构造满足图表生成器字段约束的确定性 OHLCV 数据。
    """
    end_dt = datetime(2025, 1, 30)
    index = pd.date_range(end=end_dt, periods=days, freq="D")

    prices = pd.Series(range(100, 100 + days), index=index).astype(float)
    data = pd.DataFrame(
        {
            "Open": prices - 0.5,
            "High": prices + 1.0,
            "Low": prices - 1.0,
            "Close": prices,
            "Volume": 1_000_000,
        },
        index=index,
    )
    return data


def test_create_price_signal_chart_returns_figure():
    """当存在有效数据时，图表生成器应返回 Matplotlib 图像对象。"""
    sample_frame = _sample_ohlcv()
    stub_provider = StubDataProvider(frame=sample_frame)

    generator = InteractiveChartGenerator(data_provider=stub_provider)
    figure = generator.create_price_signal_chart("MOCK")

    assert figure is not None, "应在有效数据下得到 Matplotlib 图像"

    # 关闭图像，避免测试结束时后台发出警告
    plt.close(figure)
