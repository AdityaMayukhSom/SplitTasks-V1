import http.client
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlmodel import col, delete, func, select

from repository.models import Currency, SessionDep

currency_router = APIRouter()


class CurrencyPopulate(BaseModel):
    model_config = {"extra": "forbid"}
    forced: bool = Field(alias="forcePopulate", default=False)


@currency_router.get(
    "/populate",
    description="populates currencies to the database",
    tags=["currency"],
)
async def populate_currencies(populate_query: Annotated[CurrencyPopulate, Query()], session: SessionDep):
    currency_cnt_stmt = select(func.count(col(Currency.code)))
    num_currency = session.exec(currency_cnt_stmt).one()

    if num_currency > 0 and not populate_query.forced:
        return PlainTextResponse(
            f"already {num_currency} currencies exist and forced populate is not enabled", status_code=http.client.OK
        )

    if num_currency > 0:
        session.exec(delete(Currency))
        session.commit()

    currencies = (
        Currency(code="INR", country="India", currency_name="Indian Rupee"),
        Currency(code="GBP", country="United Kingdom", currency_name="Pound Sterling"),
        Currency(code="USD", country="United States", currency_name="US Dollar"),
        Currency(code="EUR", country="European Union", currency_name="Euro"),
        Currency(code="JPY", country="Japan", currency_name="Japanese Yen"),
        Currency(code="CHF", country="Switzerland", currency_name="Swiss Franc"),
        Currency(code="CAD", country="Canada", currency_name="Canadian Dollar"),
        Currency(code="CNY", country="China", currency_name="Chinese Yuan"),
        Currency(code="HKD", country="Hong Kong", currency_name="Hong Kong Dollar"),
        Currency(code="KRW", country="South Korea", currency_name="South Korean Won"),
        Currency(code="SGD", country="Singapore", currency_name="Singapore Dollar"),
        Currency(code="SAR", country="Saudi Arabia", currency_name="Saudi Riyal"),
        Currency(code="SEK", country="Sweden", currency_name="Swedish Krona"),
        Currency(code="NZK", country="New Zealand", currency_name="New Zealand Dollar"),
        Currency(code="BRL", country="Brazil", currency_name="Brazilian Real"),
    )

    session.add_all(currencies)
    session.commit()

    return PlainTextResponse(
        f"created {len(currencies)} currencies with forced flag {populate_query.forced}",
        status_code=http.client.CREATED,
    )


@currency_router.get(
    "/all",
    description="Lists all supported currencies",
    response_model=list[Currency],
    tags=["currency"],
)
def supported_currencies(session: SessionDep):
    stmt = select(Currency)
    res = session.exec(stmt)
    return res
