"""
Cli module in order to allow interaction.
"""
import os

import pandas as pd
import rich_click as click
from dotenv import load_dotenv
from rich import print

from lyra.analyser import PortfolioAnalyser
from lyra.enums import (
    CollateralAsset,
    Environment,
    InstrumentType,
    OrderSide,
    OrderStatus,
    OrderType,
    SubaccountType,
    UnderlyingCurrency,
)
from lyra.lyra import LyraClient
from lyra.utils import get_logger

click.rich_click.USE_RICH_MARKUP = True
pd.set_option('display.precision', 2)


def set_logger(ctx, level):
    """Set the logger."""
    if not hasattr(ctx, "logger"):
        ctx.logger = get_logger()
        ctx.logger.setLevel(level)
    return ctx.logger


def set_client(ctx):
    """Set the client."""
    # we use dotenv to load the env vars from DIRECTORY where the cli tool is executed
    _path = os.getcwd()
    env_path = os.path.join(_path, ".env")
    load_dotenv(dotenv_path=env_path)
    if not hasattr(ctx, "client"):
        auth = {
            "private_key": os.environ.get("ETH_PRIVATE_KEY"),
            "logger": ctx.logger,
            "verbose": ctx.logger.level == "DEBUG",
        }
        chain = os.environ.get("ENVIRONMENT")
        if chain == Environment.PROD.value:
            env = Environment.PROD
        else:
            env = Environment.TEST

        subaccount_id = os.environ.get("SUBACCOUNT_ID", None)
        if subaccount_id:
            subaccount_id = int(subaccount_id)
        wallet = os.environ.get("WALLET")
        ctx.client = LyraClient(**auth, env=env, subaccount_id=subaccount_id, wallet=wallet)

    if ctx.logger.level == "DEBUG":
        print(f"Client created for environment `{ctx.client.env.value}`")
    return ctx.client


@click.group("Lyra Client")
@click.option(
    "--log-level",
    "-l",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Logging level.",
)
@click.pass_context
def cli(ctx, log_level):
    """Lyra v2 client command line interface."""
    ctx.ensure_object(dict)
    ctx.obj["logger"] = set_logger(ctx, log_level)
    ctx.obj["client"] = set_client(ctx)


@cli.group("instruments")
def instruments():
    """Interact with markets."""


@cli.group("tickers")
def tickers():
    """Interact with tickers."""


@cli.group("subaccounts")
def subaccounts():
    """Interact with subaccounts."""


@cli.group("orders")
def orders():
    """Interact with orders."""


@cli.group("collateral")
def collateral():
    """Interact with collateral."""


@cli.group("positions")
def positions():
    """Interact with positions."""


@positions.command("fetch")
@click.pass_context
def fetch_positions(ctx):
    """Fetch positions."""
    print("Fetching positions")
    client = ctx.obj["client"]
    positions = client.get_positions()
    print(positions)


@collateral.command("fetch")
@click.pass_context
def fetch_collateral(ctx):
    """Fetch collateral."""
    print("Fetching collateral")
    client = ctx.obj["client"]
    collateral = client.get_collaterals()
    print(collateral)


