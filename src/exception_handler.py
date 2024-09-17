from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import IntegrityError, StatementError
from starlette.responses import JSONResponse
from sqlalchemy.orm.exc import NoResultFound

from src.service.Logger import logger


def setup_exception_handlers(app):

    @app.exception_handler(StatementError)
    async def statement_exception_handler(request, exc):
        logger.error(f"Statement error: {exc.args[0]}")
        return JSONResponse(
            status_code=400,
            content={"detail": f"{exc.args[0]}"},
        )

    @app.exception_handler(ValueError)
    async def value_exception_handler(request, exc):
        logger.error(f"Value error: {exc.args[0]}")
        return JSONResponse(
            status_code=400,
            content={"detail": f"{exc.args[0]}"},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request, exc):
        logger.error(f"Integrity error: {exc.args[0]}")
        return JSONResponse(
            status_code=400,
            content={"detail": f"Integrity error: {exc.args[0]}"},
        )

    @app.exception_handler(NoResultFound)
    async def no_result_handler(request, exc):
        logger.error("No result found error")
        return JSONResponse(
            status_code=404,
            content={"detail": "Ningún objeto con ese ID."},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=400,
            content={"detail": exc.errors(), "body": exc.body},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        logger.error(f"HTTP error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):
        logger.error(f"Generic error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )