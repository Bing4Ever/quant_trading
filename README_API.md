# 🎯 量化交易系统 - API层提取完成

> **重大更新**: 系统已完成前后端分离架构升级！现在支持RESTful API和现代前端框架集成。

## 📁 项目结构

```
quant_trading/
├── api/                        # ⭐ API层（新增）
│   ├── models/                 # 数据模型
│   ├── routes/                 # API路由
│   ├── services/               # 业务逻辑
│   ├── middleware/             # 中间件
│   ├── config.py               # 配置管理
│   └── dependencies.py         # 依赖注入
├── automation/                 # 任务调度
├── strategies/                 # 交易策略
├── data/                       # 数据管理
├── portfolio/                  # 投资组合
├── risk_management/            # 风险管理
├── backtesting/                # 回测引擎
├── api_main.py                 # ⭐ API入口（新增）
├── streamlit_app.py            # Streamlit界面（保留）
├── requirements_api.txt        # ⭐ API依赖（新增）
└── frontend_demo.html          # ⭐ 前端示例（新增）
```

## 🚀 两种使用方式

### 方式1: API服务器（推荐用于生产）

```bash
# 安装依赖
pip install -r requirements_api.txt

# 启动API
python api_main.py

# 访问文档
http://localhost:8000/docs
```

### 方式2: Streamlit界面（快速测试）

```bash
# 安装依赖
pip install -r requirements.txt

# 启动界面
streamlit run streamlit_app.py
```

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 3分钟快速启动 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 架构设计详解 |
| [API_DEPLOYMENT.md](API_DEPLOYMENT.md) | 云部署指南 |
| [API_SUMMARY.md](API_SUMMARY.md) | API层完整总结 |
| [TASK_MANAGEMENT_GUIDE.md](TASK_MANAGEMENT_GUIDE.md) | 任务管理指南 |

## ✨ 主要特性

### API层（新增）
- ✅ **18个RESTful端点**
- ✅ **自动生成Swagger文档**
- ✅ **类型安全的数据验证**
- ✅ **统一异常处理**
- ✅ **请求日志记录**
- ✅ **CORS跨域支持**
- ✅ **健康检查端点**

### 核心功能（保留）
- ✅ 多种交易策略（MA、RSI、MACD等）
- ✅ 自动化任务调度
- ✅ 投资组合管理
- ✅ 风险管理系统
- ✅ 回测引擎
- ✅ 实时监控

## 🎯 API端点概览

### 任务管理 `/api/tasks`
```
GET    /api/tasks                    # 获取所有任务
POST   /api/tasks                    # 创建任务
GET    /api/tasks/{id}               # 获取单个任务
PUT    /api/tasks/{id}               # 更新任务
DELETE /api/tasks/{id}               # 删除任务
POST   /api/tasks/{id}/execute       # 执行任务
POST   /api/tasks/{id}/pause         # 暂停任务
POST   /api/tasks/{id}/resume        # 恢复任务
```

### 调度器控制 `/api/scheduler`
```
GET  /api/scheduler/status          # 获取状态
POST /api/scheduler/start           # 启动调度器
POST /api/scheduler/stop            # 停止调度器
POST /api/scheduler/restart         # 重启调度器
```

### 策略分析 `/api/strategies`
```
POST /api/strategies/analyze         # 单个股票分析
POST /api/strategies/batch-analyze   # 批量分析
GET  /api/strategies/available       # 可用策略列表
```

## 💡 使用示例

### Python示例

```python
import requests

API_BASE = "http://localhost:8000"

# 创建任务
response = requests.post(f"{API_BASE}/api/tasks", json={
    "name": "Daily AAPL Analysis",
    "frequency": "daily",
    "symbols": ["AAPL", "MSFT"],
    "strategies": ["all"]
})
print(response.json())

# 启动调度器
response = requests.post(f"{API_BASE}/api/scheduler/start")
print(response.json())
```

### JavaScript示例

```javascript
const API_BASE = 'http://localhost:8000';

// 创建任务
const response = await fetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: 'Daily AAPL Analysis',
        frequency: 'daily',
        symbols: ['AAPL', 'MSFT'],
        strategies: ['all']
    })
});
const data = await response.json();
console.log(data);
```

### curl示例

```bash
# 创建任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily AAPL",
    "frequency": "daily",
    "symbols": ["AAPL"],
    "strategies": ["all"]
  }'
```

## 🎨 前端集成

### 使用提供的HTML示例
```bash
# Windows
start frontend_demo.html

# macOS
open frontend_demo.html
```

### 创建React应用
```bash
npx create-react-app trading-frontend
cd trading-frontend
npm install axios
# 参考 API_DEPLOYMENT.md 中的示例代码
```

## 🌐 云部署

### Docker
```bash
docker build -t trading-api .
docker run -p 8000:8000 trading-api
```

### Heroku
```bash
heroku create trading-api
git push heroku main
```

详细部署指南请查看 [API_DEPLOYMENT.md](API_DEPLOYMENT.md)

## 📊 架构对比

| 特性 | Streamlit | FastAPI |
|------|-----------|---------|
| 架构 | 单体应用 | 前后端分离 ✅ |
| API | 无 | RESTful ✅ |
| 前端 | 固定 | 任意框架 ✅ |
| 文档 | 手动 | 自动生成 ✅ |
| 性能 | 中等 | 高性能 ✅ |
| 扩展性 | 受限 | 优秀 ✅ |
| 移动端 | 不支持 | 支持 ✅ |

## 🔒 安全配置

```bash
# .env文件配置
ENABLE_AUTH=true
SECRET_KEY=your-secret-key
CORS_ORIGINS=["https://your-frontend.com"]
```

## 🧪 测试

```bash
# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest --cov=api tests/
```

## 📈 性能

- ⚡ 批量分析支持并行处理
- ⚡ 异步API端点
- ⚡ 高效的数据验证
- ⚡ 支持多worker部署

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- FastAPI - 高性能Web框架
- Pydantic - 数据验证
- Uvicorn - ASGI服务器
- yfinance - 市场数据

---

## 📞 获取帮助

- 查看 [文档](ARCHITECTURE.md)
- 访问 [Swagger UI](http://localhost:8000/docs)
- 查看 [示例代码](API_DEPLOYMENT.md)

**项目状态**: ✅ 生产就绪

**最后更新**: 2025-10-22
