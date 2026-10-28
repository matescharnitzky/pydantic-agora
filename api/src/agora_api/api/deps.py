from collections.abc import Iterator
from typing import Annotated

from dbos import DBOSClient, DBOSPortableJSONSerializer
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from agora_api.config import settings
from agora_api.services.workflows import APPLICATION_NAME


def get_workflow_client() -> Iterator[DBOSClient]:
    client = DBOSClient(
        system_database_url=settings.dbos_database_url,
        application_name=APPLICATION_NAME,
        dbos_system_schema=settings.dbos_system_schema,
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
