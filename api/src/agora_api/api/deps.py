from collections.abc import Iterator
from typing import Annotated

import psycopg
from dbos import DBOSClient, DBOSPortableJSONSerializer
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from agora_api.config import settings
from agora_api.services.runs import APPLICATION_NAME


def get_worker_client() -> Iterator[DBOSClient]:
    client = DBOSClient(
        system_database_url=settings.dbos_database_url,
        application_name=APPLICATION_NAME,
        serializer=DBOSPortableJSONSerializer(),
        lazy=True,
        retry_connection_errors=False,
    )
    try:
        yield client
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Run storage unavailable") from None
    finally:
        client.destroy()


WorkerClient = Annotated[DBOSClient, Depends(get_worker_client)]


def get_database_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    try:
        with psycopg.connect(
            str(settings.database_url), connect_timeout=2, options="-c statement_timeout=2000"
        ) as connection:
            yield connection
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database unavailable") from None


DatabaseConnection = Annotated[
    psycopg.Connection[tuple[object, ...]], Depends(get_database_connection)
]
