#!/usr/bin/env python3
"""
简单启动脚本 - 直接在当前终端运行
"""

import os
import sys
from pathlib import Path

def main():
    """主函数"""
    print("🚀 启动量化交易系统 (当前终端模式)")
    print("=" * 50)
    
    # 确保在正确目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 创建必要目录
    for directory in ['data', 'logs', 'exports']:
        Path(directory).mkdir(exist_ok=True)
    
    print("🌐 启动Streamlit应用...")
    print("🔗 访问地址: http://localhost:8502")
    print("📝 按 Ctrl+C 停止服务")
    print("=" * 50)
    
    try:
        # 直接运行streamlit模块，使用8502端口
        os.system(f"{sys.executable} -m streamlit run streamlit_app.py --server.port 8502")
    except KeyboardInterrupt:
        print("\n👋 系统已停止")

if __name__ == "__main__":
    main()