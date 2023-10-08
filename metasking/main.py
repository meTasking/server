import traceback

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

import metasking.logger  # noqa: F401
import metasking.model  # noqa: F401

from metasking.api import api_router as api
from metasking.model import ErrorModel

app = FastAPI(title="meTasking")

app.include_router(api, prefix="/api")


@app.exception_handler(Exception)
async def app_exception_handler(
    request: Request,
    exc: Exception
):
    traceback.print_exception(exc)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorModel(
                message=exc.detail,
            ).dict(),
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorModel(
            message="Internal server error",
        ).dict(),
    )
