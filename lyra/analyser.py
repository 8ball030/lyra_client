"""
Class based analyser for portfolios.
"""

from typing import List, Optional

import pandas as pd

pd.set_option('display.precision', 2)


DELTA_COLUMNS = ['delta', 'gamma', 'vega', 'theta']


class PortfolioAnalyser:
    raw_data: List[dict]
    df: pd.DataFrame

    def __init__(self, raw_data: List[dict]):
        self.raw_data = raw_data
        self.positions = pd.DataFrame.from_records(raw_data['positions'])
        self.positions["amount"] = pd.to_numeric(self.positions["amount"])
        for col in DELTA_COLUMNS:
            self.positions[col] = pd.to_numeric(self.positions[col])
            adjusted_greek = self.positions[col] * self.positions.amount
            self.positions[col] = adjusted_greek

        self.positions = self.positions.apply(pd.to_numeric, errors='ignore')

    def get_positions(self, underlying_currency: str) -> pd.DataFrame:
        df = self.positions
        df = df[df['instrument_name'].str.contains(underlying_currency.upper())]
        return df

    def get_open_positions(self, underlying_currency: str) -> pd.DataFrame:
        df = self.get_positions(underlying_currency)
        return df[df['amount'] != 0]

    def get_total_greeks(self, underlying_currency: str) -> pd.DataFrame:
        df = self.get_open_positions(underlying_currency)
        return df[DELTA_COLUMNS].sum()

    def get_subaccount_value(self) -> float:
        return float(self.raw_data['subaccount_value'])

    def print_positions(self, underlying_currency: str, columns: Optional[List[str]] = None):
        df = self.get_open_positions(underlying_currency)
        if columns:
            df = df[[c for c in columns if c not in DELTA_COLUMNS] + DELTA_COLUMNS]
        print(df)
