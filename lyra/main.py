"""
Lyra is a Python library for trading on lyra v2
"""
import json
import time
from enum import Enum

import requests
from eth_account.messages import encode_defunct
from web3 import Web3

BASE_URL = "https://api-demo.lyra.finance"

PUBLIC_HEADERS = {"accept": "application/json", "content-type": "application/json"}


class InstrumentType(Enum):
    ERC20 = "erc20"
    OPTION = "option"
    PERP = "perp"


class UnderlyingCurrency(Enum):
    ETH = "eth"
    BTC = "btc"


w3 = Web3()


def to_32byte_hex(val):
    return Web3.to_hex(Web3.to_bytes(val).rjust(32, b"\0"))


class LyraClient:
    def __init__(self, private_key):
        """
        Initialize the LyraClient class.
        """
        self.wallet = w3.eth.account.from_key(private_key)

    def create_account(self, wallet):
        """Call the create account endpoint."""
        endpoint = "create_account"
        payload = {"wallet": wallet}
        url = f"{BASE_URL}/public/{endpoint}"
        result = requests.post(
            headers=PUBLIC_HEADERS,
            url=url,
            json=payload,
        )
        result_code = json.loads(result.content)

        if "error" in result_code:
            raise Exception(result_code["error"])
        return True

    def fetch_tickers(
        self,
        expired=True,
        instrument_type="erc20",
        page=1,
        page_size=20,
        currency="eth",
    ):
        """Return the tickers"""
        if instrument_type.upper() not in InstrumentType.__members__:
            raise Exception(f"Invalid instrument type {instrument_type}")
        endpoint = "get_tickers"
        url = f"{BASE_URL}/public/{endpoint}"
        payload = {
            "expired": expired,
            "instrument_type": instrument_type,
            "page": page,
            "page_size": page_size,
            "currency": currency.upper(),
        }
        headers = {"accept": "application/json", "content-type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)

        results = json.loads(response.content)["result"]
        return results

    def fetch_subaccounts(self, wallet):
        """
        Returns the subaccounts for a given wallet
        let wallet = new ethers.Wallet(process.env.OWNER_PRIVATE_KEY as string, provider);
        let timestamp = Date.now() // ensure UTC
        let signature = (await wallet.signMessage(timestamp)).toString()

        const response = await axios.request<R>({
          "POST",
          "https://api-demo.lyra.finance/private/get_subaccounts",
          {wallet: wallet.address},
          {
                "X-LyraWallet": wallet.address,
                "X-LyraTimestamp": timestamp,
                "X-LyraSignature": signature
          }
        });
        """
        endpoint = "get_subaccounts"
        url = f"{BASE_URL}/private/{endpoint}"
        payload = {"wallet": wallet}
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = json.loads(response.content)["result"]
        return results

    def _create_signature_headers(self):
        """
        Create the signature headers
        """
        timestamp = str(int(time.time() * 1000))
        msg = encode_defunct(
            text=timestamp,
        )
        signature = self.wallet.sign_message(msg)
        return {
            "X-LyraWallet": self.wallet.address,
            "X-LyraTimestamp": timestamp,
            "X-LyraSignature": Web3.to_hex(signature.signature),
        }


def main():
    """Execute the main function."""
    print("Hello")
