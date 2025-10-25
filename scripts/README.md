# 🔧 脚本工具集

本目录包含项目的各种脚本和工具。

## 🚀 启动脚本

### API服务器
- **start_api.bat** - Windows启动API服务器
- **start_api.sh** - Linux/macOS启动API服务器

使用方法:
```bash
# Windows
.\scripts\start_api.bat

# Linux/macOS
chmod +x scripts/start_api.sh
./scripts/start_api.sh
```

### 交易引擎
- **run_quick_trading.py** - 快速交易引擎
- **run_live_trading.py** - 实时交易引擎
- **run_advanced_trading.py** - 高级交易引擎

使用方法:
```bash
python scripts/run_quick_trading.py
```

## 🔧 工具脚本

- **launcher.py** - 通用启动器
- **simple_test.py** - 简单测试工具
- **ui_update_summary.py** - UI更新总结
- **fix_risk_metrics_whitespace.py** - 修复空格问题

## 📂 脚本结构

```
scripts/
├── README.md                      # 本文件
├── start_api.bat                  # API启动（Windows）⭐
├── start_api.sh                   # API启动（Linux）⭐
├── run_quick_trading.py           # 快速交易 ⭐
├── run_live_trading.py            # 实时交易
├── run_advanced_trading.py        # 高级交易
├── launcher.py                    # 启动器
├── simple_test.py                 # 测试工具
├── ui_update_summary.py           # UI总结
├── verify_dataaccess_migration.py # 验证迁移
└── fix_risk_metrics_whitespace.py # 修复工具
```

> 💡 **演示程序已移至 `demos/` 目录**
> 
> 如需运行演示程序，请查看：
> - `demos/new_architecture_demo.py` - 架构演示
> - `demos/backtest_demo.py` - 回测演示
> - `demos/optimization_demo.py` - 优化演示
> - 更多详情见 [demos/README.md](../demos/README.md)

## 🎯 常用操作

### 启动API（推荐用于生产）
```bash
# 方式1: 使用启动脚本
.\scripts\start_api.bat

# 方式2: 直接运行
python app.py
```

### 启动Streamlit界面
```bash
streamlit run streamlit_app.py
```

### 运行回测
```bash
python scripts/demo_backtest.py
```

### 测试系统
```bash
python scripts/simple_test.py
```

## 💡 使用提示

1. **所有脚本都应该从项目根目录运行**
2. **确保已激活conda环境**: `conda activate quanttrading`
3. **演示脚本不需要实际市场数据**

## 📝 添加新脚本

如果需要添加新的脚本工具:
1. 将脚本放到此目录
2. 更新本README
3. 确保脚本有适当的注释

---

**脚本总数**: 13个文件  
**最后更新**: 2025-10-22
