"""
Data manager for storing and retrieving market data.
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime
import sqlite3
import pandas as pd
from config import config
from .data_fetcher import DataFetcher

SQLITE_PREFIX = "sqlite:///"

class DataManager:
    """
    Manages market data storage and retrieval.
    """

    def __init__(self, data_dir: str = None, db_url: str = None):
        """
        Initialize data manager.

        Args:
            data_dir: Directory for storing data files
            db_url: Database URL for data storage
        """
        self.data_dir = Path(
            data_dir or config.get("market_data.data_directory", "./data/")
        )
        self.db_url = db_url or config.get(
            "market_data.database_url", f"{SQLITE_PREFIX}market_data.db"
        )
        self.data_fetcher = DataFetcher()

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        if self.db_url.startswith(SQLITE_PREFIX):
            db_path = self.db_url.replace(SQLITE_PREFIX, "")
            conn = sqlite3.connect(db_path)

            # Create tables
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_data (
                    symbol TEXT,
                    date DATE,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    adjusted_close REAL,
                    PRIMARY KEY (symbol, date)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_updates (
                    symbol TEXT PRIMARY KEY,
                    last_update TIMESTAMP
                )
            """
            )

            conn.commit()
            conn.close()

    def get_stock_data(
        self,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None,
        force_update: bool = False,
    ) -> pd.DataFrame:
        """
        Get stock data, fetching from cache or external source as needed.

        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data
            force_update: Force update from external source

        Returns:
            DataFrame with stock data
        """
        # Check if we need to update data
        if force_update or self._needs_update(symbol, end_date):
            self._update_stock_data(symbol, start_date, end_date)

        # Retrieve data from database
        return self._get_cached_data(symbol, start_date, end_date)

    def _needs_update(self, symbol: str, end_date: datetime = None) -> bool:
        """Check if symbol data needs updating."""
        if end_date is None:
            end_date = datetime.now()

        if self.db_url.startswith(SQLITE_PREFIX):
            db_path = self.db_url.replace(SQLITE_PREFIX, "")
            conn = sqlite3.connect(db_path)

            cursor = conn.execute(
                "SELECT last_update FROM data_updates WHERE symbol = ?", (symbol,)
            )

            result = cursor.fetchone()
            conn.close()

            if result is None:
                return True

            last_update = datetime.fromisoformat(result[0])
            # Update if data is more than 1 day old
            return (end_date - last_update).days > 1

        return True

    def _update_stock_data(
        self, symbol: str, start_date: datetime = None, end_date: datetime = None
    ):
        """Update stock data from external source."""
        try:
            # Fetch new data
            data = self.data_fetcher.fetch_stock_data(symbol, start_date, end_date)

            if data.empty:
                return

            # Store in database
            self._store_data(symbol, data)

            # Update last update timestamp
            self._update_timestamp(symbol)

        except (sqlite3.DatabaseError, ValueError) as e:
            print(f"Database or value error updating data for {symbol}: {e}")
        except sqlite3.Error as e:
            print(f"SQLite error updating data for {symbol}: {e}")
        except pd.errors.EmptyDataError as e:
            print(f"Pandas empty data error updating data for {symbol}: {e}")

    def _store_data(self, symbol: str, data: pd.DataFrame):
        """Store data in database."""
        if self.db_url.startswith(SQLITE_PREFIX):
            db_path = self.db_url.replace(SQLITE_PREFIX, "")
            conn = sqlite3.connect(db_path)

            # Prepare data for insertion
            data_to_insert = data.copy()
            data_to_insert["symbol"] = symbol
            data_to_insert.reset_index(inplace=True)
            data_to_insert.rename(columns={"Date": "date"}, inplace=True)

            # Insert data (replace if exists)
            data_to_insert.to_sql(
                "stock_data",
                conn,
                if_exists="append",
                index=False,
                method="ignore",  # Ignore duplicates
            )

            conn.close()

    def _update_timestamp(self, symbol: str):
        """Update last update timestamp for symbol."""
        if self.db_url.startswith(SQLITE_PREFIX):
            db_path = self.db_url.replace(SQLITE_PREFIX, "")
            conn = sqlite3.connect(db_path)

            conn.execute(
                """INSERT OR REPLACE INTO data_updates (symbol, last_update) 
                   VALUES (?, ?)""",
                (symbol, datetime.now().isoformat()),
            )

            conn.commit()
            conn.close()

    def _get_cached_data(
        self, symbol: str, start_date: datetime = None, end_date: datetime = None
    ) -> pd.DataFrame:
        """Retrieve cached data from database."""
        if self.db_url.startswith("sqlite"):
            db_path = self.db_url.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)

            query = "SELECT * FROM stock_data WHERE symbol = ?"
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date.strftime("%Y-%m-%d"))

            if end_date:
                query += " AND date <= ?"
                params.append(end_date.strftime("%Y-%m-%d"))

            query += " ORDER BY date"

            data = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if not data.empty:
                data["date"] = pd.to_datetime(data["date"])
                data.set_index("date", inplace=True)
                data.drop("symbol", axis=1, inplace=True)

            return data

        return pd.DataFrame()

    def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: datetime = None,
        end_date: datetime = None,
        force_update: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple stocks.

        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data
            force_update: Force update from external source

        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_data(
                symbol, start_date, end_date, force_update
            )

        return results

    def create_price_matrix(
        self,
        symbols: List[str],
        column: str = "close",
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> pd.DataFrame:
        """
        Create a price matrix for multiple symbols.

        Args:
            symbols: List of stock symbols
            column: Price column to use ('open', 'high', 'low', 'close')
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with symbols as columns and dates as index
        """
        data_dict = self.get_multiple_stocks(symbols, start_date, end_date)

        price_data = {}
        for symbol, data in data_dict.items():
            if not data.empty and column in data.columns:
                price_data[symbol] = data[column]

        if not price_data:
            return pd.DataFrame()

        return pd.DataFrame(price_data)
