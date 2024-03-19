"""
Lyra is a Python library for trading on lyra v2
"""

import pandas as pd
from web3 import Web3

from lyra.base_client import BaseClient
from lyra.http_client import HttpClient

# we set to show 4 decimal places
pd.options.display.float_format = '{:,.4f}'.format


def to_32byte_hex(val):
    return Web3.to_hex(Web3.to_bytes(val).rjust(32, b"\0"))


class LyraClient(BaseClient):
    """Client for the lyra dex."""

    http_client: HttpClient

    def _create_signature_headers(self):
        """Generate the signature headers."""
        return self.http_client._create_signature_headers()

    def __init__(self, *args, **kwargs):
        self.http_client = HttpClient(
            *args,
            **kwargs,
        )
        super().__init__(*args, **kwargs)
