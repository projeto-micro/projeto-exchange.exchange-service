from pydantic import BaseModel, Field


class ExchangeOut(BaseModel):
    sell: float
    buy: float
    date: str
    id_account: str = Field(serialization_alias="id-account")
