"""
Constants for Lyra.
"""
from lyra.enums import Environment

PUBLIC_HEADERS = {"accept": "application/json", "content-type": "application/json"}


CONTRACTS = {
    Environment.TEST: {
        "BASE_URL": "https://api-demo.lyra.finance",
        "WS_ADDRESS": "wss://api-demo.lyra.finance/ws",
        "ACTION_TYPEHASH": '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17',
        "DOMAIN_SEPARATOR": '0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105',
        "ETH_PERP_ADDRESS": '0x010e26422790C6Cb3872330980FAa7628FD20294',
        "BTC_PERP_ADDRESS": '0xAFB6Bb95cd70D5367e2C39e9dbEb422B9815339D',
        "TRADE_MODULE_ADDRESS": '0x87F2863866D85E3192a35A73b388BD625D83f2be',
    },
    Environment.PROD: {
        "BASE_URL": "https://api.lyra.finance",
        "WS_ADDRESS": "wss://api.lyra.finance/ws",
    },
}
