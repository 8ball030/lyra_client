"""
Cli module in order to allow interaction.
"""
import os

import rich_click as click
from dotenv import load_dotenv

from lyra.enums import Environment
from lyra.lyra import LyraClient
from lyra.utils import get_logger

click.rich_click.USE_RICH_MARKUP = True


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
        chain = os.environ.get("ENVIROMENT")
        if chain == Environment.PROD.value:
            env = Environment.PROD
        else:
            env = Environment.TEST
        ctx.client = LyraClient(**auth, env=env)
        breakpoint()
        if not ctx.client.web3_client.isConnected():
            raise ConnectionError("Web3 client not connected.")
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


@cli.group("markets")
def markets():
    """Interact with markets."""


@markets.command("fetch")
@click.pass_context
def fetch_markets(ctx):
    """Fetch markets."""
    client = ctx.obj["client"]
    markets = client.fetch_markets()
    click.echo(markets)
