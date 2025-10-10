<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Quantitative Trading Project Instructions

This project is a comprehensive quantitative trading system built with Python. When working on this project, please follow these guidelines:

## Project Structure
- `data/` - Market data storage and management
- `strategies/` - Trading strategy implementations
- `backtesting/` - Backtesting framework and results
- `risk_management/` - Risk assessment and management tools
- `portfolio/` - Portfolio optimization and management
- `utils/` - Utility functions and helpers
- `config/` - Configuration files
- `tests/` - Unit and integration tests

## Development Guidelines
- Use type hints for all function signatures
- Follow PEP 8 coding standards
- Include comprehensive docstrings for all classes and functions
- Implement proper error handling and logging
- Use vectorized operations with pandas/numpy for performance
- Follow financial industry best practices for risk management

## Key Dependencies
- pandas, numpy for data manipulation
- yfinance, alpha_vantage for market data
- scikit-learn for machine learning models
- matplotlib, plotly for visualization
- pytest for testing
- python-dotenv for environment management

## Testing
- Write unit tests for all strategy logic
- Include backtesting validation
- Test edge cases and error conditions
- Use mock data for consistent testing

## Documentation
- Document all trading strategies with mathematical formulas
- Include performance metrics and risk assessments
- Provide examples of how to use each module