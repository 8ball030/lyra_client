"""
Tests for the main function.
"""
import pytest

from lyra.main import InstrumentType, LyraClient, UnderlyingCurrency, main

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
