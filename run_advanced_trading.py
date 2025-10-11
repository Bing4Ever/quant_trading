#!/usr/bin/env python3
"""高级交易引擎启动脚本"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trading.advanced_trading_engine import main

if __name__ == "__main__":
    main()