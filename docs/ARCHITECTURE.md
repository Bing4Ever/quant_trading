# 前后端分离架构说明

## 📐 架构概览

本项目已完成从单体Streamlit应用到**前后端完全分离**的架构升级：

```
┌─────────────────────────────────────────────────────────┐
│                     前端层 (Frontend)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   React      │  │   Vue.js     │  │  Mobile App  │  │
│  │   (计划)      │  │   (计划)      │  │   (可选)      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│           │                │                 │            │
│           └────────────────┴─────────────────┘            │
│                          │ HTTP/WebSocket                 │
└──────────────────────────┼────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────────┐
│                     API层 (Backend)                       │
│  ┌────────────────────────────────────────────────────┐  │
│  │           FastAPI Application (api_main.py)        │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                                │
│  ┌──────────────┬────────┼────────┬──────────────┐      │
│  │   Routers    │  Middleware    │   Models      │      │
│  ├──────────────┤ ├──────────────┤├──────────────┤      │
│  │ tasks.py     │ │ logging.py   ││task_models   │      │
│  │ scheduler.py │ │ exceptions   ││strategy_...  │      │
│  │ strategies.py│ │ CORS         ││portfolio_... │      │
│  └──────────────┘ └──────────────┘└──────────────┘      │
│                          │                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Service Layer (服务层)                │  │
│  │  ┌───────────┬────────────┬─────────────┐       │  │
│  │  │TaskService│SchedulerSvc│StrategySvc  │       │  │
│  │  └───────────┴────────────┴─────────────┘       │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────┼────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────────┐
│                   核心业务层 (Core)                        │
│  ┌──────────────┬────────────┬──────────────┐            │
│  │  Automation  │  Strategies│  Portfolio   │            │
│  │  ┌─────────┐ │  ┌────────┐│  ┌─────────┐ │            │
│  │  │Scheduler│ │  │MA      ││  │Manager  │ │            │
│  │  │Monitor  │ │  │RSI     ││  │Optimizer│ │            │
│  │  └─────────┘ │  │MACD    ││  └─────────┘ │            │
│  │              │  └────────┘│              │            │
│  ├──────────────┼────────────┼──────────────┤            │
│  │    Data      │Backtesting │ Risk Mgmt    │            │
│  │  ┌─────────┐ │  ┌────────┐│  ┌─────────┐ │            │
│  │  │Fetcher  │ │  │Engine  ││  │Manager  │ │            │
│  │  │Storage  │ │  │Reports ││  │Metrics  │ │            │
│  │  └─────────┘ │  └────────┘│  └─────────┘ │            │
│  └──────────────┴────────────┴──────────────┘            │
└───────────────────────────────────────────────────────────┘
```

## 🎯 分层架构详解

### 1. API层 (`/api`)

**职责**: 处理HTTP请求、数据验证、路由分发

#### 1.1 Models (数据模型)
- `task_models.py`: 任务相关的请求/响应模型
- `strategy_models.py`: 策略分析模型
- `portfolio_models.py`: 投资组合模型
- `scheduler_models.py`: 调度器状态模型
- `common_models.py`: 通用响应模型

**特点**: 使用Pydantic进行自动验证和序列化

#### 1.2 Routes (路由层)
- `tasks.py`: 任务CRUD端点
- `scheduler.py`: 调度器控制端点
- `strategies.py`: 策略分析端点

**职责**: 
- 接收HTTP请求
- 调用Service层处理业务逻辑
- 返回标准化响应

#### 1.3 Services (服务层)
- `task_service.py`: 任务管理业务逻辑
- `scheduler_service.py`: 调度器管理逻辑
- `strategy_service.py`: 策略分析逻辑

**职责**:
- 解耦路由和核心业务代码
- 封装复杂业务逻辑
- 提供可复用的服务接口

#### 1.4 Middleware (中间件)
- `logging.py`: 请求/响应日志
- `exception_handlers.py`: 统一异常处理

### 2. 核心业务层

**保留原有功能**, 不受API层影响：
- `automation/`: 任务调度和自动化
- `strategies/`: 交易策略实现
- `portfolio/`: 投资组合管理
- `data/`: 数据获取和存储
- `backtesting/`: 回测引擎
- `risk_management/`: 风险管理

## 🔄 数据流

### 典型请求流程

