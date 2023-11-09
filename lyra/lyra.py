"""
Lyra is a Python library for trading on lyra v2
"""
import json
import random
import time
from datetime import datetime

import eth_abi
import requests
from eth_account.messages import encode_defunct
from web3 import Web3
from websocket import create_connection

from lyra.enums import InstrumentType, OrderSide, OrderType, TimeInForce

BASE_URL = "https://api-demo.lyra.finance"

PUBLIC_HEADERS = {"accept": "application/json", "content-type": "application/json"}

ACTION_TYPEHASH = '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17'
DOMAIN_SEPARATOR = '0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105'
ASSET_ADDRESS = '0x010e26422790C6Cb3872330980FAa7628FD20294'
TRADE_MODULE_ADDRESS = '0x87F2863866D85E3192a35A73b388BD625D83f2be'

OPTION_NAME = 'ETH-PERP'
OPTION_SUB_ID = '0'

WS_ADDRESS = "wss://api-demo.lyra.finance/ws"

subaccount_id = 5


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

    def __init__(self, private_key, logger, env, verbose=False):
        """
        Initialize the LyraClient class.
        """
        self.logger = logger
        self.verbose = verbose
        self.env = env
        self.web3_client = Web3()
        self.wallet = self.web3_client.eth.account.from_key(private_key)

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
        order = self._define_order()
        self.logger.info("Raw order:")
        self.logger.info(order)
        signed_order = self._sign_order(order)
        ws = self.connect_ws()
        self.login_client(ws)
        response = self.submit_order(signed_order, ws)
        return response

    def submit_order(self, order, ws):
        id = str(int(time.time()))
        ws.send(json.dumps({'method': 'private/order', 'params': order, 'id': id}))
        self.logger.info(order)
        while True:
            message = json.loads(ws.recv())
            if message['id'] == id:
                print('Got order response:', message)
                return message

    def sign_authentication_header(self):
        timestamp = str(int(time.time() * 1000))
        msg = encode_defunct(
            text=timestamp,
        )
        signature = self.web3_client.eth.account.sign_message(
            msg, private_key=self.wallet._private_key
        ).signature.hex()  # pylint: disable=protected-access
        return {
            'wallet': self.wallet.address,
            'timestamp': str(timestamp),
            'signature': signature,
        }

    def connect_ws(self):
        ws = create_connection(WS_ADDRESS)
        return ws

    def login_client(self, ws):
        login_request = json.dumps(
            {'method': 'public/login', 'params': self.sign_authentication_header(), 'id': str(int(time.time()))}
        )
        ws.send(login_request)
        time.sleep(2)

    def create_subaccount(
        amount,
        asset_name,
        currency="USDT",
        margin_type="SM",
    ):
        """
        Create a subaccount
        """
        endpoint = "create_subaccount"
        url = f"{BASE_URL}/private/{endpoint}"

        payload = {
            "amount": "",
            "asset_name": "string",
            "currency": "string",
            "margin_type": "PM",
            "nonce": 0,
            "signature": "string",
            "signature_expiry_sec": 0,
            "signer": "string",
            "wallet": "string",
        }
        headers = {"accept": "application/json", "content-type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        print(response.text)

    def _define_order(
        self,
    ):
        """
        Define the order, in preparation for encoding and signing
        """
        ts = int(datetime.now().timestamp() * 1000)
        return {
            'instrument_name': OPTION_NAME,
            'subaccount_id': subaccount_id,
            'direction': 'buy',
            'limit_price': 1310,
            'amount': 100,
            'signature_expiry_sec': int(ts) + 3000,
            'max_fee': '10.01',
            'nonce': int(f"{int(ts)}{random.randint(100, 999)}"),
            'signer': self.wallet.address,
            'order_type': 'limit',
            'mmp': False,
            'signature': 'filled_in_below',
        }

    def _encode_trade_data(self, order):
        encoded_data = eth_abi.encode(
            ['address', 'uint256', 'int256', 'int256', 'uint256', 'uint256', 'bool'],
            [
                ASSET_ADDRESS,
                int(OPTION_SUB_ID),
                self.web3_client.to_wei(order['limit_price'], 'ether'),
                self.web3_client.to_wei(order['amount'], 'ether'),
                self.web3_client.to_wei(order['max_fee'], 'ether'),
                order['subaccount_id'],
                order['direction'] == 'buy',
            ],
        )

        return self.web3_client.keccak(encoded_data)

    def _sign_order(self, order):
        trade_module_data = self._encode_trade_data(order)
        print('Signing Trade module data:', trade_module_data.hex())
        encoded_action_hash = eth_abi.encode(
            ['bytes32', 'uint256', 'uint256', 'address', 'bytes32', 'uint256', 'address', 'address'],
            [
                bytes.fromhex(ACTION_TYPEHASH[2:]),
                order['subaccount_id'],
                order['nonce'],
                TRADE_MODULE_ADDRESS,
                trade_module_data,
                order['signature_expiry_sec'],
                self.wallet.address,
                order['signer'],
            ],
        )

        action_hash = self.web3_client.keccak(encoded_action_hash)
        print('Signing Action hash:', action_hash.hex())
        encoded_typed_data_hash = "".join(['0x1901', DOMAIN_SEPARATOR[2:], action_hash.hex()[2:]])
        typed_data_hash = self.web3_client.keccak(hexstr=encoded_typed_data_hash)
        print('Typed data hash:', typed_data_hash.hex())
        order['signature'] = self.wallet.signHash(typed_data_hash).signature.hex()
        return order


def main():
    """Execute the main function."""
    from tests.test_main import TEST_PRIVATE_KEY

    client = LyraClient(TEST_PRIVATE_KEY)
    client.create_order(
        instrument_name="ETH-PERP",
        price=1310,
        amount=100,
    )


if __name__ == "__main__":
    main()
