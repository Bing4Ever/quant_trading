"""
Configuration management for the quantitative trading system.
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


class Config:
    """Configuration manager for the trading system."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default path.
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            # If config.yaml doesn't exist, try to load example config
            example_path = Path(self.config_path).parent / "config.example.yaml"
            if example_path.exists():
                print(f"Warning: {self.config_path} not found. Using example config.")
                with open(example_path, 'r') as file:
                    return yaml.safe_load(file)
            else:
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'trading.initial_capital')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
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
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w') as file:
            yaml.dump(self._config, file, default_flow_style=False)
    
    @property
    def market_data(self) -> Dict[str, Any]:
        """Get market data configuration."""
        return self.get('market_data', {})
    
    @property
    def trading(self) -> Dict[str, Any]:
        """Get trading configuration."""
        return self.get('trading', {})
    
    @property
    def backtesting(self) -> Dict[str, Any]:
        """Get backtesting configuration."""
        return self.get('backtesting', {})
    
    @property
    def risk_management(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return self.get('risk_management', {})


# Global configuration instance
config = Config()