# Manual Test Scripts

| Script | Function | Execution |
| --- | --- | --- |
| `tests/manual/test_chart_generator_price.py` | Generates a price/signal chart via `InteractiveChartGenerator.create_price_signal_chart` (default ticker `AAPL`) and writes the PNG to `charts/` for manual inspection. | `python tests/manual/test_chart_generator_price.py` |

# Automation Test Scripts

| Script | Function | Execution |
| --- | --- | --- |
| `tests/automation/test_chart_generator.py` | Uses synthetic OHLCV data to assert that `InteractiveChartGenerator.create_price_signal_chart` returns a Matplotlib figure (no live API calls). | `pytest tests/automation/test_chart_generator.py` |
| `tests/automation/test_task_manager_reconcile.py` | Stubs an in-memory broker to verify `TaskManager.reconcile_orders` surfaces terminal order statuses. | `pytest tests/automation/test_task_manager_reconcile.py` |
| `tests/automation/test_live_runtime.py` | Checks that `LiveTradingRuntime` wires a provided broker/data provider and toggles monitoring lifecycle without external services. | `pytest tests/automation/test_live_runtime.py` |
