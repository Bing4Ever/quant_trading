from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when executing from scripts/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import config as app_config  # type: ignore  # noqa: E402
from src.tradingagent.core.brokers import BrokerFactory  # type: ignore  # noqa: E402

def main() -> None:
    broker_type, params = app_config.resolve_broker("alpaca")
    print(f"Resolved broker => {broker_type}, params keys: {list(params.keys())}")

    broker = BrokerFactory.create(broker_type, **params)
    ok = broker.connect()
    print(f"connect() -> {ok}")

    if ok:
        account = broker.get_account_balance()
        print("Account balance:", account)
        broker.disconnect()

if __name__ == "__main__":
    main()
