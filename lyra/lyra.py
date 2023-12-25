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

from lyra.constants import CONTRACTS, PUBLIC_HEADERS
from lyra.enums import InstrumentType, OrderSide, OrderStatus, OrderType, TimeInForce, UnderlyingCurrency
from lyra.utils import get_logger

OPTION_NAME = 'ETH-PERP'
OPTION_SUB_ID = '0'


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

    def __init__(self, private_key, env, logger=None, verbose=False, subaccount_id=None):
        """
        Initialize the LyraClient class.
        """
        self.verbose = verbose
        self.contracts = CONTRACTS[env]
        self.logger = logger or get_logger()
        self.web3_client = Web3()
        self.wallet = self.web3_client.eth.account.from_key(private_key)
        if not subaccount_id:
            self.subaccount_id = self.fetch_subaccounts(self.wallet.address)['subaccount_ids'][0]

    def create_account(self, wallet):
        """Call the create account endpoint."""
        payload = {"wallet": wallet}
        url = f"{self.contracts['BASE_URL']}/public/create_account"
        result = requests.post(
            headers=PUBLIC_HEADERS,
            url=url,
            json=payload,
        )
        result_code = json.loads(result.content)

        if "error" in result_code:
            raise Exception(result_code["error"])
        return True

    def fetch_instruments(
        self,
        expired=False,
        instrument_type: InstrumentType = InstrumentType.PERP,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        """
        Return the tickers.
        First fetch all instrucments
        Then get the ticket for all instruments.
        """
        url = f"{self.contracts['BASE_URL']}/public/get_instruments"
        payload = {
            "expired": expired,
            "instrument_type": instrument_type.value,
            "currency": currency.name,
        }
        headers = {"accept": "application/json", "content-type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        results = response.json()["result"]
        return results

    def fetch_subaccounts(self, wallet=None):
        """
        Returns the subaccounts for a given wallet
        """
        url = f"{self.contracts['BASE_URL']}/private/get_subaccounts"
        payload = {"wallet": wallet if wallet else self.wallet.address}
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = json.loads(response.content)["result"]
        return results

    def fetch_subaccount(self, subaccount_id):
        """
        Returns information for a given subaccount
        """
        url = f"{self.contracts['BASE_URL']}/private/get_subaccount"
        payload = {"subaccount_id": self.subaccount_id}
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = response.json()["result"]
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
                return message['result']['order']

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
        ws = create_connection(self.contracts['WS_ADDRESS'])
        return ws

    def login_client(self, ws):
        login_request = json.dumps(
            {'method': 'public/login', 'params': self.sign_authentication_header(), 'id': str(int(time.time()))}
        )
        ws.send(login_request)
        time.sleep(1)

    def create_subaccount(
        self,
        amount,
        asset_name,
        currency="USDT",
        margin_type="SM",
    ):
        """
        Create a subaccount
        """
        url = f"{self.contracts['BASE_URL']}/private/create_subaccount"

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
        response = requests.post(url, json=payload, headers=PUBLIC_HEADERS)
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
            'subaccount_id': self.subaccount_id,
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
                self.contracts['ASSET_ADDRESS'],
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
        encoded_action_hash = eth_abi.encode(
            ['bytes32', 'uint256', 'uint256', 'address', 'bytes32', 'uint256', 'address', 'address'],
            [
                bytes.fromhex(self.contracts['ACTION_TYPEHASH'][2:]),
                order['subaccount_id'],
                order['nonce'],
                self.contracts['TRADE_MODULE_ADDRESS'],
                trade_module_data,
                order['signature_expiry_sec'],
                self.wallet.address,
                order['signer'],
            ],
        )

        action_hash = self.web3_client.keccak(encoded_action_hash)
        encoded_typed_data_hash = "".join(['0x1901', self.contracts['DOMAIN_SEPARATOR'][2:], action_hash.hex()[2:]])
        typed_data_hash = self.web3_client.keccak(hexstr=encoded_typed_data_hash)
        order['signature'] = self.wallet.signHash(typed_data_hash).signature.hex()
        return order

    def fetch_ticker(self, instrument_name):
        """
        Fetch the ticker for a given instrument name.
        """
        url = f"{self.contracts['BASE_URL']}/public/get_ticker"
        payload = {"instrument_name": instrument_name}
        response = requests.post(url, json=payload, headers=PUBLIC_HEADERS)
        results = json.loads(response.content)["result"]
        return results

    def fetch_orders(
        self,
        instrument_name: str = None,
        label: str = None,
        page: int = 1,
        page_size: int = 100,
        status: OrderStatus = None,
    ):
        """
        Fetch the orders for a given instrument name.
        """
        url = f"{self.contracts['BASE_URL']}/private/get_orders"
        payload = {"instrument_name": instrument_name, "subaccount_id": self.subaccount_id}
        for key, value in {"label": label, "page": page, "page_size": page_size, "status": status}.items():
            if value:
                payload[key] = value
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = response.json()["result"]['orders']
        return results

    def cancel(self, order_id, instrument_name):
        """
        Cancel an order
        """

        ws = self.connect_ws()
        self.login_client(ws)
        id = str(int(time.time()))
        payload = {"order_id": order_id, "subaccount_id": self.subaccount_id, "instrument_name": instrument_name}
        ws.send(json.dumps({'method': 'private/cancel', 'params': payload, 'id': id}))
        while True:
            message = json.loads(ws.recv())
            if message['id'] == id:
                return message['result']

    def cancel_all(self):
        """
        Cancel all orders
        """
        ws = self.connect_ws()
        self.login_client(ws)
        id = str(int(time.time()))
        payload = {"subaccount_id": self.subaccount_id}
        ws.send(json.dumps({'method': 'private/cancel_all', 'params': payload, 'id': id}))
        while True:
            message = json.loads(ws.recv())
            if message['id'] == id:
                return message['result']

    def get_positions(self):
        """
        Get positions
        """
        url = f"{self.contracts['BASE_URL']}/private/get_positions"
        payload = {"subaccount_id": self.subaccount_id}
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = response.json()["result"]['positions']
        return results
