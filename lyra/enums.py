"""
Necessary enumarations for the Lyra project.
"""

from enum import Enum


class InstrumentType(Enum):
    """Instrument types."""

    ERC20 = "erc20"
    OPTION = "option"
    PERP = "perp"


class UnderlyingCurrency(Enum):
    """Underlying currencies."""

    ETH = "eth"
    BTC = "btc"


class OrderSide(Enum):
    """Order sides."""

    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order types."""

    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(Enum):
    """Time in force."""

    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class Environment(Enum):
    """Environment."""

    PROD = "prod"
    TEST = "test"
