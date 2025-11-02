"""
Configuration management for the quantitative trading system.
"""

import os
import yaml
from typing import Dict, Any, Union, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager for the trading system."""

    def __init__(self, config_path: str = None, env_file: str = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, uses default path.
            env_file: Path to .env file. If None, uses default path.
        """
        # Load environment variables first
        self._load_env_file(env_file)

        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        self.config_path = config_path
        self._config = self._load_config()

        # Override config with environment variables
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            ) from exc

    def _load_env_file(self, env_file: str = None) -> None:
        """Load environment variables from .env file."""
        if env_file is None:
            env_file = Path(__file__).parent / ".env"

        # Also try to load .env.example if .env doesn't exist
        if not Path(env_file).exists():
            example_env = Path(__file__).parent / ".env.example"
            if example_env.exists():
                print(
                    f"Warning: {env_file} not found. Loading {example_env} for reference."
                )
                # Don't actually load the example file, just show the warning
                return

        if Path(env_file).exists():
            load_dotenv(env_file)
            print(f"Loaded environment variables from {env_file}")

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # 环境变量到配置键的映射
        env_mappings = {
            # 数据源配置
            "ALPHA_VANTAGE_API_KEY": "market_data.alpha_vantage_api_key",
            "QUANDL_API_KEY": "market_data.quandl_api_key",
            "IEX_CLOUD_API_KEY": "market_data.iex_cloud.api_key",
            "IEX_CLOUD_BASE_URL": "market_data.iex_cloud.base_url",
            # 数据库配置
            "DATABASE_URL": "database.url",
            "POSTGRES_HOST": "database.postgres.host",
            "POSTGRES_PORT": "database.postgres.port",
            "POSTGRES_DB": "database.postgres.database",
            "POSTGRES_USER": "database.postgres.user",
            "POSTGRES_PASSWORD": "database.postgres.password",
            # 交易配置
            "INITIAL_CAPITAL": "trading.initial_capital",
            "MAX_POSITION_SIZE": "trading.max_position_size",
            "MAX_DAILY_LOSS": "risk_management.max_daily_loss",
            "MAX_DRAWDOWN": "risk_management.max_drawdown",
            "COMMISSION_RATE": "trading.commission_rate",
            "SLIPPAGE_RATE": "trading.slippage_rate",
            # 回测配置
            "BACKTEST_START_DATE": "backtesting.start_date",
            "BACKTEST_END_DATE": "backtesting.end_date",
            # 通知配置
            "EMAIL_SMTP_SERVER": "notifications.email.smtp_server",
            "EMAIL_SMTP_PORT": "notifications.email.smtp_port",
            "EMAIL_USERNAME": "notifications.email.username",
            "EMAIL_PASSWORD": "notifications.email.password",
            "EMAIL_FROM": "notifications.email.from",
            "EMAIL_TO": "notifications.email.to",
            # 日志配置
            "LOG_LEVEL": "logging.level",
            "LOG_FILE_PATH": "logging.file_path",
            "ENABLE_FILE_LOGGING": "logging.enable_file_logging",
            "ENABLE_CONSOLE_LOGGING": "logging.enable_console_logging",
            # 策略配置
            "MA_FAST_PERIOD": "strategies.moving_average.fast_period",
            "MA_SLOW_PERIOD": "strategies.moving_average.slow_period",
            "RSI_PERIOD": "strategies.rsi.period",
            "BOLLINGER_PERIOD": "strategies.bollinger.period",
            "BOLLINGER_STD": "strategies.bollinger.std_dev",
            # 开发配置
            "DEBUG_MODE": "development.debug_mode",
            "PAPER_TRADING": "trading.paper_trading",
            "API_TIMEOUT": "api.timeout",
            "DATA_CACHE_DURATION": "data.cache_duration",
            # Brokers
            "ALPACA_API_KEY": "brokers.registry.alpaca.credentials.api_key",
            "ALPACA_API_SECRET": "brokers.registry.alpaca.credentials.api_secret",
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 类型转换
                converted_value = self._convert_env_value(env_value)
                self.set(config_key, converted_value)

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type."""
        # 布尔值转换
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False

        # 数字转换
        try:
            # 尝试转换为整数
            if "." not in value:
                return int(value)
            # 尝试转换为浮点数
            return float(value)
        except ValueError:
            pass

        # 保持字符串
        return value

    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable value with type conversion.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value with appropriate type
        """
        env_value = os.getenv(key)
        if env_value is None:
            return default
        return self._convert_env_value(env_value)

    def set_env_mapping(self, env_var: str, config_key: str) -> None:
        """
        Add a new environment variable to configuration key mapping.

        Args:
            env_var: Environment variable name
            config_key: Configuration key (supports dot notation)
        """
        env_value = os.getenv(env_var)
        if env_value is not None:
            converted_value = self._convert_env_value(env_value)
            self.set(config_key, converted_value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'trading.initial_capital')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        current_config = self._config

        for k in keys[:-1]:
            if k not in current_config:
                current_config[k] = {}
            current_config = current_config[k]

        current_config[keys[-1]] = value

    def save(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, "w", encoding="utf-8") as file:
            yaml.dump(self._config, file, default_flow_style=False)

    @property
    def market_data(self) -> Dict[str, Any]:
        """Get market data configuration."""
        return self.get("market_data", {})

    @property
    def trading(self) -> Dict[str, Any]:
        """Get trading configuration."""
        return self.get("trading", {})

    @property
    def backtesting(self) -> Dict[str, Any]:
        """Get backtesting configuration."""
        return self.get("backtesting", {})

    @property
    def risk_management(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return self.get("risk_management", {})

    @property
    def brokers(self) -> Dict[str, Any]:
        """Get broker configuration."""
        return self.get("brokers", {})

    def resolve_broker(
        self,
        broker_id: Optional[str] = None,
        **overrides: Any,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Resolve broker type and parameters using configuration and environment variables.

        Args:
            broker_id: Desired broker identifier. If None, use the configured default.
            **overrides: Extra parameters to merge into broker configuration.

        Returns:
            Tuple of (broker_type, broker_params).

        Raises:
            EnvironmentError: When required credentials are missing.
        """
        brokers_cfg = self.brokers or {}
        default_id = brokers_cfg.get("default", "simulation")
        target_id = (broker_id or default_id).lower()
        registry = brokers_cfg.get("registry", {})
        definition = registry.get(target_id, {})

        if not definition:
            raise ValueError(f"Unknown broker '{broker_id or default_id}'")

        broker_type = definition.get("type", target_id)
        params = dict(definition.get("params") or {})
        credentials = definition.get("credentials") or {}

        # Direct credential values
        for key in ("api_key", "api_secret", "base_url"):
            if key in credentials and credentials[key]:
                params.setdefault(key, credentials[key])

        # Environment-based credentials
        env_mapping = {
            "api_key_env": "api_key",
            "api_secret_env": "api_secret",
        }
        missing_credentials = []
        for env_key, param_name in env_mapping.items():
            env_var = credentials.get(env_key)
            if env_var:
                env_value = self.get_env(env_var)
                if env_value is not None:
                    params.setdefault(param_name, env_value)
                else:
                    missing_credentials.append(env_var)

        # Merge overrides at the end
        params.update(overrides)

        # Validate mandatory credentials for known brokers
        if broker_type == "alpaca":
            required = ["api_key", "api_secret"]
            still_missing = [name for name in required if not params.get(name)]
            if still_missing:
                detail = ", ".join(still_missing)
                env_hint = (
                    ", ".join(missing_credentials) or "ALPACA_API_KEY/ALPACA_API_SECRET"
                )
                raise EnvironmentError(
                    f"Missing Alpaca credentials ({detail}). "
                    f"Please set environment variables ({env_hint}) or provide explicit parameters."
                )

        return broker_type, params


# Global configuration instance
config = Config()
