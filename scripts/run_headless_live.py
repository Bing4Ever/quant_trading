#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无人值守的实时交易启动脚本。

基于 LiveTradingRuntime，自动加载行情→生成信号→执行下单→定期对账，
适合在服务器/容器中长期运行。
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import List

# 确保可以导入 src 包
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.tradingservice.services.automation.live_runtime import LiveTradingRuntime


def _parse_symbols(raw: str) -> List[str]:
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Headless live trading runtime (Alpaca ready)."
    )
    parser.add_argument(
        "--symbols",
        default=os.getenv("LIVE_SYMBOLS", "AAPL,MSFT,GOOGL"),
        help="逗号分隔的监控标的列表，默认读取 LIVE_SYMBOLS 环境变量。",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("LIVE_PROVIDER", "alpaca"),
        help="行情/交易数据提供方，默认 alpaca。",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.getenv("LIVE_POLL_INTERVAL", "5")),
        help="行情轮询间隔（秒）。",
    )
    parser.add_argument(
        "--reconcile-interval",
        type=int,
        default=int(os.getenv("LIVE_RECONCILE_INTERVAL", "30")),
        help="对账巡检间隔（秒）。",
    )
    parser.add_argument(
        "--log-file",
        default=os.getenv("LIVE_LOG_FILE", "logs/live_runtime.log"),
        help="日志输出文件路径。",
    )
    return parser


class RuntimeService:
    """封装运行与优雅停止逻辑。"""

    def __init__(self, runtime: LiveTradingRuntime, reconcile_interval: int) -> None:
        self.runtime = runtime
        self.reconcile_interval = reconcile_interval
        self._running = False

    def start(self, symbols: List[str]) -> None:
        self.runtime.start(symbols=symbols)
        self._running = True

    def stop(self) -> None:
        if self._running:
            self.runtime.stop()
            self._running = False

    def run_forever(self) -> None:
        while self._running:
            try:
                updates = self.runtime.reconcile_now()
                if updates:
                    logging.info("Reconciled orders: %s", len(updates))
                time.sleep(self.reconcile_interval)
            except KeyboardInterrupt:  # pragma: no cover - 外部信号
                logging.info("Received KeyboardInterrupt, shutting down...")
                self.stop()
            except Exception as exc:  # pragma: no cover - 防御性
                logging.exception("Runtime loop error: %s", exc)
                time.sleep(self.reconcile_interval)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    if not symbols:
        parser.error("监控标的列表为空，请通过 --symbols 指定。")

    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(args.log_file, encoding="utf-8"),
        ],
    )

    runtime = LiveTradingRuntime(
        provider=args.provider,
        poll_interval=args.poll_interval,
    )
    service = RuntimeService(runtime, args.reconcile_interval)

    def _handle_signal(signum, _frame):
        logging.info("Received signal %s, stopping runtime...", signum)
        service.stop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _handle_signal)

    logging.info(
        "Starting headless live runtime | provider=%s | symbols=%s",
        args.provider,
        ", ".join(symbols),
    )
    service.start(symbols)
    service.run_forever()
    logging.info("Live runtime stopped.")


if __name__ == "__main__":
    main()
