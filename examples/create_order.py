"""
Sample for creating an order on the lyra client.
"""

from rich import print

from lyra.enums import Environment, OrderSide
from lyra.lyra import LyraClient
from tests.test_main import TEST_PRIVATE_KEY


def main():
    """
    Demonstrate fetching instruments from the lyra client.
    """

    client = LyraClient(TEST_PRIVATE_KEY, env=Environment.TEST)
    order = client.create_order(
        instrument_name="BTC-PERP",
        side=OrderSide.BUY,
        price=1000,
        amount=1,
    )
    print(order)


if __name__ == "__main__":
    main()
