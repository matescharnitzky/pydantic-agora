"""Generate pgAdmin connection JSON before running its official entrypoint."""

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    server = {
        "Name": "Agora local",
        "Group": "Agora",
        "Host": "postgres",
        "Port": 5432,
        "MaintenanceDB": os.environ["POSTGRES_DB"],
        "Username": os.environ["POSTGRES_USER"],
        "SSLMode": "prefer",
    }
    Path(os.environ["PGADMIN_SERVER_JSON_FILE"]).write_text(
        json.dumps({"Servers": {"1": server}}), encoding="utf-8"
    )
    os.execv("/entrypoint.sh", ["/entrypoint.sh", *sys.argv[1:]])
