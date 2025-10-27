from fastapi import APIRouter
from sqlmodel import select

from repository.models import Currency, SessionDep

currency_router = APIRouter()


@currency_router.get(
    "/populate",
    description="populates currencies to the database",
)
def populate_currencies(session: SessionDep):
    session.add(Currency(code="INR", country="India", currency_name="Indian Rupee"))
    session.add(Currency(code="GBP", country="United Kingdom", currency_name="Pound Sterling"))
    session.add(Currency(code="USD", country="United States", currency_name="US Dollar"))
    session.add(Currency(code="EUR", country="European Union", currency_name="Euro"))
    session.add(Currency(code="JPY", country="Japan", currency_name="Japanese Yen"))
    session.add(Currency(code="CHF", country="Switzerland", currency_name="Swiss Franc"))
    session.add(Currency(code="CAD", country="Canada", currency_name="Canadian Dollar"))
    session.add(Currency(code="CNY", country="China", currency_name="Chinese Yuan"))
    session.add(Currency(code="HKD", country="Hong Kong", currency_name="Hong Kong Dollar"))
    session.add(Currency(code="KRW", country="South Korea", currency_name="South Korean Won"))
    session.add(Currency(code="SGD", country="Singapore", currency_name="Singapore Dollar"))
    session.add(Currency(code="SAR", country="Saudi Arabia", currency_name="Saudi Riyal"))
    session.add(Currency(code="SEK", country="Sweden", currency_name="Swedish Krona"))
    session.add(Currency(code="NZK", country="New Zealand", currency_name="New Zealand Dollar"))
    session.add(Currency(code="BRL", country="Brazil", currency_name="Brazilian Real"))
    session.commit()


@currency_router.get(
    "/all",
    description="Lists all supported currencies",
    response_model=list[Currency],
)
def supported_currencies(session: SessionDep):
    stmt = select(Currency)
    res = session.exec(stmt)
    return res
