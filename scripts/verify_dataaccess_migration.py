#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证数据访问层迁移
测试新的 Repository 模式架构
"""

from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_common_infrastructure():
    """测试公共基础设施"""
    print("\n🔧 测试公共基础设施...")
    
    try:
        from src.common.dataaccess import OrmBase, DatabaseEngine, BaseRepository
        print("  ✅ 公共基础设施导入成功")
        print(f"     - OrmBase: {OrmBase}")
        print(f"     - DatabaseEngine: {DatabaseEngine}")
        print(f"     - BaseRepository: {BaseRepository}")
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False


def test_tradingservice_dataaccess():
    """测试 TradingService dataaccess"""
    print("\n📊 测试 TradingService 数据访问层...")
    
    try:
        from src.tradingservice import (
            get_backtest_repository,
            get_optimization_repository,
            get_favorite_repository,
            get_strategy_comparison_repository
        )
        print("  ✅ TradingService 仓库导入成功")
        
        # 测试实例化
        backtest_repo = get_backtest_repository()
        print(f"     - BacktestRepository: {backtest_repo}")
        
        # 测试查询（不添加数据）
        count = backtest_repo.count()
        print(f"     - 回测记录数: {count}")
        
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tradingagent_dataaccess():
    """测试 TradingAgent dataaccess"""
    print("\n🤖 测试 TradingAgent 数据访问层...")
    
    try:
        from src.tradingagent.dataaccess import (
            MarketDataRepository,
            StockData,
            DataUpdate
        )
        print("  ✅ TradingAgent 数据访问层导入成功")
        print(f"     - MarketDataRepository: {MarketDataRepository}")
        print(f"     - StockData: {StockData}")
        print(f"     - DataUpdate: {DataUpdate}")
        
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backtest_analytics():
    """测试 BacktestAnalytics 迁移"""
    print("\n📈 测试 BacktestAnalytics 迁移...")
    
    try:
        from src.tradingservice import BacktestAnalytics
        print("  ✅ BacktestAnalytics 导入成功")
        
        # 测试实例化
        analytics = BacktestAnalytics()
        print(f"     - BacktestAnalytics 实例: {analytics}")
        
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_legacy_compatibility():
    """测试向后兼容性"""
    print("\n🔄 测试向后兼容性...")
    
    try:
        from src.tradingservice import BacktestDatabase
        if BacktestDatabase is None:
            print("  ⚠️  BacktestDatabase 已废弃（预期行为）")
            print("     使用 get_backtest_repository() 和 BacktestAnalytics")
        else:
            print(f"  ⚠️  BacktestDatabase 仍然可用: {BacktestDatabase}")
        
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def main():
    """主测试流程"""
    print("=" * 60)
    print("🚀 数据访问层迁移验证")
    print("=" * 60)
    
    results = {
        "公共基础设施": test_common_infrastructure(),
        "TradingService 数据访问": test_tradingservice_dataaccess(),
        "TradingAgent 数据访问": test_tradingagent_dataaccess(),
        "BacktestAnalytics 迁移": test_backtest_analytics(),
        "向后兼容性": test_legacy_compatibility()
    }
    
    print("\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:30s} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有测试通过！数据访问层迁移成功！")
        print("\n架构摘要:")
        print("  ├── common/dataaccess/          # 共享基础设施")
        print("  │   ├── orm_base.py             # ORM 基类")
        print("  │   ├── database_engine.py      # 数据库引擎")
        print("  │   └── base_repository.py      # 基础仓库")
        print("  │")
        print("  ├── tradingservice/dataaccess/  # 业务数据")
        print("  │   ├── models/                 # 4 个业务模型")
        print("  │   └── repositories/           # 4 个业务仓库")
        print("  │")
        print("  └── tradingagent/.../dataaccess/ # 市场数据缓存")
        print("      ├── models/                 # 2 个缓存模型")
        print("      └── repositories/           # 1 个市场数据仓库")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit(main())
