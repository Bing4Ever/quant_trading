# 配置管理使用指南

## 概述

该项目使用混合配置管理方式：
- **环境变量**：管理敏感信息（API密钥等）
- **YAML配置文件**：管理结构化配置

环境变量的优先级高于YAML配置文件。

## 快速开始

### 1. 设置API密钥

```bash
# 复制环境变量模板
copy config\.env.example config\.env

# 编辑 .env 文件添加你的API密钥
notepad config\.env
```

在 `.env` 文件中设置：
```bash
ALPHA_VANTAGE_API_KEY=your_actual_alpha_vantage_api_key
QUANDL_API_KEY=your_actual_quandl_api_key
```

### 2. 获取API密钥

- **Alpha Vantage**: https://www.alphavantage.co/support/#api-key (免费)
- **Quandl**: https://www.quandl.com/tools/api (免费)

### 3. 在代码中使用

```python
from config import Config

# 创建配置实例
config = Config()

# 获取配置值（支持点符号）
initial_capital = config.get('trading.initial_capital', 100000.0)
api_key = config.get('market_data.alpha_vantage.api_key')

# 直接获取环境变量
debug_mode = config.get_env('DEBUG_MODE', False)
log_level = config.get_env('LOG_LEVEL', 'INFO')
```

## 环境变量映射

系统会自动将环境变量映射到配置键：

| 环境变量 | 配置键 | 类型 | 说明 |
|---------|--------|------|------|
| `ALPHA_VANTAGE_API_KEY` | `market_data.alpha_vantage.api_key` | str | Alpha Vantage API密钥 |
| `INITIAL_CAPITAL` | `trading.initial_capital` | float | 初始资金 |
| `MAX_POSITION_SIZE` | `trading.max_position_size` | float | 最大仓位比例 |
| `LOG_LEVEL` | `logging.level` | str | 日志级别 |
| `DEBUG_MODE` | `development.debug_mode` | bool | 调试模式 |
| `PAPER_TRADING` | `trading.paper_trading` | bool | 模拟交易 |

完整的映射列表请参考 `config/__init__.py` 中的 `_apply_env_overrides` 方法。

## 类型自动转换

环境变量会自动进行类型转换：

- **布尔值**: `true`, `yes`, `1`, `on` → `True`；`false`, `no`, `0`, `off` → `False`
- **数字**: 自动识别整数和浮点数
- **字符串**: 其他值保持为字符串

## 配置优先级

1. **环境变量**（最高优先级）
2. **YAML配置文件**
3. **默认值**（最低优先级）

## 安全注意事项

1. **永远不要将 `.env` 文件提交到版本控制系统**
2. **在生产环境中使用环境变量而不是配置文件**
3. **定期更换API密钥**
4. **使用强密码和加密**

## 示例用法

### 获取API密钥

```python
from config import config

# 获取Alpha Vantage API密钥
api_key = config.get('market_data.alpha_vantage.api_key')
if not api_key:
    raise ValueError("请设置 ALPHA_VANTAGE_API_KEY 环境变量")
```

### 获取交易配置

```python
# 获取交易配置
trading_config = config.trading
initial_capital = trading_config.get('initial_capital', 100000.0)
max_position = trading_config.get('max_position_size', 0.05)
```

### 动态设置配置

```python
# 动态设置配置值
config.set('trading.commission_rate', 0.001)
config.set('strategies.rsi.period', 14)

# 保存到文件（仅保存到YAML文件）
config.save()
```

### 添加自定义环境变量映射

```python
# 添加新的环境变量映射
config.set_env_mapping('CUSTOM_API_KEY', 'custom.api_key')
```

## 测试配置

运行配置测试：

```bash
python test_env_config.py
```

这将测试：
- 环境变量加载
- 类型转换
- 配置映射
- 默认值处理

## 常见问题

### Q: 为什么我的环境变量没有生效？
A: 确保：
1. 环境变量名称正确
2. `.env` 文件在 `config/` 目录下
3. 重启应用程序以重新加载环境变量

### Q: 如何查看当前的配置值？
A: 使用调试模式：
```python
from config import config
import json
print(json.dumps(config._config, indent=2))
```

### Q: 如何在不同环境中使用不同的配置？
A: 使用不同的 `.env` 文件：
```python
# 开发环境
config = Config(env_file='config/.env.dev')

# 生产环境
config = Config(env_file='config/.env.prod')
```