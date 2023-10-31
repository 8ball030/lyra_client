"""
Lyra is a Python library for trading on lyra v2
"""
import json
import time
from enum import Enum
import hashlib

# we need to encode the abi for the contract
# const encoder = ethers.AbiCoder.defaultAbiCoder();
# The ethers library is a JavaScript library, the equivalent in Python is eth_abi
#
import eth_abi
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


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(Enum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


ACTION_TYPEHASH = '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17'
DOMAIN_SEPARATOR = '0xff2ba7c8d1c63329d3c2c6c9c19113440c004c51fe6413f65654962afaff00f3'
ASSET_ADDRESS = '0x8932cc48F7AD0c6c7974606cFD7bCeE2F543a124'
TRADE_MODULE_ADDRESS = '0x63Bc9D10f088eddc39A6c40Ff81E99516dfD5269'

OPTION_NAME = 'ETH-20231027-1500-P'
OPTION_SUB_ID = '644245094401698393600'

CHAIN_ID = 901
w3 = Web3(Web3.HTTPProvider(BASE_URL))


def to_32byte_hex(val):
    return Web3.to_hex(Web3.to_bytes(val).rjust(32, b"\0"))


class LyraClient:
    """Client for the lyra dex."""

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

    def build_register_session_key_tx(self, expiry_sec: int):
        """Build register session key transaction."""

        endpoint = "build_register_session_key_tx"
        url = f"{BASE_URL}/public/{endpoint}"
        payload = {
            "expiry_sec": str(expiry_sec),
            "wallet": self.wallet.address,
            "gas": "0",
            "nonce": "0",
            "public_session_key": self.wallet.address,
        }
        response = requests.post(
            headers=PUBLIC_HEADERS,
            url=url,
            json=payload,
        )
        result = json.loads(response.content)["result"]
        return result

    def register_session_key(self, tx_params: dict, expiry_sec: int):
        """Register session key"""

        tx_params.pop("gasLimit", None)
        signed_tx = self.wallet.sign_transaction(tx_params)
        endpoint = "register_session_key"
        url = f"{BASE_URL}/public/{endpoint}"
        payload = {
            "expiry_sec": str(expiry_sec),
            "label": self.wallet.address[:16],
            "signed_raw_tx": signed_tx.rawTransaction.hex(),
            "public_session_key": self.wallet.address,
            "wallet": self.wallet.address,
        }
        response = requests.post(
            headers=PUBLIC_HEADERS,
            url=url,
            json=payload,
        )

        result = json.loads(response.content)["result"]
        return result

    def get_instruments(self, currency: UnderlyingCurrency, expired: bool, intrument_type: InstrumentType):
        """Get instruments."""

        endpoint = "get_instruments"
        url = f"{BASE_URL}/public/{endpoint}"
        payload = {
            "currency": currency.value.upper(),
            "expired": expired,
            "instrument_type": intrument_type.value,
        }
        response = requests.post(
            headers=PUBLIC_HEADERS,
            url=url,
            json=payload,
        )
        result = json.loads(response.content)["result"]
        return result

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
        """
        endpoint = "get_subaccounts"
        url = f"{BASE_URL}/private/{endpoint}"
        payload = {"wallet": wallet}
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = json.loads(response.content)["result"]
        return results

    def create_order(
        self,
        price,
        amount,
        instrument_name: str,
        reduce_only=False,
        side: OrderSide = OrderSide.BUY,
        order_type: OrderType = OrderType.LIMIT,
        time_in_force: TimeInForce = TimeInForce.GTC,
    ):
        """
        Create the order.
        """
        if side.name.upper() not in OrderSide.__members__:
            raise Exception(f"Invalid side {side}")
        endpoint = "order"
        url = f"{BASE_URL}/private/{endpoint}"

        order = self.__define_order(
            OPTION_NAME=instrument_name,
            subaccount_id="",
        )
        encoded_order = self.__encode_order(order)
        signed_order = self.__sign_order(encoded_order)
        print(url, signed_order)

    def __encode_order(self, order):
        """
        We have to do some work here.
        let encoded_data = encoder.encode( // same as "encoded_data" in public/order_debug
          ['address', 'uint', 'int', 'int', 'uint', 'uint', 'bool'],
          [
            ASSET_ADDRESS,
            OPTION_SUB_ID,
            ethers.parseUnits(order.limit_price.toString(), 18),
            ethers.parseUnits(order.amount.toString(), 18),
            ethers.parseUnits(order.max_fee.toString(), 18),
            order.subaccount_id, order.direction === 'buy']
          );
        return ethers.keccak256(Buffer.from(encoded_data.slice(2), 'hex'))
        """
        encoded = eth_abi.encode_abi(
            ["address", "uint", "int", "int", "uint", "uint", "bool"],
            [
                order["instrument_name"],
                order["subaccount_id"],
                order["limit_price"],
                order["amount"],
                order["max_fee"],
                order["nonce"],
                order["direction"] == "buy",
            ],
        )

        return w3.keccak(encoded)


def main():
    """Execute the main function."""
    print("Hello")
