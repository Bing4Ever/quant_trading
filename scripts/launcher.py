#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量化交易系统主启动器 - 提供统一的交易引擎启动界面"""

import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


# 常量定义
RETURN_TO_MENU_MSG = "返回主菜单..."
MENU_SEPARATOR = "=" * 60


def display_main_menu():
    """显示主菜单"""
    print(f"\n{MENU_SEPARATOR}")
    print("🚀 量化交易系统")
    print(MENU_SEPARATOR)
    print("请选择要启动的交易引擎:")
    print()
    print("1. 快速交易引擎 (QuickTradingEngine)")
    print("   - 快速测试和演示")
    print("   - 支持实时价格和信号分析")
    print("   - 简单的交互式操作")
    print()
    print("2. 实时交易引擎 (LiveTradingEngine)")
    print("   - 完整的实时交易功能")
    print("   - 支持定时任务和回测分析")
    print("   - 交互式菜单界面")
    print()
    print("3. 高级交易引擎 (AdvancedTradingEngine)")
    print("   - 集成风险管理模块")
    print("   - 自动化交易和监控")
    print("   - 生产级别的交易系统")
    print()
    print("4. 运行测试套件")
    print("   - 验证所有模块功能")
    print()
    print("0. 退出")
    print(MENU_SEPARATOR)


def handle_choice(choice: str) -> bool:
    """
    处理用户选择

    Args:
        choice (str): 用户输入的选择

    Returns:
        bool: 是否继续运行程序
    """
    if choice == "0":
        print("再见！")
        return False

    if choice == "1":
        print("\n启动快速交易引擎...")
        # pylint: disable=import-outside-toplevel
        from src.tradingservice.services.engines.quick_trading_engine import main as quick_main

        quick_main()
    elif choice == "2":
        print("\n启动实时交易引擎...")
        # pylint: disable=import-outside-toplevel
        from src.tradingservice.services.engines.live_trading_engine import main as live_main

        live_main()
    elif choice == "3":
        print("\n启动高级交易引擎...")
        # pylint: disable=import-outside-toplevel
        from src.tradingservice.services.engines.advanced_trading_engine import main as advanced_main

        advanced_main()
    elif choice == "4":
        print("\n运行测试套件...")
        subprocess.run([sys.executable, "tests/run_tests.py"], check=False)
    else:
        print("无效选择，请重新输入")

    return True


def main():
    """主函数 - 启动量化交易系统主菜单"""
    while True:
        try:
            display_main_menu()
            choice = input("\n请选择 (0-4): ").strip()

            if not handle_choice(choice):
                break

        except KeyboardInterrupt:
            print("\n\n程序已停止")
            break
        except ImportError as error:
            print(f"\n模块导入错误: {error}")
            print(RETURN_TO_MENU_MSG)
        except FileNotFoundError as error:
            print(f"\n文件未找到: {error}")
            print(RETURN_TO_MENU_MSG)
        except OSError as error:
            print(f"\n系统错误: {error}")
            print(RETURN_TO_MENU_MSG)


if __name__ == "__main__":
    main()
