"""
Setup configuration for the quantitative trading system.
"""

import pathlib

from setuptools import find_packages, setup

# Read the README file for long description
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

# Read requirements from requirements.txt
def read_requirements(filename):
    """Read requirements from file, filtering out comments and empty lines."""
    with open(filename, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]

try:
    REQUIREMENTS = read_requirements("requirements.txt")
except FileNotFoundError:
    # Fallback to essential requirements if file not found
    REQUIREMENTS = [
        "pandas>=2.0.0",
        "numpy>=1.24.0", 
        "yfinance>=0.2.0",
        "matplotlib>=3.7.0",
        "scikit-learn>=1.3.0",
        "pyyaml>=6.0.0",
    ]

setup(
    name="quant-trading-system",
    version="1.0.0",
    author="Bing4Ever",
    author_email="",
    description="A comprehensive Python-based quantitative trading framework",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Bing4Ever/quant_trading",
    project_urls={
        "Bug Reports": "https://github.com/Bing4Ever/quant_trading/issues",
        "Source": "https://github.com/Bing4Ever/quant_trading",
        "Documentation": "https://github.com/Bing4Ever/quant_trading/blob/main/README.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "notebooks", "notebooks.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=REQUIREMENTS,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "bandit>=1.7.0",
            "pre-commit>=3.4.0",
        ],
        "notebook": [
            "jupyter>=1.0.0",
            "ipykernel>=6.25.0",
            "jupyterlab>=4.0.0",
        ],
        "advanced": [
            "alpha-vantage>=2.3.0",
            "backtrader>=1.9.0",
            "empyrical>=0.5.0",
            # Note: ta-lib, quantlib require manual installation
        ],
        "ml": [
            "xgboost>=1.7.0",
            "lightgbm>=4.0.0",
            # Note: tensorflow, torch are large packages
        ],
        "all": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0", 
            "black>=23.0.0",
            "jupyter>=1.0.0",
            "alpha-vantage>=2.3.0",
            "empyrical>=0.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quant-trading=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
        "config": ["*.yaml", "*.yml"],
        "notebooks": ["*.ipynb"],
    },
    keywords=[
        "quantitative trading",
        "algorithmic trading",
        "backtesting",
        "financial analysis",
        "portfolio optimization",
        "risk management",
        "stock market",
        "trading strategies",
    ],
    zip_safe=False,
)