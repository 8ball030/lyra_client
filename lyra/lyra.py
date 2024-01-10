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

# OPTION_NAME = 'ETH-PERP'
# OPTION_SUB_ID = '0'


def to_32byte_hex(val):
    return Web3.to_hex(Web3.to_bytes(val).rjust(32, b"\0"))


class LyraClient:
    """Client for the lyra dex."""

    def _create_signature_headers(
        self,
    ):
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

    def __init__(self, private_key, env, logger=None, verbose=False, subaccount_id=None, wallet=None):
        """
        Initialize the LyraClient class.
        """
        self.verbose = verbose
        self.env = env
        self.contracts = CONTRACTS[env]
        self.logger = logger or get_logger()
        self.web3_client = Web3()
        self.signer = self.web3_client.eth.account.from_key(private_key)
        self.wallet = self.signer.address if not wallet else wallet
        print(f"Signing address: {self.signer.address}")
        if wallet:
            print(f"Using wallet: {wallet}")
        if not subaccount_id:
            self.subaccount_id = self.fetch_subaccounts()['subaccount_ids'][0]
        else:
            self.subaccount_id = subaccount_id
        self.ws = self.connect_ws()
        self.login_client()

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
        response = requests.post(url, json=payload, headers=PUBLIC_HEADERS)
        results = response.json()["result"]
        return results

    def fetch_subaccounts(self):
        """
        Returns the subaccounts for a given wallet
        """
        url = f"{self.contracts['BASE_URL']}/private/get_subaccounts"
        payload = {"wallet": self.wallet}
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
        order = self._define_order(
            instrument_name=instrument_name,
            price=price,
            amount=amount,
            side=side,
        )
        _currency = UnderlyingCurrency[instrument_name.split("-")[0]]
        if instrument_name.split("-")[1] == "PERP":
            instruments = self.fetch_instruments(instrument_type=InstrumentType.PERP, currency=_currency)
            instruments = {i['instrument_name']: i for i in instruments}
            base_asset_sub_id = instruments[instrument_name]['base_asset_sub_id']
            instrument_type = InstrumentType.PERP
        else:
            instruments = self.fetch_instruments(instrument_type=InstrumentType.OPTION, currency=_currency)
            instruments = {i['instrument_name']: i for i in instruments}
            base_asset_sub_id = instruments[instrument_name]['base_asset_sub_id']
            instrument_type = InstrumentType.OPTION

        signed_order = self._sign_order(order, base_asset_sub_id, instrument_type, _currency)
        response = self.submit_order(signed_order)
        return response

    def _define_order(
        self,
        instrument_name: str,
        price: float,
        amount: float,
        side: OrderSide,
    ):
        """
        Define the order, in preparation for encoding and signing
        """
        ts = int(datetime.now().timestamp() * 1000)
        return {
            'instrument_name': instrument_name,
            'subaccount_id': self.subaccount_id,
            'direction': side.name.lower(),
            'limit_price': price,
            'amount': amount,
            'signature_expiry_sec': int(ts) + 3000,
            'max_fee': '200.01',
            'nonce': int(f"{int(ts)}{random.randint(100, 999)}"),
            'signer': self.signer.address,
            'order_type': 'limit',
            'mmp': False,
            'signature': 'filled_in_below',
        }

    def submit_order(self, order):
        id = str(int(time.time()))
        self.ws.send(json.dumps({'method': 'private/order', 'params': order, 'id': id}))
        while True:
            message = json.loads(self.ws.recv())
            if message['id'] == id:
                try:
                    return message['result']['order']
                except KeyError as error:
                    raise Exception(f"Unable to submit order {message}") from error

    def sign_authentication_header(self):
        timestamp = str(int(time.time() * 1000))
        msg = encode_defunct(
            text=timestamp,
        )
        signature = self.web3_client.eth.account.sign_message(
            msg, private_key=self.signer._private_key
        ).signature.hex()  # pylint: disable=protected-access
        return {
            'wallet': self.wallet,
            'timestamp': str(timestamp),
            'signature': signature,
        }

    def connect_ws(self):
        ws = create_connection(self.contracts['WS_ADDRESS'])
        return ws

    def login_client(
        self,
    ):
        login_request = {
            'method': 'public/login',
            'params': self.sign_authentication_header(),
            'id': str(int(time.time())),
        }
        self.ws.send(json.dumps(login_request))
        # we need to wait for the response
        while True:
            message = json.loads(self.ws.recv())
            if message['id'] == login_request['id']:
                if "result" not in message:
                    raise Exception(f"Unable to login {message}")
                break

    def create_subaccount(
        self,
        asset_name="USDC",
        amount=0,
    ):
        """
        Create a subaccount
        """
        url = f"{self.contracts['BASE_URL']}/private/create_subaccount"
        ts = int(datetime.now().timestamp() * 1000)
        payload = {
            "amount": f"{amount}",
            "asset_name": f"{asset_name}",
            "margin_type": "SM",
            'nonce': int(f"{int(ts)}{random.randint(100, 999)}"),
            "signature": "string",
            "signature_expiry_sec": int(ts) + 3000,
            "signer": self.wallet.address,
            "wallet": self.wallet.address,
        }
        print(payload)
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        print(response.text)

    def _encode_trade_data(self, order, base_asset_sub_id, instrument_type, currency):
        encoded_data = eth_abi.encode(
            ['address', 'uint256', 'int256', 'int256', 'uint256', 'uint256', 'bool'],
            [
                self.contracts[f'{currency.name}_{instrument_type.name}_ADDRESS'],
                int(base_asset_sub_id),
                self.web3_client.to_wei(order['limit_price'], 'ether'),
                self.web3_client.to_wei(order['amount'], 'ether'),
                self.web3_client.to_wei(order['max_fee'], 'ether'),
                order['subaccount_id'],
                order['direction'] == 'buy',
            ],
        )

        return self.web3_client.keccak(encoded_data)

    def _sign_order(self, order, base_asset_sub_id, instrument_type, currency):
        trade_module_data = self._encode_trade_data(order, base_asset_sub_id, instrument_type, currency)
        encoded_action_hash = eth_abi.encode(
            ['bytes32', 'uint256', 'uint256', 'address', 'bytes32', 'uint256', 'address', 'address'],
            [
                bytes.fromhex(self.contracts['ACTION_TYPEHASH'][2:]),
                order['subaccount_id'],
                order['nonce'],
                self.contracts['TRADE_MODULE_ADDRESS'],
                trade_module_data,
                order['signature_expiry_sec'],
                self.wallet,
                order['signer'],
            ],
        )

        action_hash = self.web3_client.keccak(encoded_action_hash)
        encoded_typed_data_hash = "".join(['0x1901', self.contracts['DOMAIN_SEPARATOR'][2:], action_hash.hex()[2:]])
        typed_data_hash = self.web3_client.keccak(hexstr=encoded_typed_data_hash)
        order['signature'] = self.signer.signHash(typed_data_hash).signature.hex()
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

        id = str(int(time.time()))
        payload = {"order_id": order_id, "subaccount_id": self.subaccount_id, "instrument_name": instrument_name}
        self.ws.send(json.dumps({'method': 'private/cancel', 'params': payload, 'id': id}))
        while True:
            message = json.loads(self.ws.recv())
            if message['id'] == id:
                return message['result']

    def cancel_all(self):
        """
        Cancel all orders
        """
        id = str(int(time.time()))
        payload = {"subaccount_id": self.subaccount_id}
        self.ws.send(json.dumps({'method': 'private/cancel_all', 'params': payload, 'id': id}))
        while True:
            message = json.loads(self.ws.recv())
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

    def get_collaterals(self):
        """
        Get collaterals
        """
        url = f"{self.contracts['BASE_URL']}/private/get_collaterals"
        payload = {"subaccount_id": self.subaccount_id}
        headers = self._create_signature_headers()
        response = requests.post(url, json=payload, headers=headers)
        results = response.json()["result"]['collaterals']
        return results.pop()

    def fetch_tickers(
        self,
        instrument_type: InstrumentType = InstrumentType.OPTION,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        """
        Fetch tickers using the ws connection
        """
        instruments = self.fetch_instruments(instrument_type=instrument_type, currency=currency)
        instrument_names = [i['instrument_name'] for i in instruments]
        id_base = str(int(time.time()))
        ids_to_instrument_names = {
            f'{id_base}_{enumerate}': instrument_name for enumerate, instrument_name in enumerate(instrument_names)
        }
        for id, instrument_name in ids_to_instrument_names.items():
            payload = {"instrument_name": instrument_name}
            self.ws.send(json.dumps({'method': 'public/get_ticker', 'params': payload, 'id': id}))
            time.sleep(0.05)  # otherwise we get rate limited...
        results = {}
        while ids_to_instrument_names:
            message = json.loads(self.ws.recv())
            if message['id'] in ids_to_instrument_names:
                results[message['result']['instrument_name']] = message['result']
                del ids_to_instrument_names[message['id']]
        return results
