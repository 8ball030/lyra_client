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
        "ETH_OPTION_ADDRESS": '0xBcB494059969DAaB460E0B5d4f5c2366aab79aa1',
        "BTC_OPTION_ADDRESS": '0xAeB81cbe6b19CeEB0dBE0d230CFFE35Bb40a13a7',
        "TRADE_MODULE_ADDRESS": '0x87F2863866D85E3192a35A73b388BD625D83f2be',
    },
    Environment.PROD: {
        "BASE_URL": "https://api.lyra.finance",
        "WS_ADDRESS": "wss://api.lyra.finance/ws",
        "ACTION_TYPEHASH": '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17',
        "DOMAIN_SEPARATOR": '0xd96e5f90797da7ec8dc4e276260c7f3f87fedf68775fbe1ef116e996fc60441b',
        "ETH_PERP_ADDRESS": '0xAf65752C4643E25C02F693f9D4FE19cF23a095E3',
        "BTC_PERP_ADDRESS": '0xDBa83C0C654DB1cd914FA2710bA743e925B53086',
        "ETH_OPTION_ADDRESS": '0x4BB4C3CDc7562f08e9910A0C7D8bB7e108861eB4',
        "BTC_OPTION_ADDRESS": '0xd0711b9eBE84b778483709CDe62BacFDBAE13623',
        "TRADE_MODULE_ADDRESS": '0xB8D20c2B7a1Ad2EE33Bc50eF10876eD3035b5e7b',
    },
}
