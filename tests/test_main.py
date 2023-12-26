"""
Tests for the main function.
"""
from itertools import product

import pytest

from lyra.enums import Environment, InstrumentType, OrderSide, OrderType, UnderlyingCurrency
from lyra.lyra import LyraClient
from lyra.utils import get_logger

TEST_WALLET = "0x3A5c777edf22107d7FdFB3B02B0Cdfe8b75f3453"
TEST_PRIVATE_KEY = "0xc14f53ee466dd3fc5fa356897ab276acbef4f020486ec253a23b0d1c3f89d4f4"


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
    accounts = lyra_client.fetch_subaccounts(TEST_WALLET)
    assert accounts['subaccount_ids']


def test_create_subaccount(lyra_client):
    """
    Test the LyraClient class.
    """
    subaccount_id = lyra_client.create_subaccount()
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


def test_fetch_subaccount(lyra_client):
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
