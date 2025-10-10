"""
Example usage of the quantitative trading system.
"""

import sys
from pathlib import Path
from data import DataFetcher
from strategies import MovingAverageStrategy, MeanReversionStrategy
from backtesting import BacktestEngine


# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))


def main():
    """Main example demonstrating the trading system."""

    print("🚀 Quantitative Trading System Example")
    print("=" * 50)

    # Initialize components
    print("\n📊 Initializing data fetcher...")
    data_fetcher = DataFetcher()

    # Fetch sample data
    print("📈 Fetching market data for AAPL...")
    symbol = "AAPL"
    start_date = "2022-01-01"
    end_date = "2023-12-31"

    try:
        data = data_fetcher.fetch_stock_data(symbol, start_date, end_date)
        print(f"✅ Fetched {len(data)} days of data for {symbol}")
        print(
            f"   Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}"
        )
        print(
            f"   Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}"
        )
    except (ConnectionError, ValueError) as e:
        print(f"❌ Error fetching data: {e}")
        print(
            "💡 Make sure you have internet connection and required packages installed"
        )
        return

    # Test Moving Average Strategy
    print("\n🔄 Testing Moving Average Strategy...")
    ma_strategy = MovingAverageStrategy(short_window=20, long_window=50)

    try:
        ma_signals = ma_strategy.generate_signals(data)
        signal_count = (ma_signals["signal"] != 0).sum()
        print(f"✅ Generated {signal_count} signals")

        # Run backtest
        backtest_engine = BacktestEngine(initial_capital=100000)
        ma_results = backtest_engine.run_backtest(ma_strategy, data)

        print("📊 Moving Average Strategy Results:")
        print(f"   Total Return: {ma_results['total_return']:.2%}")
        print(f"   Annual Return: {ma_results['annual_return']:.2%}")
        print(f"   Volatility: {ma_results['volatility']:.2%}")
        print(f"   Sharpe Ratio: {ma_results['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {ma_results['max_drawdown']:.2%}")
        print(f"   Total Trades: {ma_results['total_trades']}")
        print(f"   Win Rate: {ma_results['win_rate']:.2%}")

    except (ValueError, KeyError, RuntimeError) as e:
        print(f"❌ Error running Moving Average strategy: {e}")

    # Test Mean Reversion Strategy
    print("\n🔄 Testing Mean Reversion Strategy...")
    mr_strategy = MeanReversionStrategy()

    try:
        mr_signals = mr_strategy.generate_signals(data)
        signal_count = (mr_signals["signal"] != 0).sum()
        print(f"✅ Generated {signal_count} signals")

        # Run backtest
        backtest_engine = BacktestEngine(initial_capital=100000)
        mr_results = backtest_engine.run_backtest(mr_strategy, data)

        print("📊 Mean Reversion Strategy Results:")
        print(f"   Total Return: {mr_results['total_return']:.2%}")
        print(f"   Annual Return: {mr_results['annual_return']:.2%}")
        print(f"   Volatility: {mr_results['volatility']:.2%}")
        print(f"   Sharpe Ratio: {mr_results['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {mr_results['max_drawdown']:.2%}")
        print(f"   Total Trades: {mr_results['total_trades']}")
        print(f"   Win Rate: {mr_results['win_rate']:.2%}")

    except (ValueError, KeyError, RuntimeError) as e:
        print(f"❌ Error running Mean Reversion strategy: {e}")

    print(
        "\n✨ Example completed! Check the strategies and backtesting modules for more details."
    )
    print("\n💡 Next steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Copy config/.env.example to config/.env")
    print("   3. Add your API keys to the .env file")
    print("   4. Explore the notebooks/ directory for analysis examples")


if __name__ == "__main__":
    main()
