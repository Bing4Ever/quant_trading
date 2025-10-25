#!/usr/bin/env python3
"""交易引擎启动脚本"""

import sys
from pathlib import Path

# 添加项目根目录到路径  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tradingservice.services.engines.quick_trading_engine import main

if __name__ == "__main__":
    main()