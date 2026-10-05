import json
from pathlib import Path

from reader_core.protocol.messages import COMMANDS, VERSION


def test_canonical_schema_matches_core():
    root = Path(__file__).parents[1]
    schema = json.loads((root / "packages/protocol/schema.json").read_text())
    assert set(schema["properties"]["command"]["enum"]) == set(COMMANDS)
    assert schema["properties"]["protocol_version"]["const"] == VERSION
    source = (root / "packages/types/src/index.ts").read_text()
    for name in COMMANDS:
        assert f"'{name}'" in source or f'"{name}"' in source
