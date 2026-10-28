import logfire

from agora_worker.config import Settings


def configure_observability(settings: Settings) -> None:
    token = settings.logfire_token.get_secret_value()
    logfire.configure(
        service_name="agora-worker",
        token=token or None,
        send_to_logfire=bool(token),
        console=False,
        inspect_arguments=False,
        data_dir="/tmp/agora-logfire-worker",
    )
