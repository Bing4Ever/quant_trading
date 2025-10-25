# 安装指南 (Installation Guide)

## 📋 系统要求 (System Requirements)

- Python 3.8 或更高版本
- pip 或 conda 包管理器
- Git (用于克隆仓库)

## 🚀 快速安装 (Quick Installation)

### 方法 1: 基础安装 (Basic Installation)

```bash
# 克隆仓库
git clone https://github.com/Bing4Ever/quant_trading.git
cd quant_trading

# 安装基础依赖
pip install -r requirements.txt
```

### 方法 2: 使用 setup.py

```bash
# 基础安装
pip install -e .

# 包含开发工具
pip install -e ".[dev]"

# 包含 Jupyter 支持
pip install -e ".[notebook]"

# 完整安装
pip install -e ".[all]"
```

## 🛠️ 详细安装步骤 (Detailed Installation)

### 1. 准备环境

```bash
# 创建虚拟环境 (推荐)
python -m venv quant_env

# 激活虚拟环境
# Windows:
quant_env\Scripts\activate
# Linux/Mac:
source quant_env/bin/activate

# 升级 pip
python -m pip install --upgrade pip
```

### 2. 克隆项目

```bash
git clone https://github.com/Bing4Ever/quant_trading.git
cd quant_trading
```

### 3. 安装依赖

#### 基础安装 (推荐新手)
```bash
pip install -r requirements.txt
```

#### 开发者安装
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 高级功能 (可选)
```bash
# 谨慎安装，可能有兼容性问题
pip install -r requirements-advanced.txt
```

## ⚙️ 可选组件安装 (Optional Components)

### TA-Lib (技术分析库)

TA-Lib 需要单独安装 C 库：

#### Windows:
```bash
# 方法1: 使用预编译包
pip install TA-Lib

# 方法2: 如果上述失败，从 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 下载对应版本
# 例如: pip install TA_Lib-0.4.25-cp311-cp311-win_amd64.whl
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt-get install libta-lib-dev
pip install TA-Lib

# CentOS/RHEL
sudo yum install ta-lib-devel
pip install TA-Lib
```

#### macOS:
```bash
brew install ta-lib
pip install TA-Lib
```

### QuantLib (量化金融库)

```bash
# Windows (通过 conda 推荐)
conda install -c conda-forge quantlib

# Linux
sudo apt-get install libquantlib0-dev
pip install QuantLib

# macOS
brew install quantlib
pip install QuantLib
```

## 🧪 验证安装 (Verify Installation)

```bash
# 运行基础测试
python -c "import pandas, numpy, yfinance; print('基础包安装成功!')"

# 运行项目示例
python main.py

# 运行测试套件
pytest tests/ -v
```

## 🐛 常见问题 (Troubleshooting)

### 1. pip 安装失败

```bash
# 升级 pip 和 setuptools
python -m pip install --upgrade pip setuptools wheel

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 2. TA-Lib 安装失败

```bash
# Windows: 下载预编译文件
# 访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

# 或者跳过 TA-Lib，使用我们内置的技术指标
# 编辑 requirements.txt，注释掉 ta-lib 行
```

### 3. 内存不足

```bash
# 逐个安装大包
pip install pandas
pip install numpy
pip install matplotlib
# ... 其他包
```

### 4. 网络问题

```bash
# 使用镜像源
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 或者
pip install -r requirements.txt -i https://pypi.douban.com/simple/
```

## 🖥️ 不同操作系统的特殊说明

### Windows 用户

1. 确保安装了 Visual Studio Build Tools 或 Visual Studio
2. 某些包可能需要预编译版本
3. 推荐使用 Anaconda 环境

### Linux 用户

1. 可能需要安装开发工具：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential python3-dev
   
   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install python3-devel
   ```

### macOS 用户

1. 安装 Xcode Command Line Tools：
   ```bash
   xcode-select --install
   ```

## 🐳 Docker 安装 (可选)

如果遇到依赖问题，可以使用 Docker：

```bash
# 构建镜像
docker build -t quant-trading .

# 运行容器
docker run -it -p 8888:8888 quant-trading
```

## 📊 性能优化建议

1. **使用 conda 环境**：某些科学计算包在 conda 中有更好的优化
2. **启用多核处理**：确保 NumPy 使用了优化的 BLAS 库
3. **内存管理**：对于大数据集，考虑使用 Dask 或分块处理

## 🆘 获取帮助

如果遇到安装问题：

1. 查看 [GitHub Issues](https://github.com/Bing4Ever/quant_trading/issues)
2. 提交新的 Issue 并附上错误信息
3. 查看项目 Wiki 页面
4. 联系项目维护者

---

## English Version

### Quick Setup

```bash
git clone https://github.com/Bing4Ever/quant_trading.git
cd quant_trading
pip install -r requirements.txt
python main.py
```

For detailed English installation instructions, please refer to the error messages and use online translators or contact the maintainers.