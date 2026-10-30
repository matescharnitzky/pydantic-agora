from collections.abc import Iterator
from typing import Annotated

import psycopg
from dbos import DBOSClient, DBOSPortableJSONSerializer
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from agora_api.config import settings
from agora_api.services.workflows import APPLICATION_NAME


def get_workflow_client() -> Iterator[DBOSClient]:
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
        raise HTTPException(status_code=503, detail="Workflow storage unavailable") from None
    finally:
        client.destroy()


WorkflowClient = Annotated[DBOSClient, Depends(get_workflow_client)]


def get_registry_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    try:
        with psycopg.connect(
            str(settings.database_url), connect_timeout=2, options="-c statement_timeout=2000"
        ) as connection:
            yield connection
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Capability registry unavailable") from None


RegistryConnection = Annotated[
    psycopg.Connection[tuple[object, ...]], Depends(get_registry_connection)
]
