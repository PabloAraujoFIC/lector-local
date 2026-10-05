"""Authenticode signing with an already provisioned certificate (no embedded secrets)."""

import os
import subprocess
import sys


def main():
    thumbprint = os.environ.get("LECTOR_WINDOWS_CERTIFICATE_THUMBPRINT", "")
    timestamp = os.environ.get("LECTOR_WINDOWS_TIMESTAMP_URL", "")
    if sys.platform != "win32" or not thumbprint or not timestamp or len(sys.argv) != 2:
        raise SystemExit("Requiere Windows, certificado aprovisionado, URL de timestamp y archivo.")
    tool = os.environ.get("LECTOR_SIGNTOOL", "signtool.exe")
    subprocess.run(
        [
            tool,
            "sign",
            "/sha1",
            thumbprint,
            "/fd",
            "SHA256",
            "/tr",
            timestamp,
            "/td",
            "SHA256",
            sys.argv[1],
        ],
        check=True,
    )
    subprocess.run([tool, "verify", "/pa", "/all", sys.argv[1]], check=True)


if __name__ == "__main__":
    main()
