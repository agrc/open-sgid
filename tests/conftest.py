import os
from pathlib import Path

os.environ.setdefault("CLOUDB_CONFIG", str(Path(__file__).parents[1] / "src" / "cloudb" / "secrets" / "db" / "connection.template"))
