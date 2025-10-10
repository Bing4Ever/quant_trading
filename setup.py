"""
Setup configuration for the quantitative trading system.
"""

from setuptools import setup, find_packages
import pathlib

# Read the README file for long description
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

# Read requirements from requirements.txt
REQUIREMENTS = [
    line.strip()
    for line in open("requirements.txt", encoding="utf-8").readlines()
    if line.strip() and not line.startswith("#")
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
        ],
        "notebook": [
            "jupyter>=1.0.0",
            "ipykernel>=6.25.0",
            "jupyterlab>=3.6.0",
        ],
        "ml": [
            "tensorflow>=2.13.0",
            "torch>=2.0.0",
            "xgboost>=1.7.0",
            "lightgbm>=4.0.0",
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