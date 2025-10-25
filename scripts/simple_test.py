#!/usr/bin/env python3
# 简化的报告生成器测试

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def simple_test():
    """简化测试"""
    try:
        from automation.report_generator import ReportGenerator
        
        print("Creating report generator...")
        generator = ReportGenerator()
        
        print("Generating daily report...")
        daily_report = generator.generate_daily_report()
        
        print(f"✅ Daily report generated: {daily_report}")
        
        # 检查文件是否存在
        if os.path.exists(daily_report):
            file_size = os.path.getsize(daily_report)
            print(f"✅ Report file size: {file_size} bytes")
        else:
            print("❌ Report file not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Simple Report Generator Test")
    print("=" * 40)
    
    if simple_test():
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")