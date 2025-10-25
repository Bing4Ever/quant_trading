# 项目结构重组方案

## 🎯 目标结构

```
quant_trading/
├── docs/                          # 📚 所有文档
│   ├── README.md                  # 主文档
│   ├── QUICKSTART.md              # 快速开始
│   ├── ARCHITECTURE.md            # 架构说明
│   ├── API_GUIDE.md               # API指南
│   ├── DEPLOYMENT.md              # 部署指南
│   └── CHANGELOG.md               # 变更日志
│
├── src/                           # 💻 源代码
│   ├── api/                       # API层
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── middleware/
│   ├── automation/                # 自动化
│   ├── strategies/                # 策略
│   ├── portfolio/                 # 投资组合
│   ├── risk_management/           # 风险管理
│   ├── backtesting/              # 回测
│   ├── data/                      # 数据
│   ├── trading/                   # 交易
│   └── utils/                     # 工具
│
├── scripts/                       # 🔧 脚本工具
│   ├── start_api.bat             # API启动（Windows）
│   ├── start_api.sh              # API启动（Linux）
│   ├── start_streamlit.bat       # Streamlit启动
│   └── demo_*.py                 # 演示脚本
│
├── tests/                         # 🧪 测试
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── fixtures/                 # 测试数据
│
├── config/                        # ⚙️ 配置
│   ├── .env.example
│   └── settings.yaml
│
├── data/                          # 📊 数据存储
│   ├── raw/                      # 原始数据
│   ├── processed/                # 处理后数据
│   └── cache/                    # 缓存
│
├── logs/                          # 📝 日志
├── reports/                       # 📈 报告
├── notebooks/                     # 📓 Jupyter笔记本
│
├── app.py                         # 🚀 主入口（API）
├── streamlit_app.py              # 🎨 Streamlit入口
├── requirements.txt              # 📦 基础依赖
├── requirements-dev.txt          # 🔧 开发依赖
├── setup.py                      # 📦 包配置
└── README.md                     # 📖 主README
```

## 🔄 重组操作

### 阶段1: 整理文档（立即执行）

**移动到 `docs/` 目录:**
- ARCHITECTURE.md
- API_DEPLOYMENT.md
- API_SUMMARY.md
- QUICKSTART.md
- TASK_MANAGEMENT_GUIDE.md
- INSTALLATION.md
- CHANGELOG.md
- ENCODING_FIX.md
- REMOVAL_AND_FIX_SUMMARY.md
- PYLANCE_GUIDE.md
- PARAMETER_OPTIMIZATION_REPORT.md
- FAVORITES_FEATURE_REPORT.md
- README_DEPLOYMENT.md
- README_实战指南.md

**合并README:**
- README.md (主)
- README_API.md (合并到主README)

### 阶段2: 整理脚本

**移动到 `scripts/` 目录:**
- start_api.bat
- start_api.sh
- demo_*.py (所有演示脚本)
- launcher.py
- simple_test.py
- fix_*.py (临时修复脚本)
- ui_update_summary.py

**删除冗余启动文件:**
- start.py (保留 app.py)
- run.py (合并到 app.py)
- run_*.py (移到scripts/)

### 阶段3: 整理源代码

**当前问题:**
```
❌ api/ 在根目录
❌ automation/ 在根目录
❌ strategies/ 在根目录
```

**建议结构:**
```
✅ src/
   ├── api/
   ├── automation/
   ├── strategies/
   └── ...
```

**但是**: 这会破坏所有import语句！

### 阶段4: 整理测试

**移动到 `tests/` 对应子目录:**
- test_serialization.py → tests/unit/
- test_system.py → tests/integration/
- test_task_creation.py → tests/integration/

### 阶段5: 清理临时文件

**可以删除:**
- api_server.py (已被 api_main.py 替代)
- fix_risk_metrics_whitespace.py (一次性脚本)
- simple_test.py (临时测试)

## ⚠️ 关键决策

### 选项A: 激进重组（推荐用于新项目）
- 所有代码移到 `src/`
- 需要更新所有import语句
- 需要配置PYTHONPATH
- 优点: 结构清晰、规范
- 缺点: 工作量大、可能出错

### 选项B: 保守重组（推荐当前使用）✅
- **只整理文档和脚本**
- **核心代码保持在根目录**
- 不破坏现有import
- 优点: 安全、快速
- 缺点: 结构不够完美

## 🎯 建议执行方案（保守）

### 立即执行:

1. **创建 `docs/` 并移动文档**
2. **创建 `scripts/` 并移动脚本**
3. **删除冗余文件**
4. **统一启动入口**
5. **更新主README**

### 暂不执行:

- 移动核心代码到 `src/`（风险太大）
- 大规模重构import（容易出错）

## 📝 执行清单

- [ ] 创建 docs/ 目录
- [ ] 移动14个文档文件
- [ ] 创建 scripts/ 目录
- [ ] 移动启动脚本和演示脚本
- [ ] 删除 api_server.py (重复)
- [ ] 统一为 app.py 作为主入口
- [ ] 更新 README.md
- [ ] 更新 .gitignore
- [ ] 测试所有启动方式

## 🚀 预期结果

**之前根目录: 40+ 个文件**
**之后根目录: ~15 个文件**

```
quant_trading/
├── docs/                    # 所有文档
├── scripts/                 # 所有脚本
├── tests/                   # 所有测试
├── api/                     # 核心代码
├── automation/              # 核心代码
├── strategies/              # 核心代码
├── ...                      # 其他核心代码
├── app.py                   # 主入口
├── streamlit_app.py         # UI入口
├── requirements.txt         # 依赖
└── README.md               # 文档
```

**清爽多了！** ✨
