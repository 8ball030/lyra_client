"""
Tests for the main function.
"""
from itertools import product
from unittest.mock import MagicMock

import pytest

from lyra.enums import (
    CollateralAsset,
    Environment,
    InstrumentType,
    OrderSide,
    OrderType,
    SubaccountType,
    UnderlyingCurrency,
)
from lyra.lyra import LyraClient
from lyra.utils import get_logger

TEST_WALLET = "0x3A5c777edf22107d7FdFB3B02B0Cdfe8b75f3453"
TEST_PRIVATE_KEY = "0xc14f53ee466dd3fc5fa356897ab276acbef4f020486ec253a23b0d1c3f89d4f4"


def freeze_time(lyra_client):
    ts = 1705439697008
    nonce = 17054396970088651
    expiration = 1705439703008
    lyra_client.get_nonce_and_signature_expiry = MagicMock(return_value=(ts, nonce, expiration))
    return lyra_client


@pytest.fixture
def lyra_client():
    return LyraClient(TEST_PRIVATE_KEY, env=Environment.TEST, logger=get_logger())


def test_lyra_client(lyra_client):
    """
    Test the LyraClient class.
    """
    assert lyra_client.create_account(TEST_WALLET)


@pytest.mark.parametrize(
    "instrument_type, currency",
    product(
        [InstrumentType.PERP, InstrumentType.OPTION],
        [UnderlyingCurrency.BTC],
    ),
)
def test_lyra_client_fetch_instruments(lyra_client, instrument_type, currency):
    """
    Test the LyraClient class.
    """
    assert lyra_client.fetch_instruments(instrument_type=instrument_type, currency=currency)


def test_create_signature_headers(lyra_client):
    """
    Test the LyraClient class.
    """
    assert lyra_client._create_signature_headers()


def test_fetch_subaccounts(lyra_client):
    """
    Test the LyraClient class.
    """
    accounts = lyra_client.fetch_subaccounts()
    assert accounts['subaccount_ids']


def test_fetch_subaccount(lyra_client):
    """
    Show we can fetch a subaccount.
    """
    subaccount_id = lyra_client.fetch_subaccounts()['subaccount_ids'][0]
    subaccount = lyra_client.fetch_subaccount(subaccount_id)
    assert subaccount['subaccount_id'] == subaccount_id


@pytest.mark.skip()
def test_create_pm_subaccount(lyra_client):
    """
    Test the LyraClient class.
    """
    # freeze_time(lyra_client)
    collateral_asset = CollateralAsset.USDC
    underlying_currency = UnderlyingCurrency.ETH
    subaccount_id = lyra_client.create_subaccount(
        subaccount_type=SubaccountType.PORTFOLIO,
        collateral_asset=collateral_asset,
        underlying_currency=underlying_currency,
    )
    assert subaccount_id


@pytest.mark.parametrize(
    "instrument_name, side, price",
    [
        ("ETH-PERP", OrderSide.BUY, 200),
        ("ETH-PERP", OrderSide.SELL, 10000),
        ("BTC-PERP", OrderSide.BUY, 2000),
        ("BTC-PERP", OrderSide.SELL, 100000),
    ],
)
def test_create_order(lyra_client, instrument_name, side, price):
    """
    Test the LyraClient class.
    """
    result = lyra_client.create_order(
        price=price,
        amount=1,
        instrument_name=instrument_name,
        side=OrderSide(side),
        order_type=OrderType.LIMIT,
    )
    assert "error" not in result
    order_price = float(result['limit_price'])
    order_side = result['direction']
    assert order_price == price
    assert order_side == side.value


def test_fetch_ticker(lyra_client):
    """
    Test the LyraClient class.
    """
    instruments = lyra_client.fetch_instruments(instrument_type=InstrumentType.PERP)
    instrument_name = instruments[0]['instrument_name']
    ticker = lyra_client.fetch_ticker(instrument_name=instrument_name)
    assert ticker['instrument_name'] == instrument_name


def test_fetch_option_tickers(lyra_client):
    """
    Test the LyraClient class.
    """
    instruments = lyra_client.fetch_instruments(instrument_type=InstrumentType.OPTION, expired=False)
    instrument_name = instruments[0]['instrument_name']
    ticker = lyra_client.fetch_ticker(instrument_name=instrument_name)
    assert ticker['instrument_name'] == instrument_name


def test_fetch_first_subaccount(lyra_client):
    """
    Test the LyraClient class.
    """
    subaccount_id = lyra_client.fetch_subaccounts()['subaccount_ids'][0]
    subaccount = lyra_client.fetch_subaccount(subaccount_id)
    assert subaccount['subaccount_id'] == subaccount_id


def test_fetch_orders(lyra_client):
    """
    Test the LyraClient class.
    """
    orders = lyra_client.fetch_orders()
    assert orders


