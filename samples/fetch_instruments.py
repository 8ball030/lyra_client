"""
Sample of fetching instruments from the lyra client, and printing the result.
"""
from rich import print

from lyra.enums import Environment, InstrumentType
from lyra.lyra import LyraClient
from tests.test_main import TEST_PRIVATE_KEY


def main():
    """
    Demonstrate fetching instruments from the lyra client.
    """

    client = LyraClient(TEST_PRIVATE_KEY, env=Environment.TEST)

    for instrument_type in [InstrumentType.OPTION, InstrumentType.PERP]:
        print(f"Fetching instruments for {instrument_type}")
        instruments = client.fetch_instruments(instrument_type=instrument_type)
        print(instruments)


if __name__ == "__main__":
    main()
