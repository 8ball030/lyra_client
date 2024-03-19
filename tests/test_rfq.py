"""
Implement tests for the RFQ class.
"""


from dataclasses import asdict, dataclass

from lyra.enums import OrderSide

LEG_1_NAME = 'ETH-20240329-2400-C'
LEG_2_NAME = 'ETH-20240329-2600-C'

LEGS_TO_SUB_ID: any = {
    'ETH-20240329-2400-C': '39614082287924319838483674368',
    'ETH-20240329-2600-C': '39614082373823665758483674368',
}


@dataclass
class Leg:
    instrument_name: str
    amount: str
    direction: str


@dataclass
class Rfq:
    subaccount_id: str
    leg_1: Leg
    leg_2: Leg

    def to_dict(self):
        return {"legs": [asdict(self.leg_1), asdict(self.leg_2)], "subaccount_id": self.subaccount_id}


def test_lyra_client_create_rfq(
    lyra_client,
):
    """
    Test the LyraClient class.
    """

    subaccount_id = lyra_client.subaccount_id
    leg_1 = Leg(instrument_name=LEG_1_NAME, amount='1', direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=LEG_2_NAME, amount='1', direction=OrderSide.SELL.value)
    rfq = Rfq(leg_1=leg_1, leg_2=leg_2, subaccount_id=subaccount_id)
    assert lyra_client.send_rfq(rfq.to_dict())


def test_lyra_client_create_quote(
    lyra_client,
):
    """
    Test the LyraClient class.
    """

    subaccount_id = lyra_client.subaccount_id
    leg_1 = Leg(instrument_name=LEG_1_NAME, amount='1', direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=LEG_2_NAME, amount='1', direction=OrderSide.SELL.value)
    rfq = Rfq(leg_1=leg_1, leg_2=leg_2, subaccount_id=subaccount_id)
    res = lyra_client.send_rfq(rfq.to_dict())

    # we now create the quote
    quote = lyra_client.create_quote_object(
        rfq_id=res['rfq_id'],
        legs=[asdict(leg_1), asdict(leg_2)],
        direction='sell',
    )
    # we now sign it
    assert lyra_client._sign_quote(quote)
    breakpoint()


def test_poll_rfqs(lyra_client):
    """
    Test the LyraClient class.
    """
    subaccount_id = lyra_client.subaccount_id
    leg_1 = Leg(instrument_name=LEG_1_NAME, amount='1', direction=OrderSide.BUY.value)
    leg_2 = Leg(instrument_name=LEG_2_NAME, amount='1', direction=OrderSide.SELL.value)
    rfq = Rfq(leg_1=leg_1, leg_2=leg_2, subaccount_id=subaccount_id)
    assert lyra_client.send_rfq(rfq.to_dict())
    quotes = lyra_client.poll_rfqs()
    assert quotes
