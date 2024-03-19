"""
Base class for HTTP client.
"""

import time

from eth_account.messages import encode_defunct
from web3 import Web3

from lyra.base_client import BaseClient


class HttpClient(BaseClient):
    def _create_signature_headers(self):
        """
        Create the signature headers
        """
        timestamp = str(int(time.time() * 1000))
        msg = encode_defunct(
            text=timestamp,
        )
        signature = self.signer.sign_message(msg)
        return {
            "X-LyraWallet": self.wallet,
            "X-LyraTimestamp": timestamp,
            "X-LyraSignature": Web3.to_hex(signature.signature),
        }
