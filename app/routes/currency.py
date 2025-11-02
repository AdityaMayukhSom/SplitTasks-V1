import csv
from typing import Sequence, Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query
from fastapi.responses import PlainTextResponse
from sqlmodel import col, delete, func, select
from starlette.responses import JSONResponse

from app.repository.models import Currency, SessionDep
from app.routes.base_payload import BasePayload

currency_router = APIRouter()


@currency_router.get(
    "/populate",
    description="populates currencies to the database",
    tags=["currency"],
    response_class=PlainTextResponse,
)
async def populate_currencies(session: SessionDep, force_populate: bool = False):
    currency_cnt_stmt = select(func.count(col(Currency.code)))
    num_currency = session.exec(currency_cnt_stmt).first()

    if num_currency > 0 and not force_populate:
        return PlainTextResponse(
            f"already {num_currency} currencies exist and forced populate is not enabled",
            status_code=status.HTTP_200_OK,
        )

    if num_currency > 0:
        session.exec(delete(Currency))
        session.commit()

    try:
        with open("./public/currency.csv", "r", encoding="utf-8") as f:
            csv_curr = csv.DictReader(f)
            currencies = [
                Currency(
                    code=row.get("Code"),
                    name=row.get("Name"),
                    country=row.get("Country"),
                    show_in_ui=row.get("ShowInUI").lower() == "true",
                )
                for row in csv_curr
            ]
    except IOError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="could not read currency data, could not populate currency database",
        )

    session.add_all(currencies)
    session.commit()

    return PlainTextResponse(
        f"created {len(currencies)} currencies with forced flag {force_populate}",
        status_code=status.HTTP_201_CREATED,
    )


class CurrencyPayload(BasePayload):
    code: str
    name: str


@currency_router.get(
    "/all",
    description="Lists currencies, sorted by their country code.",
    response_class=JSONResponse,
    response_model=list[CurrencyPayload],
    tags=["currency"],
)
async def get_currencies(
    session: SessionDep,
    ui: Annotated[
        bool,
        Query(description="if true, only currencies which are to be shown in UI are returned."),
    ] = False,
):
    stmt = select(Currency)
    if ui:
        stmt = stmt.where(Currency.show_in_ui)
    stmt = stmt.order_by(Currency.code)
    res: Sequence[Currency] = session.exec(stmt).all()
    currencies = [CurrencyPayload(code=c_db.code, name=c_db.name) for c_db in res]
    return JSONResponse(content=jsonable_encoder(currencies), status_code=status.HTTP_200_OK)
