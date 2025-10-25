# API层部署文档

## 📋 项目结构

```
quant_trading/
├── api/                        # API层（新增）
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── dependencies.py         # 依赖注入
│   ├── models/                # 数据模型
│   │   ├── task_models.py
│   │   ├── strategy_models.py
│   │   ├── portfolio_models.py
│   │   ├── scheduler_models.py
│   │   └── common_models.py
│   ├── routes/                # API路由
│   │   ├── tasks.py           # 任务管理端点
│   │   ├── scheduler.py       # 调度器控制端点
│   │   └── strategies.py      # 策略分析端点
│   ├── services/              # 业务逻辑层
│   │   ├── task_service.py
│   │   ├── scheduler_service.py
│   │   └── strategy_service.py
│   ├── middleware/            # 中间件
│   │   ├── logging.py
│   │   └── exception_handlers.py
│   └── utils/                 # 工具函数
├── api_main.py                # FastAPI应用入口
├── requirements_api.txt       # API依赖
├── .env.example              # 环境变量模板
└── frontend_demo.html        # 前端示例
```

## 🚀 快速启动

### 1. 安装依赖

```bash
# 安装API所需依赖
pip install -r requirements_api.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，根据需要调整配置
```

### 3. 启动API服务器

```bash
# 开发模式（自动重载）
python api_main.py

# 或使用uvicorn直接启动
uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式（多worker）
uvicorn api_main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问API文档

启动后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📡 API端点概览

### 任务管理 (`/api/tasks`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取所有任务 |
| GET | `/api/tasks/{task_id}` | 获取指定任务 |
| POST | `/api/tasks` | 创建新任务 |
| PUT | `/api/tasks/{task_id}` | 更新任务 |
| DELETE | `/api/tasks/{task_id}` | 删除任务 |
| POST | `/api/tasks/{task_id}/execute` | 手动执行任务 |
| POST | `/api/tasks/{task_id}/pause` | 暂停任务 |
| POST | `/api/tasks/{task_id}/resume` | 恢复任务 |

### 调度器控制 (`/api/scheduler`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/scheduler/status` | 获取调度器状态 |
| POST | `/api/scheduler/start` | 启动调度器 |
| POST | `/api/scheduler/stop` | 停止调度器 |
| POST | `/api/scheduler/restart` | 重启调度器 |

### 策略分析 (`/api/strategies`)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/strategies/analyze` | 分析单个股票 |
| POST | `/api/strategies/batch-analyze` | 批量分析多个股票 |
| GET | `/api/strategies/available` | 获取可用策略列表 |

## 📝 使用示例

### 创建任务

```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily AAPL Analysis",
    "frequency": "daily",
    "symbols": ["AAPL", "MSFT"],
    "strategies": ["all"],
    "enabled": true
  }'
```

### 启动调度器

```bash
curl -X POST "http://localhost:8000/api/scheduler/start"
```

### 分析股票

```bash
curl -X POST "http://localhost:8000/api/strategies/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "strategies": ["ma_crossover", "rsi"],
    "period": "1mo",
    "interval": "1d"
  }'
```

## 🎨 前端集成

### 方式1：使用提供的HTML示例

```bash
# 直接在浏览器中打开
start frontend_demo.html  # Windows
open frontend_demo.html   # macOS
```

### 方式2：创建React应用

```bash
# 创建新的React应用
npx create-react-app trading-frontend
cd trading-frontend

# 安装axios用于API调用
npm install axios

# 配置API_BASE_URL指向后端
# 示例代码见下方
```

React示例代码：

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// 获取所有任务
export const getTasks = async () => {
  const response = await axios.get(`${API_BASE}/api/tasks`);
  return response.data;
};

// 创建任务
export const createTask = async (taskData) => {
  const response = await axios.post(`${API_BASE}/api/tasks`, taskData);
  return response.data;
};

// 启动调度器
export const startScheduler = async () => {
  const response = await axios.post(`${API_BASE}/api/scheduler/start`);
  return response.data;
};
```

## 🔒 安全配置

### 启用认证

在 `.env` 文件中：

```bash
ENABLE_AUTH=true
SECRET_KEY=your-secure-random-secret-key-here
```

### CORS配置

```bash
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

### 生产环境建议

1. **使用HTTPS**: 部署时配置SSL证书
2. **限流**: 启用速率限制
3. **认证**: 实施JWT或API Key认证
4. **日志**: 配置日志轮转和监控
5. **数据库**: 迁移到PostgreSQL/MySQL

## 🌐 云部署指南

### Docker部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
docker build -t trading-api .
docker run -p 8000:8000 trading-api
```

### 部署到云服务

#### AWS EC2
```bash
# 1. 启动EC2实例（Ubuntu）
# 2. 安装Python和依赖
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements_api.txt

# 3. 使用systemd管理服务
sudo nano /etc/systemd/system/trading-api.service
```

#### Google Cloud Run
```bash
gcloud run deploy trading-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku
```bash
# 创建Procfile
echo "web: uvicorn api_main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 部署
heroku create trading-api
git push heroku main
```

## 📊 监控和日志

### 日志文件

- API日志: `logs/api.log`
- 调度器日志: `logs/scheduler.log`

### 健康检查

```bash
curl http://localhost:8000/health
```

### 性能监控

考虑集成：
- **Prometheus**: 指标收集
- **Grafana**: 可视化仪表板
- **Sentry**: 错误追踪

## 🧪 测试

```bash
# 运行API测试
pytest tests/test_api.py -v

# 运行集成测试
pytest tests/integration/ -v

# 生成覆盖率报告
pytest --cov=api tests/
```

## 📦 依赖说明

| 包 | 版本 | 用途 |
|----|------|------|
| fastapi | 0.109.0 | Web框架 |
| uvicorn | 0.27.0 | ASGI服务器 |
| pydantic | 2.5.3 | 数据验证 |
| pydantic-settings | 2.1.0 | 配置管理 |

## 🔧 故障排除

### 问题: 导入错误

```bash
# 确保项目根目录在Python路径中
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 问题: 端口被占用

```bash
# 更改端口
uvicorn api_main:app --port 8001
```

### 问题: CORS错误

检查 `.env` 中的 `CORS_ORIGINS` 配置是否包含前端URL。

## 📚 更多资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Uvicorn文档](https://www.uvicorn.org/)
- [Pydantic文档](https://docs.pydantic.dev/)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用MIT许可证。
