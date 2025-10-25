# 🎯 量化交易系统

> **企业级量化交易平台** - 支持策略开发、回测、自动化执行、风险管理

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心特性

- 🚀 **RESTful API** - 完整的API支持，可集成任何前端
- 📊 **多种策略** - MA、RSI、MACD、Bollinger等6+种策略
- ⚡ **自动化交易** - 任务调度、定时执行、实时监控
- 📈 **回测引擎** - 历史数据回测、性能分析
- 💼 **投资组合管理** - 组合优化、风险评估
- 🛡️ **风险管理** - VaR、CVaR、风险限额
- 🎨 **双界面** - Streamlit快速测试 + API生产部署

## 🚀 快速开始

### 方式1: API服务器（推荐）

```bash
# 1. 安装依赖
pip install -r requirements_api.txt

# 2. 启动服务器
python app.py

# 3. 访问文档
浏览器打开: http://localhost:8000/docs
```

### 方式2: Streamlit界面

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动界面
streamlit run streamlit_app.py
```

**详细指南**: 查看 [`docs/QUICKSTART.md`](docs/QUICKSTART.md)

## 📚 文档

| 文档 | 说明 |
|------|------|
| [快速开始](docs/QUICKSTART.md) | 3分钟上手指南 |
| [架构设计](docs/ARCHITECTURE.md) | 系统架构说明 |
| [API指南](docs/API_DEPLOYMENT.md) | API使用和部署 |
| [任务管理](docs/TASK_MANAGEMENT_GUIDE.md) | 自动化任务指南 |
| [中文指南](docs/README_实战指南.md) | 完整中文教程 |

**查看所有文档**: [`docs/README.md`](docs/README.md)

## 📁 项目结构

```
quant_trading/
├── api/                    # API层（Models, Routes, Services）
├── automation/             # 任务调度和自动化
├── strategies/             # 交易策略实现
├── portfolio/              # 投资组合管理
├── risk_management/        # 风险管理
├── backtesting/           # 回测引擎
├── data/                  # 数据获取和存储
├── trading/               # 交易执行
├── docs/                  # 📚 所有文档
├── scripts/               # 🔧 启动和演示脚本
├── tests/                 # 🧪 测试代码
├── app.py                 # ⭐ API主入口
├── streamlit_app.py       # ⭐ Streamlit界面
└── README.md             # 本文件
```

## 🎯 API端点

```
任务管理:
  GET    /api/tasks              获取所有任务
  POST   /api/tasks              创建任务
  DELETE /api/tasks/{id}         删除任务
  POST   /api/tasks/{id}/execute 执行任务

调度器:
  GET  /api/scheduler/status     获取状态
  POST /api/scheduler/start      启动调度器
  POST /api/scheduler/stop       停止调度器

策略分析:
  POST /api/strategies/analyze         单股票分析
  POST /api/strategies/batch-analyze   批量分析
  GET  /api/strategies/available       可用策略

系统:
  GET /health                    健康检查
  GET /docs                      Swagger文档
```

**完整API文档**: 启动后访问 http://localhost:8000/docs

## 💡 使用示例

### Python

```python
import requests

# 创建任务
response = requests.post("http://localhost:8000/api/tasks", json={
    "name": "每日AAPL分析",
    "frequency": "daily",
    "symbols": ["AAPL", "MSFT"],
    "strategies": ["all"]
})

# 启动调度器
requests.post("http://localhost:8000/api/scheduler/start")
```

### JavaScript

```javascript
// 创建任务
await fetch('http://localhost:8000/api/tasks', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: '每日AAPL分析',
        frequency: 'daily',
        symbols: ['AAPL', 'MSFT'],
        strategies: ['all']
    })
});
```

### curl

```bash
# 创建任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name":"每日分析","frequency":"daily","symbols":["AAPL"],"strategies":["all"]}'
```

## 🌐 部署

### Docker

```bash
docker build -t trading-api .
docker run -p 8000:8000 trading-api
```

### 云服务

支持部署到:
- AWS EC2
- Google Cloud Run
- Heroku
- Azure

**详细指南**: [`docs/API_DEPLOYMENT.md`](docs/API_DEPLOYMENT.md)

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | FastAPI, Python 3.11+ |
| **数据** | yfinance, pandas, numpy |
| **分析** | scikit-learn, scipy |
| **界面** | Streamlit (可选) |
| **部署** | Uvicorn, Docker |

## 📊 支持的策略

- ✅ **MA Crossover** - 移动平均线交叉
- ✅ **RSI** - 相对强弱指标
- ✅ **MACD** - 移动平均收敛散度
- ✅ **Bollinger Bands** - 布林带
- ✅ **Mean Reversion** - 均值回归
- ✅ **Momentum** - 动量策略

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_strategies.py

# 查看覆盖率
pytest --cov=api tests/
```

## 📈 性能

- ⚡ **并行处理** - 批量分析支持多线程
- ⚡ **异步API** - 高并发支持
- ⚡ **缓存优化** - 数据智能缓存
- ⚡ **负载均衡** - 支持多worker部署

## 🔒 安全

- ✅ CORS配置
- ✅ 输入验证
- ✅ 异常处理
- 🔲 JWT认证（可选启用）
- 🔲 API限流（可配置）

## 🤝 贡献

欢迎贡献！请遵循以下步骤:

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📝 许可证

本项目采用 [MIT License](LICENSE)

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [yfinance](https://github.com/ranaroussi/yfinance) - 金融数据
- [Streamlit](https://streamlit.io/) - 快速UI开发

## 📞 支持

- 📖 **文档**: [`docs/`](docs/)
- 🐛 **问题**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **讨论**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**项目状态**: ✅ 生产就绪  
**最后更新**: 2025-10-22  
**版本**: 1.0.0

Made with ❤️ for quantitative traders
