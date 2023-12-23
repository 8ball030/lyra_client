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


def test_create_order(lyra_client):
    """
    Test the LyraClient class.
    """
    assert "error" not in lyra_client.create_order(
        price=200,
        amount=1,
        instrument_name="ETH-PERP",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
    )


def test_define_order(lyra_client):
    """
    Test the LyraClient class.
    """
