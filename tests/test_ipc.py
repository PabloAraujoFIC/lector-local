import socket
import subprocess
import sys
import time

import pytest
from reader_core.ipc import request
from reader_core.protocol.framing import read_frame, write_frame
from test_core import command


@pytest.fixture
def daemon(tmp_path, monkeypatch):
    monkeypatch.setenv("LECTOR_DATA_DIR", str(tmp_path))
    process = subprocess.Popen(
        [sys.executable, "-m", "reader_core", "daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 10
    while not (tmp_path / "endpoint.json").exists():
        if process.poll() is not None or time.monotonic() > deadline:
            process.terminate()
            pytest.fail("Core did not start")
        time.sleep(0.03)
    yield tmp_path, process
    process.terminate()
    process.wait(timeout=5)


def test_clients_share_single_core_and_reject_browser_files(daemon):
    directory, process = daemon
    first = request(command("settings", values={"speed": 1.25}), "desktop")
    second = request(command("state"), "browser")
    assert first["payload"]["settings"] == second["payload"]["settings"]
    result = request(command("load_document", path="/tmp/sensitive.txt"), "browser")
    assert result["error"]["code"] == "permission_denied"
    import json

    assert json.loads((directory / "endpoint.json").read_text())["pid"] == process.pid


def test_unauthenticated_clients_are_rejected(daemon):
    import json

    endpoint = json.loads((daemon[0] / "endpoint.json").read_text())
    with socket.create_connection(("127.0.0.1", endpoint["port"])) as connection:
        with connection.makefile("rwb") as stream:
            write_frame(
                stream, {"token": "wrong", "origin": "desktop", "request": command("state")}
            )
            with pytest.raises(EOFError):
                read_frame(stream)
    if sys.platform != "win32":
        assert (daemon[0] / "endpoint.json").stat().st_mode & 0o077 == 0


def test_second_daemon_keeps_original_service(daemon):
    import json

    directory, original = daemon
    second = subprocess.run(
        [sys.executable, "-m", "reader_core", "daemon"],
        capture_output=True,
        timeout=10,
    )
    assert second.returncode == 0, second.stderr
    assert not second.stderr
    assert json.loads((directory / "endpoint.json").read_text())["pid"] == original.pid
    assert request(command("state"))["success"]


@pytest.mark.parametrize(
    "launch_args",
    [
        ["native-host"],
        ["chrome-extension://" + "a" * 32 + "/"],
        ["/tmp/org.lector.local.json", "lector-local@lector.local"],
    ],
)
def test_native_message_reaches_same_daemon(daemon, launch_args):
    process = subprocess.Popen(
        [sys.executable, "-m", "reader_core"] + launch_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        write_frame(process.stdin, command("settings", values={"speed": 1.5}))
        while True:
            result = read_frame(process.stdout)
            if result["type"] == "response":
                break
        assert result["success"]
        assert request(command("state"))["payload"]["settings"]["speed"] == 1.5
    finally:
        process.terminate()
        process.wait(timeout=5)
