import sys
from datetime import date, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from automation.report_generator import ReportGenerator, AutoReportScheduler
from utils.logger import TradingLogger


def test_report_generator():
    """测试报告生成器"""
    
    print("🧪 开始测试报告生成器...")
    
    try:
        # 创建报告生成器
        generator = ReportGenerator()
        
        # 测试日报生成
        print("\n📊 测试日报生成...")
        daily_report = generator.generate_daily_report()
        print(f"✅ 日报生成成功: {daily_report}")
        
        # 测试周报生成
        print("\n📈 测试周报生成...")
        weekly_report = generator.generate_weekly_report()
        print(f"✅ 周报生成成功: {weekly_report}")
        
        # 测试月报生成
        print("\n📋 测试月报生成...")
        monthly_report = generator.generate_monthly_report()
        print(f"✅ 月报生成成功: {monthly_report}")
        
        # 检查生成的文件
        reports_dir = Path("reports")
        if reports_dir.exists():
            report_files = list(reports_dir.glob("*.html"))
            print(f"\n📁 生成的报告文件数: {len(report_files)}")
            for file in report_files[-3:]:  # 显示最新的3个文件
                print(f"   📄 {file.name}")
        
        print("✅ 报告生成器测试完成!")
        return True
        
    except (ImportError, FileNotFoundError, ValueError) as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_scheduler():
    """测试调度器"""
    print("\n🕒 测试报告调度器...")
    
    try:
        scheduler = AutoReportScheduler()
        
        # 测试调度设置（不实际运行）
        print("设置日报调度...")
        scheduler.schedule_daily_reports("18:00")
        
        print("设置周报调度...")
        scheduler.schedule_weekly_reports("monday", "09:00")
        
        print("设置月报调度...")
        scheduler.schedule_monthly_reports(1, "09:00")
        
        print("✅ 调度器设置完成!")
        return True
        
    except (ImportError, AttributeError) as e:
        print(f"❌ 调度器测试失败: {e}")
        return False


def create_sample_data():
    """创建示例数据用于测试"""
    print("\n🗄️ 创建示例数据...")
    
    try:
        import random
        
        # 插入一些示例回测结果
        sample_results = []
        strategies = ['RSI策略', 'MA策略', 'Bollinger策略', '均值回归策略']
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
        
        for i in range(10):
            result = {
                'id': f'test_{i}',
                'strategy_name': random.choice(strategies),
                'symbol': random.choice(symbols),
                'start_date': date.today() - timedelta(days=random.randint(1, 30)),
                'end_date': date.today(),
                'total_return': random.uniform(-0.1, 0.2),
                'sharpe_ratio': random.uniform(0.5, 2.0),
                'max_drawdown': random.uniform(0.02, 0.15),
                'parameters': {'period': random.randint(10, 30)}
            }
            sample_results.append(result)
        
        print(f"✅ 创建了 {len(sample_results)} 条示例数据")
        return True
        
    except (ImportError, ValueError) as e:
        print(f"❌ 创建示例数据失败: {e}")
        return False


def demo_reports():
    """演示报告功能"""
    print("\n🎯 报告生成演示")
    print("=" * 50)
    
    # 测试基本功能
    if test_report_generator():
        print("\n✅ 基础功能测试通过!")
    else:
        print("\n❌ 基础功能测试失败!")
        return
    
    # 测试调度器
    if test_scheduler():
        print("\n✅ 调度器测试通过!")
    else:
        print("\n❌ 调度器测试失败!")
    
    # 显示生成的报告
    reports_dir = Path("reports")
    if reports_dir.exists():
        print(f"\n📁 报告目录: {reports_dir.absolute()}")
        print("📄 生成的报告文件:")
        for file in reports_dir.glob("*.html"):
            size = file.stat().st_size / 1024  # KB
            print(f"   • {file.name} ({size:.1f} KB)")
    
    print("\n🎉 报告生成器演示完成!")
    print("\n💡 提示:")
    print("   • 报告已保存在 reports/ 目录下")
    print("   • 可以用浏览器打开HTML文件查看")
    print("   • 支持自动调度生成日报、周报、月报")


if __name__ == "__main__":
    # 运行演示
    demo_reports()