def test_cancel_order(lyra_client):
    """
    Test the LyraClient class.
    """
    order = lyra_client.create_order(
        price=200,
        amount=1,
        instrument_name="ETH-PERP",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
    )
    order_id = order['order_id']
    result = lyra_client.cancel(instrument_name="ETH-PERP", order_id=order_id)
    assert result['order_id'] == order_id


def test_cancel_all_orders(lyra_client):
    """Test all open orders are cancelled."""
    lyra_client.create_order(
        price=200,
        amount=1,
        instrument_name="ETH-PERP",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
    )
    open_orders = lyra_client.fetch_orders(status="open")
    assert open_orders
    lyra_client.cancel_all()
    open_orders = lyra_client.fetch_orders(status="open")
    assert not open_orders


def test_get_positions(lyra_client):
    """Test get positions."""
    positions = lyra_client.get_positions()
    assert isinstance(positions, list)


def test_get_collaterals(lyra_client):
    """Test get collaterals."""
    collaterals = lyra_client.get_collaterals()
    assert isinstance(collaterals, dict)


def test_get_tickers(lyra_client):
    """Test get tickers."""
    tickers = lyra_client.fetch_tickers()
    assert isinstance(tickers, dict)


@pytest.mark.parametrize(
    "currency, side",
    [
        (UnderlyingCurrency.ETH, OrderSide.BUY),
        (UnderlyingCurrency.ETH, OrderSide.SELL),
        (UnderlyingCurrency.BTC, OrderSide.BUY),
        (UnderlyingCurrency.BTC, OrderSide.SELL),
    ],
)
def test_can_create_option_order(lyra_client, currency, side):
    """Test can create option order."""
    tickers = lyra_client.fetch_tickers(
        instrument_type=InstrumentType.OPTION,
        currency=currency,
    )
    symbol, ticker = [f for f in tickers.items()][0]
    if side == OrderSide.BUY:
        order_price = ticker['min_price']
    else:
        order_price = ticker['max_price']
    order = lyra_client.create_order(
        price=order_price,
        amount=1,
        instrument_name=symbol,
        side=side,
        order_type=OrderType.LIMIT,
    )
    assert order


@pytest.mark.parametrize(
    "subaccount_type,underlying_currency,result",
    [
        (
            SubaccountType.STANDARD,
            None,
            (
                "0x247da26f2c790be0f0838efa1403703863af35a74c439665dca40a4491bd8c2f",
                "0x68031dbf2804c2c5c848de876db4cc334c69267ed7ff49646fbbd9d2aff16f71",
                "0x9abed503592450a03d53af21e2693d60e08a69506c6a61d219da071c5a1a1de5",
            ),
        ),
        (
            SubaccountType.PORTFOLIO,
            UnderlyingCurrency.ETH,
            (
                "0xaf75590c7dde08338ed8f52c718140000bdee1476232b1321e694807d739aa74",
                "0x2c83609b60aec89e15520b340369a8d48257a83c95e18b751ac41b27fd3f7d7c",
                "0x6ae341bd695b518b7d7ade71bb9a3157cabc15847af7c70d0152a28f9c7dab2e",
            ),
        ),
    ],
)
def test_generate_necessary_data(lyra_client, subaccount_type, underlying_currency, result):
    freeze_time(lyra_client)
    collateral_asset = CollateralAsset.USDC
    subaccount_id = 0
    _, nonce, expiration = lyra_client.get_nonce_and_signature_expiry()
    if subaccount_type is SubaccountType.STANDARD:
        contract_key = f"{subaccount_type.name}_RISK_MANAGER_ADDRESS"
    elif subaccount_type is SubaccountType.PORTFOLIO:
        if not collateral_asset:
            raise Exception("Underlying currency must be provided for portfolio subaccounts")
        contract_key = f"{underlying_currency.name}_{subaccount_type.name}_RISK_MANAGER_ADDRESS"
    deposit_data = lyra_client._encode_deposit_data(
        amount=0.0,
        contract_key=contract_key,
    )
    assert deposit_data.hex() == result[0]

    action_hash = lyra_client._generate_action_hash(
        subaccount_id=subaccount_id,
        encoded_deposit_data=deposit_data,
        expiration=expiration,
        nonce=nonce,
    )
    assert action_hash.hex() == result[1]

    typed_data_hash = lyra_client._generate_typed_data_hash(
        action_hash=action_hash,
    )
    assert typed_data_hash.hex() == result[2]


def test_get_nonce_and_signature_expiration(lyra_client):
    """Test get nonce and signature."""

    ts, nonce, expiration = lyra_client.get_nonce_and_signature_expiry()
    assert ts
    assert nonce
    assert expiration


@pytest.mark.skip()
def test_transfer_collateral(lyra_client):
    """Test transfer collateral."""
    # freeze_time(lyra_client)
    amount = 1
    to = lyra_client.fetch_subaccounts()['subaccount_ids'][1]
    asset = CollateralAsset.USDC
    result = lyra_client.transfer_collateral(amount, to, asset)

    assert result
