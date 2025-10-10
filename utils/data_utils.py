"""
Data Utilities Module

This module provides utility functions for data processing,
validation, and transformation in quantitative trading.
"""

from typing import List, Tuple
import pandas as pd
import numpy as np


class DataUtils:
    """
    Collection of utility functions for data processing.
    """

    @staticmethod
    def validate_data(data: pd.DataFrame, required_columns: List[str] = None) -> bool:
        """
        Validate DataFrame structure and content

        Args:
            data: DataFrame to validate
            required_columns: List of required column names

        Returns:
            True if valid, False otherwise
        """
        if data.empty:
            return False

        if required_columns:
            missing_cols = set(required_columns) - set(data.columns)
            if missing_cols:
                print(f"Missing columns: {missing_cols}")
                return False

        # Check for null values in price columns
        price_cols = ["open", "high", "low", "close"]
        existing_price_cols = [col for col in price_cols if col in data.columns]

        if existing_price_cols and data[existing_price_cols].isnull().any().any():
            print("Warning: Null values found in price data")

        return True

    @staticmethod
    def clean_data(data: pd.DataFrame, method: str = "forward_fill") -> pd.DataFrame:
        """
        Clean data by handling missing values and outliers

        Args:
            data: DataFrame to clean
            method: Method for handling missing values ('forward_fill', 'drop', 'interpolate')

        Returns:
            Cleaned DataFrame
        """
        data_clean = data.copy()

        if method == "forward_fill":
            data_clean = data_clean.fillna(method="ffill")
        elif method == "drop":
            data_clean = data_clean.dropna()
        elif method == "interpolate":
            data_clean = data_clean.interpolate()

        return data_clean

    @staticmethod
    def resample_data(data: pd.DataFrame, frequency: str) -> pd.DataFrame:
        """
        Resample data to different frequency

        Args:
            data: DataFrame with datetime index
            frequency: Target frequency ('D', 'W', 'M', etc.)

        Returns:
            Resampled DataFrame
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have datetime index for resampling")

        # Define aggregation rules for OHLCV data
        agg_rules = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }

        # Apply rules only to existing columns
        existing_rules = {
            col: rule for col, rule in agg_rules.items() if col in data.columns
        }

        # Handle other columns (typically take last value)
        other_cols = set(data.columns) - set(existing_rules.keys())
        for col in other_cols:
            existing_rules[col] = "last"

        return data.resample(frequency).agg(existing_rules)

    @staticmethod
    def calculate_returns(prices: pd.Series, method: str = "simple") -> pd.Series:
        """
        Calculate returns from price series

        Args:
            prices: Series of prices
            method: 'simple' or 'log' returns

        Returns:
            Series of returns
        """
        if method == "simple":
            return prices.pct_change()
        elif method == "log":
            return np.log(prices / prices.shift(1))
        else:
            raise ValueError("Method must be 'simple' or 'log'")

    @staticmethod
    def normalize_data(data: pd.DataFrame, method: str = "z_score") -> pd.DataFrame:
        """
        Normalize data using various methods

        Args:
            data: DataFrame to normalize
            method: 'z_score', 'min_max', or 'robust'

        Returns:
            Normalized DataFrame
        """
        if method == "z_score":
            return (data - data.mean()) / data.std()
        elif method == "min_max":
            return (data - data.min()) / (data.max() - data.min())
        elif method == "robust":
            median = data.median()
            mad = (data - median).abs().median()
            return (data - median) / mad
        else:
            raise ValueError("Method must be 'z_score', 'min_max', or 'robust'")

    @staticmethod
    def detect_outliers(
        data: pd.Series, method: str = "iqr", threshold: float = 3.0
    ) -> pd.Series:
        """
        Detect outliers in data

        Args:
            data: Series to analyze
            method: 'iqr', 'z_score', or 'modified_z_score'
            threshold: Threshold for outlier detection

        Returns:
            Boolean series indicating outliers
        """
        if method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (data < lower_bound) | (data > upper_bound)

        elif method == "z_score":
            z_scores = np.abs((data - data.mean()) / data.std())
            return z_scores > threshold

        elif method == "modified_z_score":
            median = data.median()
            mad = (data - median).abs().median()
            modified_z_scores = 0.6745 * (data - median) / mad
            return np.abs(modified_z_scores) > threshold

        else:
            raise ValueError("Method must be 'iqr', 'z_score', or 'modified_z_score'")

    @staticmethod
    def split_data(
        data: pd.DataFrame, train_ratio: float = 0.8, validation_ratio: float = 0.1
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, and test sets

        Args:
            data: DataFrame to split
            train_ratio: Ratio for training data
            validation_ratio: Ratio for validation data

        Returns:
            Tuple of (train, validation, test) DataFrames
        """
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + validation_ratio))

        train = data.iloc[:train_end]
        validation = data.iloc[train_end:val_end]
        test = data.iloc[val_end:]

        return train, validation, test

    @staticmethod
    def align_data(*dataframes: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Align multiple DataFrames to common index

        Args:
            dataframes: Variable number of DataFrames to align

        Returns:
            List of aligned DataFrames
        """
        if not dataframes:
            return []

        # Find common index
        common_index = dataframes[0].index
        for df in dataframes[1:]:
            common_index = common_index.intersection(df.index)

        # Align all DataFrames to common index
        aligned = [df.loc[common_index] for df in dataframes]

        return aligned

    @staticmethod
    def rolling_window_split(
        data: pd.DataFrame, window_size: int, step_size: int = 1
    ) -> List[pd.DataFrame]:
        """
        Create rolling windows from data

        Args:
            data: DataFrame to split
            window_size: Size of each window
            step_size: Step size between windows

        Returns:
            List of DataFrames representing windows
        """
        windows = []
        start = 0

        while start + window_size <= len(data):
            window = data.iloc[start : start + window_size]
            windows.append(window)
            start += step_size

        return windows
