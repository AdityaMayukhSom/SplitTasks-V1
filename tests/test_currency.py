from fastapi.testclient import TestClient
from sqlmodel import Session

from app.repository.models import Currency


def test_currency_show_in_ui():
    currency_gbp = Currency(code="GBP", name="Great Britain Pound", country="United Kingdom")
    assert currency_gbp.show_in_ui is False

    currency_iqd = Currency(code="IQD", name="Iraqi Dinar", country="Iraq", show_in_ui=True)
    assert currency_iqd.show_in_ui is True


def test_get_currencies(client: TestClient, session: Session):
    currency_chf = Currency(code="CHF", name="Swiss Franc", country="Switzerland")
    currency_htg = Currency(code="HTG", name="Haitian Gourde", country="Haiti")
    currency_inr = Currency(code="INR", name="Indian Rupee", country="India", show_in_ui=True)
    currency_egp = Currency(code="EGP", name="Egyptian Pound", country="Egypt", show_in_ui=True)

    session.add(currency_chf)
    session.add(currency_inr)
    session.add(currency_egp)
    session.add(currency_htg)

    session.commit()

    resp = client.get("/currency/all")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 4

    assert data[0]["code"] == "CHF"
    assert data[1]["code"] == "EGP"
    assert data[2]["code"] == "HTG"
    assert data[3]["code"] == "INR"

    resp = client.get("/currency/all", params={"ui": True})
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 2

    assert data[0]["code"] == "EGP"
    assert data[0]["name"] == currency_egp.name

    assert data[1]["code"] == "INR"
    assert data[1]["name"] == currency_inr.name

    # Change one show in UI to true, then test whether this updated variable is sent back

    currency_htg.show_in_ui = True
    session.add(currency_htg)
    session.commit()

    resp = client.get("/currency/all", params={"ui": True})
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 3

    assert data[0]["code"] == "EGP"
    assert data[0]["name"] == currency_egp.name

    assert data[1]["code"] == "HTG"
    assert data[1]["name"] == currency_htg.name

    assert data[2]["code"] == "INR"
    assert data[2]["name"] == currency_inr.name

    # make all show in ui to be false, now list with no data should be sent back

    currency_inr.show_in_ui = False
    currency_htg.show_in_ui = False
    currency_egp.show_in_ui = False

    session.add(currency_htg)
    session.add(currency_htg)
    session.add(currency_inr)

    session.commit()

    resp = client.get("/currency/all", params={"ui": True})
    data = resp.json()
    assert len(data) == 0
