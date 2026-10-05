"""One catalog for extension identities shared by builders and native registration."""

import json
from pathlib import Path

CONFIG = json.loads(Path(__file__).with_name("distribution.json").read_text())
HOST_NAME = CONFIG["nativeHost"]
FIREFOX_ID = CONFIG["firefoxId"]


def chromium_id(channel: str) -> str | None:
    return CONFIG[channel]["chromiumId"]
