"""
Clas based analyser for portfolios.


    subaccount = client.fetch_subaccount(subaccount_id=subaccount_id)
    print(subaccount)

    df = pd.DataFrame.from_records(subaccount["collaterals"])

    positions = subaccount["positions"]

    df = pd.DataFrame.from_records(positions)
    df["amount"] = pd.to_numeric(df["amount"])
    delta_columns = ['delta', 'gamma', 'vega', 'theta']
    for col in delta_columns:
        df[col] = pd.to_numeric(df[col])
    if columns:
        columns = columns.split(",")
        df = df[[c for c in columns if c not in delta_columns] + delta_columns]
    print("Positions")
    open_positions = df[df['amount'] != 0]
    open_positions = open_positions[open_positions['instrument_name'].str.contains(underlying_currency.upper())]
    print("Greeks")
    for col in delta_columns:
        position_adjustment = open_positions[col] * df.amount
        open_positions[col] = position_adjustment
    print("Open positions")

    pd.options.display.float_format = "{:,.2f}".format

    open_positions = open_positions.sort_values(by=['instrument_name'])
    if columns:
        for col in columns:
            try:
                col = pd.to_numeric(open_positions[col])
            except:
                pass
        print(open_positions[columns])
    else:
        print(open_positions)

    # total deltas
    print("Total deltas")
    print(open_positions[delta_columns].sum())

    print("Subaccount values")
    print(subaccount['subaccount_value'])


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
