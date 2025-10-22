#!/usr/bin/env python3
"""
量化交易系统启动脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """检查必要的依赖"""
    required_packages = {
        'streamlit': 'streamlit',
        'pandas': 'pandas', 
        'numpy': 'numpy',
        'yfinance': 'yfinance',
        'plotly': 'plotly',
        'scikit-learn': 'sklearn'  # scikit-learn包导入名为sklearn
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ 缺少必要的依赖包: {', '.join(missing_packages)}")
        print(f"请运行: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖包检查通过")
    return True

def setup_environment():
    """设置环境"""
    # 确保在正确的目录中
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 创建必要的目录
    directories = [
        'data',
        'automation',
        'logs',
        'exports',
        'backtest_results'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ 环境设置完成")

def main():
    """主函数"""
    print("🚀 启动量化交易系统...")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 启动Streamlit应用
    print("🌐 启动Web界面...")
    print("🔗 浏览器将自动打开 http://localhost:8501")
    print("📝 按 Ctrl+C 停止服务")
    print("=" * 50)
    
    try:
        # 直接在当前进程中运行Streamlit，而不是启动新进程
        import streamlit.web.cli as stcli
        import sys
        
        # 设置Streamlit参数
        sys.argv = [
            "streamlit",
            "run", 
            "streamlit_app.py",
            "--server.port", "8501",
            "--server.headless", "false", 
            "--browser.gatherUsageStats", "false"
        ]
        
        # 直接运行Streamlit
        stcli.main()
        
    except KeyboardInterrupt:
        print("\n👋 系统已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        # 如果直接运行失败，回退到subprocess方式
        print("🔄 尝试使用subprocess方式启动...")
        try:
            subprocess.run([
                sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
                '--server.port', '8501',
                '--server.headless', 'false',
                '--browser.gatherUsageStats', 'false'
            ])
        except Exception as e2:
            print(f"❌ 启动失败: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    main()