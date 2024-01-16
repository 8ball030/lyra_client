"""
Sample for cancelling an order on the lyra client.
"""

from rich import print

from lyra.enums import Environment, OrderSide
from lyra.lyra import LyraClient
from tests.test_main import TEST_PRIVATE_KEY


def main():
    """
    Demonstrate canceling all orders on the lyra client.
    """

    client = LyraClient(TEST_PRIVATE_KEY, env=Environment.TEST)
    order = client.cancel_all(
    )
    print(order)


if __name__ == "__main__":
    main()
