"""
Async client for Lyra
"""

import asyncio
import json
import time
from datetime import datetime

import aiohttp
from web3 import Web3

from lyra.constants import CONTRACTS, TEST_PRIVATE_KEY
from lyra.enums import Environment, InstrumentType, OrderSide, OrderType, TimeInForce, UnderlyingCurrency
from lyra.utils import get_logger
from lyra.ws_client import WsClient as BaseClient


class AsyncClient(BaseClient):
    """
    We use the async client to make async requests to the lyra API
    We us the ws client to make async requests to the lyra ws API
    """

    current_subscriptions = {}

    listener = None
    subscribing = False
    _ws = None

    def __init__(
        self,
        private_key: str = TEST_PRIVATE_KEY,
        env: Environment = Environment.TEST,
        logger=None,
        verbose=False,
        subaccount_id=None,
        wallet=None,
    ):
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
        self.subaccount_id = subaccount_id
        print(f"Using subaccount id: {self.subaccount_id}")
        self.message_queues = {}
        self.connecting = False
        # we make sure to get the event loop

    @property
    async def ws(self):
        if self._ws is None:
            self._ws = await self.connect_ws()
        if not self._ws.connected:
            self._ws = await self.connect_ws()
        return self._ws

    async def fetch_ticker(self, instrument_name: str):
        """
        Fetch the ticker for a symbol
        """
        id = str(int(time.time()))
        payload = {"instrument_name": instrument_name}
        if not self.ws:
            await self.connect_ws()

        self.ws.send(json.dumps({"method": "public/get_ticker", "params": payload, "id": id}))

        # we now wait for the response
        while True:
            response = self.ws.recv()
            response = json.loads(response)
            if response["id"] == id:
                close = float(response["result"]["best_bid_price"]) + float(response["result"]["best_ask_price"]) / 2
                response["result"]["close"] = close
                return response["result"]

    def get_subscription_id(self, instrument_name: str, group: str = "1", depth: str = "100"):
        return f"orderbook.{instrument_name}.{group}.{depth}"

    async def subscribe(self, instrument_name: str, group: str = "1", depth: str = "100"):
        """
        Subscribe to the order book for a symbol
        """
        # if self.listener is None or self.listener.done():
        asyncio.create_task(self.listen_for_messages())
        channel = self.get_subscription_id(instrument_name, group, depth)
        if channel not in self.message_queues:
            self.message_queues[channel] = asyncio.Queue()
            msg = {"method": "subscribe", "params": {"channels": [channel]}}
            await self.ws.send_json(msg)
            return

        while instrument_name not in self.current_subscriptions:
            await asyncio.sleep(0.01)
        return self.current_subscriptions[instrument_name]

    async def connect_ws(self):
        self.connecting = True
        session = aiohttp.ClientSession()
        ws = await session.ws_connect(self.contracts['WS_ADDRESS'])
        self._ws = ws
        self.connecting = False
        return ws

    async def listen_for_messages(
        self,
    ):
        while True:
            try:
                msg = await self.ws.receive_json()
            except TypeError:
                continue
            if "error" in msg:
                print(msg)
                raise Exception(msg["error"])
            if "result" in msg:
                result = msg["result"]
                if "status" in result:
                    # print(f"Succesfully subscribed to {result['status']}")
                    for channel, value in result['status'].items():
                        # print(f"Channel {channel} has value {value}")
                        if "error" in value:
                            raise Exception(f"Subscription error for channel: {channel} error: {value['error']}")
                    continue
            #  default to putting the message in the queue
            subscription = msg['params']['channel']
            data = msg['params']['data']
            self.handle_message(subscription, data)

    async def login_client(
        self,
    ):
        login_request = {
            'method': 'public/login',
            'params': self.sign_authentication_header(),
            'id': str(int(time.time())),
        }
        await self._ws.send_json(login_request)
        async for data in self._ws:
            message = json.loads(data.data)
            if message['id'] == login_request['id']:
                if "result" not in message:
                    raise Exception(f"Unable to login {message}")
                break

    def handle_message(self, subscription, data):
        bids = data['bids']
        asks = data['asks']

        bids = list(map(lambda x: (float(x[0]), float(x[1])), bids))
        asks = list(map(lambda x: (float(x[0]), float(x[1])), asks))

        instrument_name = subscription.split(".")[1]

        if subscription in self.current_subscriptions:
            old_params = self.current_subscriptions[subscription]
            _asks, _bids = old_params["asks"], old_params["bids"]
            if not asks:
                asks = _asks
            if not bids:
                bids = _bids
        timestamp = data['timestamp']
        datetime_str = datetime.fromtimestamp(timestamp / 1000)
        nonce = data['publish_id']
        self.current_subscriptions[instrument_name] = {
            "asks": asks,
            "bids": bids,
            "timestamp": timestamp,
            "datetime": datetime_str.isoformat(),
            "nonce": nonce,
            "symbol": instrument_name,
        }
        return self.current_subscriptions[instrument_name]

    async def watch_order_book(self, instrument_name: str, group: str = "1", depth: str = "100"):
        """
        Watch the order book for a symbol
        orderbook.{instrument_name}.{group}.{depth}
        """

        if not self.ws and not self.connecting:
            await self.connect_ws()
            await self.login_client()

        subscription = self.get_subscription_id(instrument_name, group, depth)

        if subscription not in self.message_queues:
            while any([self.subscribing, self.ws is None, self.connecting]):
                await asyncio.sleep(1)
            await self.subscribe(instrument_name, group, depth)

        while instrument_name not in self.current_subscriptions and not self.connecting:
            await asyncio.sleep(0.01)

        return self.current_subscriptions[instrument_name]

    async def fetch_instruments(
        self,
        expired=False,
        instrument_type: InstrumentType = InstrumentType.PERP,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        return super().fetch_instruments(expired, instrument_type, currency)

    async def close(self):
        """
        Close the connection
        """
        self.ws.close()

    async def fetch_tickers(
        self,
        instrument_type: InstrumentType = InstrumentType.OPTION,
        currency: UnderlyingCurrency = UnderlyingCurrency.BTC,
    ):
        if not self._ws:
            await self.connect_ws()
        instruments = await self.fetch_instruments(instrument_type=instrument_type, currency=currency)
        instrument_names = [i['instrument_name'] for i in instruments]
        id_base = str(int(time.time()))
        ids_to_instrument_names = {
            f'{id_base}_{enumerate}': instrument_name for enumerate, instrument_name in enumerate(instrument_names)
        }
        for id, instrument_name in ids_to_instrument_names.items():
            payload = {"instrument_name": instrument_name}
            await self._ws.send_json({'method': 'public/get_ticker', 'params': payload, 'id': id})
            await asyncio.sleep(0.1)  # otherwise we get rate limited...
        results = {}
        while ids_to_instrument_names:
            message = await self._ws.receive()
            if message is None:
                continue
            if 'error' in message:
                raise Exception(f"Error fetching ticker {message}")
            if message.type == aiohttp.WSMsgType.CLOSED:
                # we try to reconnect
                print(f"Erorr fetching ticker {message}...")
                self._ws = await self.connect_ws()
                return await self.fetch_tickers(instrument_type, currency)
            message = json.loads(message.data)
            if message['id'] in ids_to_instrument_names:
                try:
                    results[message['result']['instrument_name']] = message['result']
                except KeyError:
                    print(f"Error fetching ticker {message}")
                del ids_to_instrument_names[message['id']]
        return results

    async def get_collaterals(self):
        return super().get_collaterals()

    async def get_positions(self, currency: UnderlyingCurrency = UnderlyingCurrency.BTC):
        return super().get_positions()

    async def get_open_orders(self, status, currency: UnderlyingCurrency = UnderlyingCurrency.BTC):
        return super().fetch_orders(
            status=status,
        )

    async def create_order(
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
            instruments = await self.fetch_instruments(instrument_type=InstrumentType.PERP, currency=_currency)
            instruments = {i['instrument_name']: i for i in instruments}
            base_asset_sub_id = instruments[instrument_name]['base_asset_sub_id']
            instrument_type = InstrumentType.PERP
        else:
            instruments = await self.fetch_instruments(instrument_type=InstrumentType.OPTION, currency=_currency)
            instruments = {i['instrument_name']: i for i in instruments}
            base_asset_sub_id = instruments[instrument_name]['base_asset_sub_id']
            instrument_type = InstrumentType.OPTION

        signed_order = self._sign_order(order, base_asset_sub_id, instrument_type, _currency)
        response = self.submit_order(signed_order)
        return response
