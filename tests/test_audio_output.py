from types import SimpleNamespace

from reader_core.audio.output import system_output_device


def backend(devices):
    return SimpleNamespace(
        query_devices=lambda: devices,
        query_hostapis=lambda: [{"name": "ALSA"}, {"name": "JACK"}],
    )


def test_linux_routes_through_session_server_instead_of_hardware(monkeypatch):
    monkeypatch.setattr("reader_core.audio.output.sys.platform", "linux")
    sd = backend(
        [
            {"name": "hw:0,0", "hostapi": 0, "max_output_channels": 2},
            {"name": "pulse", "hostapi": 0, "max_output_channels": 32},
            {"name": "pipewire", "hostapi": 0, "max_output_channels": 128},
        ]
    )
    assert system_output_device(sd) == 2
    sd.query_devices = lambda: [
        {"name": "pulse", "hostapi": 0, "max_output_channels": 32},
    ]
    assert system_output_device(sd) == 0


def test_capture_only_or_similarly_named_devices_are_not_selected(monkeypatch):
    monkeypatch.setattr("reader_core.audio.output.sys.platform", "linux")
    sd = backend(
        [
            {"name": "pipewire", "hostapi": 0, "max_output_channels": 0},
            {"name": "pulse headphones", "hostapi": 0, "max_output_channels": 2},
            {"name": "pulse", "hostapi": 1, "max_output_channels": 2},
        ]
    )
    assert system_output_device(sd) is None


def test_other_platforms_keep_system_default(monkeypatch):
    monkeypatch.setattr("reader_core.audio.output.sys.platform", "win32")
    assert system_output_device(SimpleNamespace()) is None
