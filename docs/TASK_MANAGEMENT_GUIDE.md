# 📖 任务管理快速指南

## 🗑️ 删除任务

### 方法一：在 Streamlit 界面删除（推荐）

1. **打开任务列表**
   - 进入 "🤖 自动化管理" 页面
   - 切换到 "📋 任务列表" 标签

2. **选择要删除的任务**
   - 在 "选择任务" 下拉菜单中选择任务

3. **删除操作**
   - 点击 "🗑️ 删除" 按钮
   - 第一次点击：系统会显示确认提示 ⚠️
   - 第二次点击：任务将被永久删除 ✅

### 方法二：通过代码删除

```python
from automation.scheduler import AutoTradingScheduler

# 创建调度器
scheduler = AutoTradingScheduler()

# 删除指定任务
success = scheduler.remove_scheduled_task("task_id")

if success:
    print("✅ 任务已删除")
else:
    print("❌ 删除失败")
```

## ⏸️ 暂停任务（不删除）

如果你只是想临时停止任务而不删除：

### 在界面中暂停
1. 选择任务
2. 点击 "⏸️ 暂停" 按钮
3. 任务会停止执行，但配置保留

### 恢复任务
1. 选择已暂停的任务
2. 点击 "▶️ 恢复" 按钮
3. 任务继续按计划执行

### 通过代码操作

```python
# 暂停任务
scheduler.pause_task("task_id")

# 恢复任务
scheduler.resume_task("task_id")
```

## 🔍 查看所有任务

### 列出所有任务

```python
# 获取所有任务
tasks = scheduler.list_all_tasks()

for task in tasks:
    print(f"任务: {task['name']}")
    print(f"  ID: {task['task_id']}")
    print(f"  状态: {task['status']}")
    print(f"  启用: {task['enabled']}")
    print()
```

### 查看任务详情

```python
# 获取单个任务状态
task_status = scheduler.get_task_status("task_id")

if task_status:
    print(f"任务名称: {task_status['name']}")
    print(f"执行频率: {task_status['frequency']}")
    print(f"上次执行: {task_status['last_run']}")
    print(f"下次执行: {task_status['next_run']}")
```

## 🚀 常用操作

### 立即执行任务（不等待计划时间）

```python
# 立即执行指定任务
scheduler.execute_task("task_id")
```

### 清空所有任务

```python
# 获取所有任务ID
task_ids = list(scheduler.scheduled_tasks.keys())

# 逐个删除
for task_id in task_ids:
    scheduler.remove_scheduled_task(task_id)

print(f"✅ 已删除 {len(task_ids)} 个任务")
```

## ⚠️ 注意事项

1. **删除是永久性的** - 删除后无法恢复，建议使用"暂停"功能
2. **正在运行的任务** - 删除时会自动取消正在运行的任务
3. **配置自动保存** - 所有操作会立即保存到配置文件
4. **双重确认** - 界面删除需要点击两次，防止误操作

## 💾 配置文件位置

任务配置保存在：
```
automation/config/scheduler_config.json
```

如果需要批量管理或备份，可以直接编辑此文件。
