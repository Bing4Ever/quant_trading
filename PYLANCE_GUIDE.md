# Pylance 代码规范指南

## 📋 总体原则

以后所有生成的程序都必须符合 Pylance 的规范要求。以下是具体的规范要点：

## 🔧 导入规范

### ✅ 正确示例
```python
from typing import Dict, Optional, List
import logging
from datetime import datetime
```

### ❌ 避免的问题
```python
import pandas as pd  # 如果未使用则删除
from typing import Dict, Optional, Tuple  # 删除未使用的 Tuple
```

## 📝 文档字符串规范

### ✅ 正确示例
```python
"""模块的简短描述"""

def function_name(param: str) -> bool:
    """
    函数的简短描述
    
    Args:
        param: 参数描述
        
    Returns:
        返回值描述
    """
```

### ❌ 避免的问题
```python
"""
多行注释被认为是注释掉的代码
不要使用这种格式
"""
```

## 🏷️ 类型注解规范

### ✅ 正确示例
```python
def calculate_position(symbol: str, price: float, capital: float) -> int:
    """计算仓位"""
    return int(capital * 0.2 / price)

class RiskManager:
    def __init__(self, max_position: float = 0.2) -> None:
        self.positions: Dict[str, Dict] = {}
```

### ❌ 避免的问题
```python
def calculate_position(symbol, price, capital):  # 缺少类型注解
    return int(capital * 0.2 / price)
```

## 📊 日志记录规范

### ✅ 正确示例
```python
# 使用 % 格式化
logger.info("仓位计算 %s: %d股 (投资额: $%.2f)", symbol, shares, investment)
logger.warning("止损触发 %s: 亏损%.2f%%", symbol, loss_pct * 100)
logger.error("操作失败 %s: %s", symbol, str(error))
```

### ❌ 避免的问题
```python
# 不要使用 f-string
logger.info(f"仓位计算 {symbol}: {shares}股")
logger.warning(f"止损触发 {symbol}: {loss_pct:.2%}")
```

## 🔄 异常处理规范

### ✅ 正确示例
```python
try:
    data = fetch_data(symbol)
except ValueError as e:
    logger.error("数据获取失败: %s", str(e))
except ConnectionError as e:
    logger.error("网络连接失败: %s", str(e))
except Exception as e:
    logger.error("未知错误: %s", str(e))
    raise
```

### ❌ 避免的问题
```python
try:
    data = fetch_data(symbol)
except:  # 不要使用裸露的 except
    pass

try:
    data = fetch_data(symbol)
except Exception as e:  # 避免捕获过于宽泛的异常
    pass
```

## 🧮 复杂度控制

### ✅ 正确示例
```python
def complex_analysis(self) -> None:
    """复杂分析 - 拆分为多个小方法"""
    self._check_stop_conditions()
    self._find_opportunities()
    self._update_positions()

def _check_stop_conditions(self) -> None:
    """检查止损条件"""
    # 具体实现...

def _find_opportunities(self) -> None:
    """寻找机会"""
    # 具体实现...
```

### ❌ 避免的问题
```python
def complex_analysis(self) -> None:
    """一个方法包含太多逻辑 - 认知复杂度过高"""
    # 100+ 行代码混在一个方法中
```

## 📦 变量和导入规范

### ✅ 正确示例
```python
# 使用变量
result = calculate_value()
logger.info("计算结果: %s", result)

# 删除未使用的变量
def process_data():
    data = fetch_data()
    return process(data)  # 使用 data
```

### ❌ 避免的问题
```python
# 未使用的变量
def process_data():
    data = fetch_data()
    unused_var = "not used"  # 删除此变量
    return process_other_data()
```

## 🔗 其他最佳实践

### 1. 字符串格式化
```python
# ✅ 正确
message = "用户 %s 执行了 %s 操作" % (user, action)

# ❌ 错误
message = f"用户 {user} 执行了 {action} 操作"  # f-string 中无变量时
```

### 2. 条件合并
```python
# ✅ 正确
if condition1 or condition2:
    execute_action()

# ❌ 错误
if condition1:
    execute_action()
elif condition2:
    execute_action()  # 重复代码
```

### 3. 迭代器使用
```python
# ✅ 正确
for key in dictionary:
    process(key)

# ❌ 错误
for key in list(dictionary.keys()):  # 不必要的 list() 调用
    process(key)
```

## 📋 检查清单

在提交代码前，确保：

- [ ] 所有导入都被使用
- [ ] 所有变量都被使用
- [ ] 使用了正确的类型注解
- [ ] 日志使用 % 格式化而非 f-string
- [ ] 异常处理具体且有意义
- [ ] 方法复杂度不超过 15
- [ ] 没有重复的代码块
- [ ] 文档字符串格式正确
- [ ] 没有不必要的 list() 调用

## 🛠️ 自动化检查

使用以下命令检查代码质量：

```bash
# 检查 Pylance 错误
python -m pylint your_file.py

# 运行类型检查
python -m mypy your_file.py

# 运行测试确保功能正常
cd tests && python run_tests.py --quick
```

---

遵循这些规范将确保代码质量高、可维护性强，且符合现代 Python 开发最佳实践。