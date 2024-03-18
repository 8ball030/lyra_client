"""
Async client for Lyra
"""

import asyncio
import json
import sys
import time
import traceback

from lyra.constants import PUBLIC_HEADERS
from lyra.enums import InstrumentType, UnderlyingCurrency
from lyra.ws_client import WsClient as BaseClient

from multiprocessing import Process
# we need a thread safe way to collect the events
from multiprocessing import Lock
from threading import Thread


class AsyncClient(BaseClient):
    """
    We use the async client to make async requests to the lyra API
    We us the ws client to make async requests to the lyra ws API
    """

    current_subscriptions = {}

    listener = None
    subscribing = False



    async def fetch_ticker(self, instrument_name: str):
        """
        Fetch the ticker for a symbol
        """
        id = str(int(time.time()))
        payload = {"instrument_name": instrument_name}
        self.ws.send(json.dumps({"method": "public/get_ticker", "params": payload, "id": id}))

        # we now wait for the response
        while True:
            response = self.ws.recv()
            response = json.loads(response)
            if response["id"] == id:
                close = float(response["result"]["best_bid_price"])  + float(response["result"]["best_ask_price"]) / 2
                response["result"]["close"] = close
                return response["result"]
            



    async def subscribe(self, instrument_name: str, group: str = "1", depth: str = "100"):
        """
        Subscribe to the order book for a symbol
        """

        self.subscribing = True
        if instrument_name not in self.current_subscriptions:
            channel = f"orderbook.{instrument_name}.{group}.{depth}"
            msg = json.dumps({
                "method": "subscribe", 
                "params": {
                    "channels": [channel]
                }

                })
            print(f"Subscribing with {msg}")
            self.ws.send(msg)
            await self.collect_events(instrument_name=instrument_name)
            print(f"Subscribed to {instrument_name}")
            return
        
        while instrument_name not in self.current_subscriptions:
            await asyncio.sleep(1)
        return self.current_subscriptions[instrument_name]
        
    

    async def collect_events(self, subscription: str = None, instrument_name: str = None):
        """Use a thread to check the subscriptions"""
        try:
            response = self.ws.recv()
            response = json.loads(response)
            if "error" in response:
                print(response)
                raise Exception(response["error"])
            if "result" in response:
                result = response["result"]
                if "status" in result:
                    print(f"Succesfully subscribed to {result['status']}")
                    for channel, value in result['status'].items():
                        print(f"Channel {channel} has value {value}")
                        if "error" in value:
                            raise Exception(value["error"])
                    self.subscribing = False
                    return


            channel = response["params"]["channel"]

            bids = response['params']['data']['bids']
            asks = response['params']['data']['asks']

            bids = list(map(lambda x: (float(x[0]), float(x[1])), bids))
            asks = list(map(lambda x: (float(x[0]), float(x[1])), asks))

            if instrument_name in self.current_subscriptions:
                old_params = self.current_subscriptions[instrument_name]
                _asks, _bids = old_params["asks"], old_params["bids"]
                if not asks:
                    asks = _asks
                if not bids:
                    bids = _bids
            self.current_subscriptions[instrument_name] = {"asks": asks, "bids": bids}
            return self.current_subscriptions[instrument_name]
        except Exception as e:
            print(f"Error: {e}")
            print(traceback.print_exc())
            sys.exit(1)

    async def watch_order_book(self, instrument_name: str, group: str = "1", depth: str = "100"):
        """
        Watch the order book for a symbol
        orderbook.{instrument_name}.{group}.{depth}
        """
        
        if not self.subscribing:
            await self.subscribe(instrument_name, group, depth)


        if not self.listener:
            print(f"Started listener for {instrument_name}")
            self.listener = True

        await self.collect_events(instrument_name=instrument_name)
        while instrument_name not in self.current_subscriptions:
            await asyncio.sleep(1)
            print(f"Waiting for {instrument_name} to be in current subscriptions")

        return self.current_subscriptions[instrument_name]

    
    async def fetch_instruments(self, expired=False, instrument_type: InstrumentType = InstrumentType.PERP, currency: UnderlyingCurrency = UnderlyingCurrency.BTC):
        return super().fetch_instruments(expired, instrument_type, currency)

    async def close(self):
        """
        Close the connection
        """
        self.ws.close()
        # if self.listener:
        #     self.listener.join()