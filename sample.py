import eth_abi
from datetime import datetime
from pprint import pprint
import json
import random
import time
from websocket import create_connection
from web3 import Web3
from eth_account.messages import encode_defunct

from tests.test_main import TEST_PRIVATE_KEY, TEST_WALLET

PRIVATE_KEY = TEST_PRIVATE_KEY
PROVIDER_URL = 'https://l2-prod-testnet-0eakp60405.t.conduit.xyz'
WS_ADDRESS = "wss://api-demo.lyra.finance/ws"
# old working addresses
ACTION_TYPEHASH = '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17'
DOMAIN_SEPARATOR = '0xff2ba7c8d1c63329d3c2c6c9c19113440c004c51fe6413f65654962afaff00f3'
# ASSET_ADDRESS = '0x8932cc48F7AD0c6c7974606cFD7bCeE2F543a124'
ASSET_ADDRESS = '0x62CF2Cc6450Dc3FbD0662Bfd69af0a4D7485Fe4E'
TRADE_MODULE_ADDRESS = '0x63Bc9D10f088eddc39A6c40Ff81E99516dfD5269'
# NEW addresses

ACTION_TYPEHASH = '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17'
DOMAIN_SEPARATOR = '0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105'
ASSET_ADDRESS = '0x6caf294DaC985ff653d5aE75b4FF8E0A66025928'
TRADE_MODULE_ADDRESS = '0x87F2863866D85E3192a35A73b388BD625D83f2be'

w3 = Web3(Web3.HTTPProvider(PROVIDER_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
subaccount_id = 550

OPTION_NAME = 'ETH-PERP'
OPTION_SUB_ID = '0'  # can retrieve with public/get_instrument


def sign_authentication_header():
    timestamp = str(int(time.time() * 1000))
    msg = encode_defunct(
        text=timestamp,
    )
    signature = w3.eth.account.sign_message(msg, private_key=PRIVATE_KEY).signature.hex()
    return {
        'wallet': account.address,
        'timestamp': str(timestamp),
        'signature': signature,
    }


def connect_ws():
    ws = create_connection(WS_ADDRESS)
    return ws


def login_client(ws):
    login_request = json.dumps({
        'method': 'public/login',
        'params': sign_authentication_header(),
        'id': str(int(time.time()))
    })
    ws.send(login_request)
    time.sleep(2)


def define_order():

    ts = int(datetime.now().timestamp() * 1000) 
    ts = 1698956141

    return {
        'instrument_name': OPTION_NAME,
        'subaccount_id': subaccount_id,
        'direction': 'buy',
        'limit_price': 1310,
        'amount': 100,
        'signature_expiry_sec': int(ts ) + 3000,
        'max_fee': '0.01',
        # 'nonce': int(f"{int(ts)}{random.randint(100, 999)}"),
        'nonce': int(f"{int(ts)}{997}"),
        'signer': account.address,
        'order_type': 'limit',
        'mmp': False,
        'signature': 'filled_in_below'
    }


def encode_trade_data(order):
    encoded_data = eth_abi.encode(['address', 'uint256', 'int256', 'int256', 'uint256', 'uint256', 'bool'],
                                     [ASSET_ADDRESS,
                                      int(OPTION_SUB_ID),
                                      w3.to_wei(order['limit_price'], 'ether'),
                                      w3.to_wei(order['amount'], 'ether'),
                                      w3.to_wei(order['max_fee'], 'ether'),
                                      order['subaccount_id'],
                                      order['direction'] == 'buy'])

    return w3.keccak(encoded_data)


def sign_order(order):
    trade_module_data = encode_trade_data(order)

    print('Signing Trade module data:', trade_module_data.hex())

    encoded_action_hash = eth_abi.encode(['bytes32', 'uint256', 'uint256', 'address', 'bytes32', 'uint256', 'address', 'address'],
                                    [bytes.fromhex(ACTION_TYPEHASH[2:]),
                                     order['subaccount_id'],
                                     order['nonce'],
                                     TRADE_MODULE_ADDRESS,
                                     trade_module_data,
                                     order['signature_expiry_sec'],
                                     account.address,
                                     order['signer']])

    action_hash = w3.keccak(encoded_action_hash)

    print('Signing Action hash:', action_hash.hex())


    encoded_typed_data_hash = "".join(['0x1901', DOMAIN_SEPARATOR[2:], action_hash.hex()[2:]])
                                        # [   bytes.fromhex('1901'),
                                        #     bytes.fromhex(DOMAIN_SEPARATOR[2:]),
                                        #     bytes.fromhex(action_hash.hex()[2:])
                                        # ])

    typed_data_hash = w3.keccak(hexstr=encoded_typed_data_hash)
    
    print('Typed data hash:', typed_data_hash.hex())

    msg = encode_defunct(
        text=typed_data_hash.hex(),
    )

    order['signature'] = account.signHash(typed_data_hash).signature.hex()
    return order


def submit_order(order, ws):
    id = str(int(time.time()))
    ws.send(json.dumps({
        'method': 'private/order',
        'params': order,
        'id': id
    }))

    pprint(order)

    while True:
        message = json.loads(ws.recv())
        if message['id'] == id:
            print('Got order response:', message)
            break


def complete_order():
    ws = connect_ws()
    login_client(ws)
    order = define_order()
    order = sign_order(order)
    submit_order(order, ws)


complete_order()
