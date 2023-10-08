from sqlmodel import SQLModel


class ErrorModel(SQLModel):
    message: str