@instruments.command("fetch")
@click.pass_context
@click.option(
    "--instrument-type",
    "-i",
    type=click.Choice([f.value for f in InstrumentType]),
    default=InstrumentType.PERP.value,
)
@click.option(
    "--currency",
    "-c",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
def fetch_instruments(ctx, instrument_type, currency):
    """Fetch markets."""
    client = ctx.obj["client"]
    markets = client.fetch_instruments(
        instrument_type=InstrumentType(instrument_type), currency=UnderlyingCurrency(currency)
    )
    print(markets)


@tickers.command("fetch")
@click.pass_context
@click.argument(
    "instrument_name",
    type=str,
)
def fetch_tickers(ctx, instrument_name):
    """Fetch tickers."""
    client = ctx.obj["client"]
    ticker = client.fetch_ticker(instrument_name=instrument_name)
    print(ticker)


@collateral.command("transfer")
@click.pass_context
@click.option(
    "--amount",
    "-a",
    type=float,
    required=True,
)
@click.option(
    "--to",
    "-t",
    type=int,
    required=True,
    help="Subaccount ID to transfer to",
)
@click.option(
    "--asset",
    "-s",
    type=click.Choice([f.value for f in CollateralAsset]),
    default=CollateralAsset.USDC.value,
)
def transfer_collateral(ctx, amount, to, asset):
    """Transfer collateral."""
    client = ctx.obj["client"]
    result = client.transfer_collateral(amount=amount, to=to, asset=CollateralAsset(asset))

    print(result)


@subaccounts.command("all")
@click.pass_context
def fetch_subaccounts(ctx):
    """Fetch subaccounts."""
    print("Fetching subaccounts")
    client = ctx.obj["client"]
    subaccounts = client.fetch_subaccounts()
    print(subaccounts)


@subaccounts.command("fetch")
@click.argument(
    "subaccount_id",
    type=int,
)
@click.option(
    "--underlying-currency",
    "-u",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
@click.option(
    "--columns",
    "-c",
    type=str,
    default=None,
)
@click.pass_context
def fetch_subaccount(ctx, subaccount_id, underlying_currency, columns):
    """Fetch subaccount."""
    print("Fetching subaccount")
    print(f"Subaccount ID: {subaccount_id}")
    print(f"Underlying currency: {underlying_currency}")
    client = ctx.obj["client"]
    subaccount = client.fetch_subaccount(subaccount_id=subaccount_id)
    analyser = PortfolioAnalyser(subaccount)
    print("Positions")
    analyser.print_positions(underlying_currency=underlying_currency, columns=columns)
    print("Total Greeks")
    print(analyser.get_total_greeks(underlying_currency))
    print("Subaccount values")
    print(f"Portfolio Value: ${analyser.get_subaccount_value():.2f}")


@subaccounts.command("create")
@click.pass_context
@click.option(
    "--underlying-currency",
    "-u",
    type=click.Choice([f.value for f in UnderlyingCurrency]),
    default=UnderlyingCurrency.ETH.value,
)
@click.option(
    "--subaccount-type",
    "-s",
    type=click.Choice([f.value for f in SubaccountType]),
    default=SubaccountType.PORTFOLIO.value,
)
@click.option(
    "--collateral-asset",
    "-c",
    type=click.Choice([f.value for f in CollateralAsset]),
    default=CollateralAsset.USDC.value,
)
@click.option(
    "--amount",
    "-a",
    type=float,
    default=0,
)
def create_subaccount(ctx, collateral_asset, underlying_currency, subaccount_type, amount):
    """Create subaccount."""
    underlying_currency = UnderlyingCurrency(underlying_currency)
    subaccount_type = SubaccountType(subaccount_type)
    collateral_asset = CollateralAsset(collateral_asset)
    print(f"Creating subaccount with collateral asset {collateral_asset} and underlying currency {underlying_currency}")
    client = ctx.obj["client"]
    subaccount_id = client.create_subaccount(
        amount=int(amount * 1e6),
        subaccount_type=subaccount_type,
        collateral_asset=collateral_asset,
        underlying_currency=underlying_currency,
    )
    print(subaccount_id)


@orders.command("fetch")
@click.pass_context
@click.option(
    "--instrument-name",
    "-i",
    type=str,
    default=None,
)
@click.option(
    "--label",
    "-l",
    type=str,
    default=None,
)
@click.option(
    "--page",
    "-p",
    type=int,
    default=1,
)
@click.option(
    "--page-size",
    "-s",
    type=int,
    default=100,
)
@click.option(
    "--status",
    "-s",
    type=click.Choice([f.value for f in OrderStatus]),
    default=None,
)
@click.option(
    "--regex",
    "-r",
    type=str,
    default=None,
)
def fetch_orders(ctx, instrument_name, label, page, page_size, status, regex):
    """Fetch orders."""
    print("Fetching orders")
    client = ctx.obj["client"]
    orders = client.fetch_orders(
        instrument_name=instrument_name,
        label=label,
        page=page,
        page_size=page_size,
        status=status,
    )
    # apply the regex if exists to filter the orders
    if regex:
        orders = [o for o in orders if regex in o["instrument_name"]]
    df = pd.DataFrame.from_records(orders)
    instrument_names = df["instrument_name"].unique()
    print(f"Found {len(instrument_names)} instruments")
    print(instrument_names)
    # print the orders
    # perform some analysis
    df['amount'] = pd.to_numeric(df['amount'])
    df['filled_amount'] = pd.to_numeric(df['filled_amount'])
    df['limit_price'] = pd.to_numeric(df['limit_price'])

    buys = df[df['direction'] == 'buy']
    sells = df[df['direction'] == 'sell']
    print("Buys")
    print(buys)
    print("Sells")
    print(sells)

    print("Average buy cost")
    # we determine by the average price of the buys by the amount
    df['cost'] = buys['limit_price'] * buys['amount']
    print(df['cost'].sum())
    amount = buys['amount'].sum()
    print(amount)
    buy_total_cost = df['cost'].sum()
    print(f"Price per unit: {buy_total_cost / amount}")
    print(buy_total_cost / amount)
    print("Average sell cost")
    # we determine by the average price of the buys by the amount
    df['cost'] = sells['limit_price'] * sells['amount']
    print(df['cost'].sum())
    amount = sells['amount'].sum()
    print(amount)
    sell_total_cost = df['cost'].sum()
    print(f"Price per unit: {sell_total_cost / amount}")
    print(sell_total_cost / amount)


@orders.command("cancel")
@click.pass_context
@click.option(
    "--order-id",
    "-o",
    type=str,
)
@click.option(
    "--instrument-name",
    "-i",
    type=str,
)
def cancel_order(ctx, order_id, instrument_name):
    """Cancel order."""
    print("Cancelling order")
    client = ctx.obj["client"]
    result = client.cancel(order_id=order_id, instrument_name=instrument_name)
    print(result)


@orders.command("cancel_all")
@click.pass_context
def cancel_all_orders(ctx):
    """Cancel all orders."""
    print("Cancelling all orders")
    client = ctx.obj["client"]
    result = client.cancel_all()
    print(result)


@orders.command("create")
@click.pass_context
@click.option(
    "--instrument-name",
    "-i",
    type=str,
    required=True,
)
@click.option(
    "--side",
    "-s",
    type=click.Choice(i.value for i in OrderSide),
    required=True,
)
@click.option(
    "--price",
    "-p",
    type=float,
    required=True,
)
@click.option(
    "--amount",
    "-a",
    type=float,
    required=True,
)
@click.option(
    "--order-type",
    "-t",
    type=click.Choice(i.value for i in OrderType),
    default="limit",
)
def create_order(ctx, instrument_name, side, price, amount, order_type):
    """Create order."""
    print("Creating order")
    client = ctx.obj["client"]
    result = client.create_order(
        instrument_name=instrument_name,
        side=OrderSide(side),
        price=price,
        amount=amount,
        order_type=OrderType(order_type),
    )
    print(result)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
