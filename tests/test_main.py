"""
Tests for the main function.
"""
import pytest
import time
import itertools
from lyra.main import InstrumentType, LyraClient, OrderSide, OrderType, UnderlyingCurrency, main

TEST_WALLET = "0x3A5c777edf22107d7FdFB3B02B0Cdfe8b75f3453"
TEST_PRIVATE_KEY = "0xc14f53ee466dd3fc5fa356897ab276acbef4f020486ec253a23b0d1c3f89d4f4"


def test_main():
    """
    Test the main function.
    """
    main()


@pytest.fixture
def lyra_client():
    return LyraClient(TEST_PRIVATE_KEY)


def test_lyra_client(lyra_client):
    """
    Test the LyraClient class.
    """
    assert lyra_client.create_account(TEST_WALLET)


def test_lyra_client_fetch_tickers(lyra_client):
    """
    Test the LyraClient class.
    """
    assert lyra_client.fetch_tickers(instrument_type=InstrumentType.PERP.value, currency=UnderlyingCurrency.ETH.value)


def test_create_signature_headers(lyra_client):
    """
    Test the LyraClient class.
    """
    assert lyra_client._create_signature_headers()


def test_fetch_subaccounts(lyra_client):
    """
    Test the LyraClient class.
    """
    assert lyra_client.fetch_subaccounts(TEST_WALLET)


def test_build_register_session_key_tx(lyra_client):
    """Test build_register_session_key_tx"""

    expiry_sec = str(int(time.time() * 1000) + 1000)
    tx = lyra_client.build_register_session_key_tx(expiry_sec)
    assert tx["tx_params"]


def test_register_session_key(lyra_client):
    """Test build_register_session_key_tx"""

    expiry_sec = str(int(time.time() * 1000) + 1000)
    tx = lyra_client.build_register_session_key_tx(expiry_sec)
    tx_receipt = lyra_client.register_session_key(tx["tx_params"], expiry_sec)
    assert tx_receipt["transaction_id"]


@pytest.mark.parametrize(
    "currency, expired, instrument_type",
    itertools.product(UnderlyingCurrency, [True, False], InstrumentType)
)
def test_get_instruments(lyra_client, currency, expired, instrument_type):
    """Test get_instruments"""

    instruments = lyra_client.get_instruments(currency, expired, instrument_type)
    assert instruments


def test_create_order(lyra_client):
    """
    Test the LyraClient class.
    """
    assert lyra_client.create_order(
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
