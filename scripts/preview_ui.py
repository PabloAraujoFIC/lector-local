"""Optional visual preview using system PyGObject/WebKitGTK on Linux.

The preview uses a snapshot of the running core, without controlling playback.
"""

import json
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))
from reader_core.ipc import request  # noqa: E402


def main():
    def fetch(command, payload=None):
        return request(
            {
                "protocol_version": 1,
                "id": "preview",
                "type": "command",
                "command": command,
                "payload": payload or {},
            }
        )

    state = fetch("state")
    page = fetch("document_page", {"start": 0, "count": 80})
    script = """window.__TAURI_INTERNALS__={
      metadata:{currentWindow:{label:'main'},currentWebview:{label:'main'}},
      transformCallback:()=>1, unregisterCallback:()=>{},
      invoke:async(command,args)=>{
        if(command==='core_request')return args.message.command==='document_page'?PAGE:STATE;
        return 1;
      }
    };""".replace("PAGE", json.dumps(page)).replace("STATE", json.dumps(state))
    manager = WebKit2.UserContentManager()
    manager.add_script(
        WebKit2.UserScript.new(
            script,
            WebKit2.UserContentInjectedFrames.TOP_FRAME,
            WebKit2.UserScriptInjectionTime.START,
            None,
            None,
        )
    )
    webview = WebKit2.WebView.new_with_user_content_manager(manager)
    window = Gtk.Window(title="Lector Local · vista de validación")
    window.set_default_size(1240, 900)
    window.add(webview)
    window.connect("destroy", Gtk.main_quit)

    def captured(view, result):
        surface = view.get_snapshot_finish(result)
        destination = Path("artifacts/desktop-preview.png")
        surface.write_to_png(str(destination))
        print(destination)
        window.destroy()

    def capture():
        webview.get_snapshot(
            WebKit2.SnapshotRegion.FULL_DOCUMENT, WebKit2.SnapshotOptions.NONE, None, captured
        )
        return False

    def loaded(view, event):
        if event == WebKit2.LoadEvent.FINISHED:
            GLib.timeout_add(1600, capture)

    webview.connect("load-changed", loaded)
    window.show_all()
    webview.load_uri("http://127.0.0.1:1420")
    GLib.timeout_add_seconds(15, lambda: (window.destroy(), False)[1])
    Gtk.main()


if __name__ == "__main__":
    main()