```
1. 前端发起请求
   POST /api/tasks
   {
     "name": "Daily AAPL",
     "frequency": "daily",
     "symbols": ["AAPL"]
   }
          ↓
2. FastAPI接收 (api_main.py)
   - CORS验证
   - 日志记录
          ↓
3. 路由层 (tasks.py)
   - 数据验证 (TaskCreateRequest)
   - 调用TaskService
          ↓
4. 服务层 (task_service.py)
   - 业务逻辑处理
   - 调用Scheduler
          ↓
5. 核心层 (automation/scheduler.py)
   - 创建任务
   - 保存配置
          ↓
6. 响应返回
   {
     "task_id": "task_xxx",
     "name": "Daily AAPL",
     "status": "created"
   }
```

## 🌟 架构优势

### ✅ 前后端分离

| 特性 | 说明 |
|------|------|
| **技术栈独立** | 前端可用React/Vue，后端FastAPI |
| **并行开发** | 前后端团队独立开发 |
| **灵活部署** | 前端静态托管，后端服务器部署 |
| **多端支持** | Web、移动、桌面应用共用API |

### ✅ 分层架构

| 层级 | 优势 |
|------|------|
| **API层** | 标准化接口，易于文档化和测试 |
| **Service层** | 业务逻辑集中，易于维护 |
| **Core层** | 原有功能保留，平滑迁移 |

### ✅ 可扩展性

- **水平扩展**: 多实例部署，负载均衡
- **垂直扩展**: 增加服务器资源
- **模块化**: 新功能只需添加新路由和服务

## 📊 与原Streamlit架构对比

| 维度 | Streamlit (原) | FastAPI (新) |
|------|---------------|--------------|
| **架构** | 单体应用 | 前后端分离 |
| **界面** | Python内置 | 任意前端框架 |
| **API** | 无 | RESTful API |
| **部署** | Streamlit服务器 | 独立API服务器 |
| **扩展性** | 受限 | 优秀 |
| **性能** | 中等 | 高性能 |
| **移动端** | 不支持 | 支持 |
| **文档** | 手动编写 | 自动生成Swagger |

## 🚀 迁移路径

### 阶段1: 共存期 ✅ (当前)

```
Streamlit应用 (保留)
     ↓
   核心业务层
     ↑
  FastAPI (新增)
     ↑
  前端 (可选)
```

**特点**: 
- Streamlit继续工作
- API层已完整实现
- 可逐步迁移功能

### 阶段2: 迁移期 (规划)

- 前端开发React应用
- 逐步替换Streamlit页面
- API持续优化

### 阶段3: 完成期 (目标)

```
React/Vue前端
     ↓
  FastAPI API
     ↓
   核心业务层
```

**特点**:
- 完全前后端分离
- Streamlit退役
- 生产级部署

## 🛠️ 开发工作流

### 添加新功能

1. **定义数据模型** (`api/models/`)
   ```python
   class NewFeatureRequest(BaseModel):
       field1: str
       field2: int
   ```

2. **创建服务** (`api/services/`)
   ```python
   class NewFeatureService:
       def process(self, request):
           # 业务逻辑
           pass
   ```

3. **添加路由** (`api/routes/`)
   ```python
   @router.post("/api/newfeature")
   async def new_feature(request: NewFeatureRequest):
       service = NewFeatureService()
       return service.process(request)
   ```

4. **测试** (自动生成Swagger文档)

## 📦 部署建议

### 开发环境
```bash
# 启动API
python api_main.py

# 启动Streamlit (可选)
streamlit run streamlit_app.py
```

### 生产环境

```bash
# 使用Gunicorn + Uvicorn
gunicorn api_main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# 使用Nginx反向代理
# 前端部署到CDN
```

## 🔐 安全性

- ✅ CORS配置
- ✅ 输入验证 (Pydantic)
- ✅ 异常处理
- ⏳ JWT认证 (待实现)
- ⏳ API限流 (待实现)
- ⏳ HTTPS (部署时配置)

## 📚 相关文档

- [API部署指南](./API_DEPLOYMENT.md)
- [任务管理指南](./TASK_MANAGEMENT_GUIDE.md)
- [Swagger文档](http://localhost:8000/docs) (启动后访问)

## 🎓 学习资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [前后端分离最佳实践](https://12factor.net/)
- [RESTful API设计规范](https://restfulapi.net/)

---

**总结**: 本项目现已具备完整的API层，支持前后端分离部署。Streamlit应用作为临时前端继续可用，未来可替换为React/Vue现代前端框架。
